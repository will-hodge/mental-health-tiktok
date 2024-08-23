import json
import logging
import os
import time
from datetime import datetime
from video_processor import VideoProcessor
from tik_tok_api import TikTokAPI
from constants import DATE_FORMAT, EXPORT_SUMMARY_FILE, EXPORT_FOLDER, HASHTAGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LambdaHandler:
    def __init__(self):
        self.video_processor = VideoProcessor(DATE_FORMAT)
        self.tiktok_api = TikTokAPI()
        self.hashtags = HASHTAGS
        self.summary = {
            "videos": {hashtag: 0 for hashtag in HASHTAGS},
            "total_api_calls": 0,
        }

    def update_summary(self, hashtag, count):
        self.summary["videos"][hashtag] = count

    def export_summary(self, duration):
        self.summary["total_api_calls"] = self.tiktok_api.api_call_count
        self.summary["duration"] = f"{duration:.2f} seconds"
        # sum all video counts
        videos = self.summary["videos"]
        videos["total"] = sum(videos.values())
        filename = os.path.join(EXPORT_FOLDER, EXPORT_SUMMARY_FILE)
        with open(filename, "w") as file:
            json.dump(self.summary, file, ensure_ascii=False, indent=4)

    def export_video_details_to_file(self, filepath, id, video):
        """
        Create a JSON file for each video.
        """
        video_folder = os.path.join(filepath, str(id))
        os.makedirs(video_folder, exist_ok=True)
        filename = os.path.join(video_folder, f"{id}.json")
        with open(filename, "w") as file:
            json.dump(video, file, ensure_ascii=False, indent=4)
        logger.info(f"Created {id}.json.")

    def process_request(self, event, context):
        logger.info("Entered lambda handler")
        export_start_time = time.time()
        # TODO: process the timestamps if we're splitting up the days by lambda invocation

        start_date = (
            "20230101"  # TODO: batch dates efficiently given we want an entire year
        )
        end_date = "20230102"
        today = datetime.now().strftime(DATE_FORMAT)

        for hashtag in self.hashtags:
            filepath = os.path.join(EXPORT_FOLDER, hashtag)
            os.makedirs(filepath, exist_ok=True)
            # Retrieve videos
            max_video_count = 100
            videos = self.tiktok_api.get_videos(
                hashtag, start_date, end_date, max_video_count
            )

            # Process each video
            for video in videos:
                video_id, username = self.video_processor.get_video_details(video)
                user_details = self.tiktok_api.get_user_details(username)
                video_comments = self.tiktok_api.get_video_comments(video_id)
                video_details = self.video_processor.create_video_json(
                    video, video_comments, user_details, hashtag, today
                )
                self.export_video_details_to_file(filepath, video_id, video_details)

            num_videos = len(videos)
            logger.info(
                f"Processed {num_videos} video{'s' if num_videos != 1 else ''} for #{hashtag}."
            )
            self.update_summary(hashtag, num_videos)
        export_end_time = time.time()
        export_duration = export_end_time - export_start_time
        self.export_summary(export_duration)
        return True


def lambda_handler(event, context):
    handler = LambdaHandler()
    return handler.process_request(event, context)


# for running locally
if __name__ == "__main__":
    handler = LambdaHandler()
    handler.process_request(None, None)
