import json
import logging
import os
from datetime import datetime
from video_processor import VideoProcessor
from tik_tok_api import TikTokAPI
from constants import DATE_FORMAT, EXPORT_FOLDER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LambdaHandler:
    def __init__(self):
        self.video_processor = VideoProcessor(DATE_FORMAT)
        self.tiktok_api = TikTokAPI()

    def export_video_details_to_file(self, username, id, video):
        """
        Create a JSON file for each video.
        """
        filename = os.path.join(EXPORT_FOLDER, f"{username}_{id}.json")
        with open(filename, "w") as file:
            json.dump(video, file, ensure_ascii=False, indent=4)
        logger.info(f"Created {username}_{id}.json")

    def process_request(self, event, context):
        logger.info("Entered lambda handler")
        # TODO: process the timestamps if we're splitting up the days by lambda invocation
        os.makedirs(EXPORT_FOLDER, exist_ok=True)

        hashtag = "suicideawareness"  # TODO: iterate through all hashtags we want to look at
        start_date = "20230101"  # TODO: batch dates efficiently
        end_date = "20230102"
        today = datetime.now().strftime(DATE_FORMAT)

        # Retrieve videos
        max_video_count = 100
        videos = self.tiktok_api.get_videos(hashtag, start_date, end_date, max_video_count)

        # Process each video
        for video in videos:
            video_id, username = self.video_processor.get_video_details(video)
            user_details = self.tiktok_api.get_user_details(username)
            video_comments = self.tiktok_api.get_video_comments(video_id)
            video_details = self.video_processor.create_video_json(
                video, video_comments, user_details, hashtag, today
            )
            self.export_video_details_to_file(username, video_id, video_details)

        logger.info(f"Processed {len(videos)} video{'s' if len(videos) != 1 else ''}.")
        return True


def lambda_handler(event, context):
    handler = LambdaHandler()
    return handler.process_request(event, context)


# for running locally
if __name__ == "__main__":
    handler = LambdaHandler()
    handler.process_request(None, None)
