import logging
from datetime import datetime
from constants import VIDEO_URL_FORMAT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, date_format):
        self.date_format = date_format

    def get_video_details(self, video):
        return video.get("id"), video.get("username"), video.get("comment_count")

    def parse_video_details(self, video):
        video_id = video.get("id")
        username = video.get("username")
        video_url = VIDEO_URL_FORMAT.format(username=username, video_id=video_id)
        return {
            "video_id": video_id,
            "video_url": video_url,
            "description": video.get("video_description"),
            "hashtags": video.get("hashtag_names"),
            "date_posted": self.format_date(video.get("create_time")),
            "region_code": video.get("region_code"),
            "like_count": video.get("like_count"),
            "share_count": video.get("share_count"),
            "comment_count": video.get("comment_count"),
            "view_count": video.get("view_count"),
            "favorites_count": video.get("favorites_count"),
            "voice_to_text": video.get("voice_to_text"),
        }

    def parse_user_details(self, user, video):
        return {
            "username": video.get("username"),
            "display_name": user.get("display_name"),
            "bio_description": user.get("bio_description"),
            "is_verified": user.get("is_verified"),
            "follower_count": user.get("follower_count"),
            "video_count": user.get("video_count"),
            "likes_count": user.get("likes_count"),
        }

    def parse_comments(self, comments):
        return [
            {
                "comment_id": comment.get("id"),
                "parent_comment_id": comment.get("parent_comment_id"),
                "text": comment.get("text"),
                "like_count": comment.get("like_count"),
                "reply_count": comment.get("reply_count"),
            }
            for comment in comments
        ]

    def format_date(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime(self.date_format)

    def create_video_json(self, video, comments, user, tag, today):
        """
        Create a JSON object containing details about a video, its comments,
        and the associated user information.
        """
        video_and_user_details = {
            "date_searched": today,
            "tag_searched": tag,
            "video": self.parse_video_details(video),
            "comments": self.parse_comments(comments),
            "user": self.parse_user_details(user, video),
        }

        logger.debug(f"Created video JSON object: {video_and_user_details}")
        return video_and_user_details
