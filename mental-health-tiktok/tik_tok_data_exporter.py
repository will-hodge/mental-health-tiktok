import json
import logging
import os
import time
from datetime import datetime
from s3_client import S3Client
from tik_tok_api import TikTokAPI
from video_processor import VideoProcessor
from constants import (
    DATE_FORMAT,
    EXPORT_SUMMARY_FILE,
    EXPORT_FOLDER,
    HASHTAGS,
    S3_BUCKET_NAME,
)

logger = logging.getLogger(__name__)


class TikTokDataExporter:
    def __init__(self):
        self.video_processor = VideoProcessor(DATE_FORMAT)
        self.tiktok_api = TikTokAPI()
        self.s3_client = S3Client(S3_BUCKET_NAME)
        self.hashtags = HASHTAGS
        self.summary = {
            "videos": {hashtag: 0 for hashtag in HASHTAGS},
            "total_api_calls": 0,
        }
        self.today = datetime.now().strftime(DATE_FORMAT)
        self.is_lambda = os.environ.get("AWS_EXECUTION_ENV") is not None

    def update_summary(self, hashtag, count):
        self.summary["videos"][hashtag] = count

    def export_summary(self, start_date, end_date, duration):
        self.summary["start_date"] = start_date
        self.summary["end_date"] = end_date
        self.summary["total_api_calls"] = self.tiktok_api.api_call_count
        self.summary["duration"] = f"{duration:.2f} seconds"
        # sum all video counts
        videos = self.summary["videos"]
        videos["total"] = sum(videos.values())
        filename = f"{EXPORT_FOLDER}/{EXPORT_SUMMARY_FILE}"
        summary_json = json.dumps(self.summary, ensure_ascii=False, indent=4)
        logger.info(f"Export summary: {summary_json}")
        # only store file when running locally
        if not self.is_lambda:
            with open(filename, "w") as file:
                json.dump(self.summary, file, ensure_ascii=False, indent=4)
        self.s3_client.upload_json(f"{self.today}/{filename}", summary_json)
        logger.info(f"Created {EXPORT_SUMMARY_FILE}.")

    def export_video_details(self, hashtag, id, video):
        """
        Create a JSON file for each video.
        """
        video_folder = f"{EXPORT_FOLDER}/{hashtag}/{id}"
        os.makedirs(video_folder, exist_ok=True)
        filename = f"{video_folder}/{id}.json"
        video_json = json.dumps(video, ensure_ascii=False, indent=4)

        # only store file when running locally
        if not self.is_lambda:
            with open(filename, "w") as file:
                json.dump(video, file, ensure_ascii=False, indent=4)
        self.s3_client.upload_json(f"{self.today}/{filename}", video_json)
        logger.info(f"Created {id}.json.")

    def process_request(self, start_date, end_date, video_count=25):
        logger.info(
            f"Exporting {video_count} TikTok videos per hashtag with start date {start_date} and end date {end_date}"
        )
        export_start_time = time.time()

        for hashtag in self.hashtags:
            # Fetch videos for the current hashtag
            videos = self.tiktok_api.get_videos(
                hashtag, start_date, end_date, video_count
            )

            # Process each video
            for video in videos:
                video_id, username, video_comment_count = (
                    self.video_processor.get_video_details(video)
                )
                user_details = self.tiktok_api.get_user_details(username)
                video_comments = (
                    self.tiktok_api.get_video_comments(video_id)
                    if video_comment_count > 0
                    else []
                )
                video_details = self.video_processor.create_video_json(
                    video, video_comments, user_details, hashtag, self.today
                )
                self.export_video_details(hashtag, video_id, video_details)

            num_videos = len(videos)
            logger.info(
                f"Processed {num_videos} video{'s' if num_videos != 1 else ''} for #{hashtag}."
            )
            self.update_summary(hashtag, num_videos)

        export_end_time = time.time()
        export_duration = export_end_time - export_start_time
        self.export_summary(start_date, end_date, export_duration)
        return True
