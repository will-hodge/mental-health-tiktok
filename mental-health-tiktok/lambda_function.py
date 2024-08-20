import json
import logging
import os
from datetime import datetime
from video_processor import VideoProcessor
from tik_tok_api import TikTokAPI
from constants import DATE_FORMAT, EXPORT_FOLDER, HASHTAGS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LambdaHandler:
    def __init__(self):
        self.video_processor = VideoProcessor(DATE_FORMAT)
        self.tiktok_api = TikTokAPI()
        self.hashtags = HASHTAGS

    def export_video_details_to_file(self, filepath, username, id, video):
        """
        Create a JSON file for each video.
        """
        video_folder = os.path.join(filepath, f"{username}_{id}")
        os.makedirs(video_folder, exist_ok=True)
        filename = os.path.join(video_folder, f"{username}_{id}.json")
        with open(filename, "w") as file:
            json.dump(video, file, ensure_ascii=False, indent=4)
        logger.info(f"Created {username}_{id}.json")

    def process_request(self, event, context):
        logger.info("Entered lambda handler")
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
                self.export_video_details_to_file(
                    filepath, username, video_id, video_details
                )

            logger.info(
                f"Processed {len(videos)} video{'s' if len(videos) != 1 else ''} for #{hashtag}."
            )
        return True


def lambda_handler(event, context):
    handler = LambdaHandler()
    return handler.process_request(event, context)


# for running locally
if __name__ == "__main__":
    handler = LambdaHandler()
    handler.process_request(None, None)
