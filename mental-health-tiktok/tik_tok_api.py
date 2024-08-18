import requests
import os
import time
import logging
from constants import (
    API_BASE_URL,
    CACHE_CONTROL,
    CLIENT_KEY,
    CLIENT_SECRET,
    ERROR_DESCRIPTION_KEY,
    ERROR_KEY,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_OK,
    HTTP_STATUS_TOO_MANY_REQUESTS,
    HTTP_STATUS_SERVICE_UNAVAILABLE,
    TOKEN_ENDPOINT,
    USER_ENDPOINT,
    URL_ENCODED_CONTENT_TYPE,
    VIDEO_COMMENTS_ENDPOINT,
    VIDEO_ENDPOINT,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokAPI:
    def __init__(self):
        self.client_key, self.client_secret = self.get_env_variables()
        self.access_token = self.get_access_token()

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
            response = requests.post(url, headers=headers, params=params, data=data, json=json)
            if response.status_code == HTTP_STATUS_OK:
                # TikTok API sometimes returns a 200 but with errors
                response_json = response.json()
                self.handle_api_error(response_json)
                return response_json
            elif response.status_code in [
                HTTP_STATUS_TOO_MANY_REQUESTS,
                HTTP_STATUS_INTERNAL_SERVER_ERROR,
                HTTP_STATUS_SERVICE_UNAVAILABLE,
            ]:
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                response.raise_for_status()  # Raise other HTTP errors
        raise Exception("Max retries exceeded")

    # Generalized error handling for API requests
    def handle_api_error(self, response_json):
        if ERROR_KEY in response_json and response_json[ERROR_KEY].get("code") != "ok":
            error = response_json.get(ERROR_KEY)
            error_description = response_json.get(ERROR_DESCRIPTION_KEY)
            message = f"API error: {error}. Description: {error_description}"
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
            return None

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

        body = {
            "query": {
                "and": [
                    {
                        "operation": "IN",
                        "field_name": "region_code",
                        "field_values": ["US"],
                    },
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
        }

        try:
            logger.info("Calling TikTok API to retrieve videos.")
            response = self._request_with_retries(url, headers, query_params, json=body)
            return response.get("data", {}).get("videos", [])
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
        return []

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
            logger.error(f"Failed to get user details for user {username} due to error: {e}")
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

        try:
            comments = []
            cursor = None
            has_more = True
            while has_more:
                if cursor:
                    body = {"video_id": video_id, "max_count": 100, "cursor": cursor}
                else:
                    body = {"video_id": video_id, "max_count": 100}

                logger.info("Calling TikTok API to retrieve video comments.")
                response = self._request_with_retries(url, headers, query_params, json=body)
                new_comments = response.get("data", {}).get("comments", [])
                cursor = response.get("data", {}).get("cursor", None)
                has_more = response.get("data", {}).get("has_more", False)

                comments.extend(new_comments)
            return response.get("data", {}).get("comments", [])
        except Exception as e:
            logger.error(f"Failed to get video comments for video with ID {video_id} due to error: {e}")
            return []
