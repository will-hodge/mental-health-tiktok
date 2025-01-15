import argparse
import logging
from datetime import datetime
from dotenv import load_dotenv
from tik_tok_data_exporter import TikTokDataExporter

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

logging.basicConfig(
    filename=f"export_{timestamp}.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_exporter():
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser(description="TikTok Data Exporter")
    parser.add_argument(
        "--start_date", required=True, help="Start date in YYYYMMDD format"
    )
    parser.add_argument("--end_date", required=True, help="End date in YYYYMMDD format")
    parser.add_argument(
        "--video_count", type=int, required=False, help="Number of videos per hashtag"
    )
    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date
    video_count = args.video_count
    logger.info(
        f"Received arguments: start_date={start_date}, end_date={end_date}, video_count={video_count}"
    )

    exporter = TikTokDataExporter()
    exporter.process_request(start_date, end_date, video_count)


if __name__ == "__main__":
    load_dotenv()
    run_exporter()
