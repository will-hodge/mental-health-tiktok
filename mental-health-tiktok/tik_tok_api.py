import requests
import os
import time
import logging
from constants import (
    API_BASE_URL,
    CACHE_CONTROL,
    CLIENT_KEY,
    CLIENT_SECRET,
    ERROR_KEY,
    ERROR_MESSAGE_KEY,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_OK,
    HTTP_STATUS_TOO_MANY_REQUESTS,
    HTTP_STATUS_SERVICE_UNAVAILABLE,
    RESPONSE_CODE_KEY,
    TOKEN_ENDPOINT,
    USER_ENDPOINT,
    URL_ENCODED_CONTENT_TYPE,
    VIDEO_COMMENTS_ENDPOINT,
    VIDEO_ENDPOINT,
)

logger = logging.getLogger(__name__)


class TikTokAPI:
    def __init__(self):
        self.client_key, self.client_secret = self.get_env_variables()
        self.api_call_count = 0
        self.access_token = self.get_access_token()

    def _increment_api_call_count(self):
        self.api_call_count += 1

    def get_env_variables(self):
        """
        Retrieve environment variables and raise an error if any are missing.
        """
        client_key = os.getenv(CLIENT_KEY)
        client_secret = os.getenv(CLIENT_SECRET)

        if None in (client_key, client_secret):
            raise ValueError(
                "Missing one or more required environment variables: "
                "CLIENT_KEY, CLIENT_SECRET"
            )

        return client_key, client_secret

    def _request_with_retries(
        self, url, headers, params=None, data=None, json=None, max_retries=5
    ):
        """
        Make API calls using exponential backoff when throttled.
        """
        for attempt in range(max_retries):
            self._increment_api_call_count()
            try:
                response = requests.post(
                    url, headers=headers, params=params, data=data, json=json
                )
                response_json = response.json()
                if response.status_code == HTTP_STATUS_OK:
                    # TikTok API sometimes returns a 200 but with errors
                    self.handle_api_error(response_json)
                    return response_json
                elif response.status_code in [
                    HTTP_STATUS_TOO_MANY_REQUESTS,
                    HTTP_STATUS_INTERNAL_SERVER_ERROR,
                    HTTP_STATUS_SERVICE_UNAVAILABLE,
                ]:
                    # Exponential backoff
                    wait_time = 2**attempt
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    self.handle_api_error(response_json)
            except ConnectionError as e:
                wait_time = 2**attempt
                logging.error(
                    f"Connection error: {e}. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
        raise Exception("Max retries exceeded")

    def handle_api_error(self, response_json):
        """
        Handle API errors.
        """
        if (
            ERROR_KEY in response_json
            and response_json[ERROR_KEY].get(RESPONSE_CODE_KEY) != "ok"
        ):
            error = response_json.get(ERROR_KEY).get(RESPONSE_CODE_KEY)
            error_message = response_json.get(ERROR_KEY).get(ERROR_MESSAGE_KEY)
            message = f"TikTok API error: {error}. Message: {error_message}"
            logger.error(message)
            raise Exception(message)

    def get_access_token(self):
        """
        Retrieve access token using client credentials.
        """
        url = API_BASE_URL + TOKEN_ENDPOINT

        headers = {
            "Content-Type": URL_ENCODED_CONTENT_TYPE,
            "Cache-Control": CACHE_CONTROL,
        }

        body = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            logger.info("Calling TikTok API to retrieve access token.")
            response = self._request_with_retries(url, headers, data=body)
            logger.info("Successfully retrieved an access token.")
            return response.get("access_token")
        except Exception as e:
            logger.error(f"Failed to get access token due to error: {e}")
            raise e

    def get_videos(self, hashtag, start_date, end_date, max_count):
        """
        Retrieve videos based on hashtag and date range.
        """
        url = API_BASE_URL + VIDEO_ENDPOINT

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        query_params = {
            "fields": "id,video_description,create_time,region_code,"
            "share_count,view_count,like_count,comment_count,"
            "favorites_count,music_id,hashtag_names,username,"
            "effect_ids,playlist_id,voice_to_text"
        }

        videos = []
        try:
            cursor = 0
            search_id = ""
            has_more = True
            while has_more and len(videos) < max_count:
                body = {
                    "query": {
                        "and": [
                            {
                                "operation": "EQ",
                                "field_name": "hashtag_name",
                                "field_values": [hashtag],
                            },
                        ]
                    },
                    "start_date": start_date,
                    "end_date": end_date,
                    "max_count": max_count,
                    "search_id": search_id,
                    "cursor": cursor,
                    "is_random": True,
                }

                logger.info("Calling TikTok API to retrieve videos.")
                response = self._request_with_retries(
                    url, headers, query_params, json=body
                )
                response_data = response.get("data", {})
                new_videos = response_data.get("videos", [])
                cursor = response_data.get("cursor", None)
                has_more = response_data.get("has_more", False)
                search_id = response_data.get("search_id", search_id)

                logger.info(
                    f"Retrieved {len(new_videos)} video{'s' if len(new_videos) != 1 else ''} for #{hashtag}."
                )
                logger.info(
                    f"has_more: {has_more}, search_id: {search_id}, cursor: {cursor}"
                )
                videos.extend(new_videos)
                # return videos  # TODO: remove once we figure out pagination issue
            return videos
        except Exception as e:
            logger.error(f"Failed to get videos for #{hashtag} due to error: {e}")
        finally:
            return videos

    def get_user_details(self, username):
        """
        Retrieve user details.
        """
        url = API_BASE_URL + USER_ENDPOINT
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        query_params = {
            "fields": "display_name,bio_description,avatar_url,is_verified,"
            "follower_count,following_count,likes_count,video_count"
        }

        body = {"username": username}

        try:
            logger.info("Calling TikTok API to retrieve user details.")
            response = self._request_with_retries(url, headers, query_params, json=body)
            return response.get("data", {})
        except Exception as e:
            logger.error(
                f"Failed to get user details for user {username} due to error: {e}"
            )
            return {}

    def get_video_comments(self, video_id):
        """
        Retrieve all comments on a video.
        """
        url = API_BASE_URL + VIDEO_COMMENTS_ENDPOINT
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        query_params = {
            "fields": "id, video_id, text, like_count, reply_count,"
            "parent_comment_id, create_time",
        }

        comments = []
        try:
            cursor = None
            has_more = True
            while has_more:
                if cursor is not None:
                    cursor = int(cursor)

                body = {
                    "video_id": video_id,
                    "max_count": 100,
                    "cursor": cursor,
                }

                logger.info("Calling TikTok API to retrieve video comments.")
                response = self._request_with_retries(
                    url, headers, query_params, json=body
                )
                response_data = response.get("data", {})
                new_comments = response_data.get("comments", [])
                cursor = response_data.get("cursor", None)
                has_more = response_data.get("has_more", False)

                logger.info(f"Retrieved {len(new_comments)} comments for {video_id}.")
                logger.info(f"has_more: {has_more}, cursor: {cursor}")

                comments.extend(new_comments)
        except Exception as e:
            logger.error(
                f"Failed to get video comments for video with ID {video_id} due to error: {e}"
            )
        finally:
            return comments
