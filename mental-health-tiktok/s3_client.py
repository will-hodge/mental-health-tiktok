import boto3
import logging

logger = logging.getLogger(__name__)


class S3Client:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client("s3")
        self.bucket_name = bucket_name

    def upload_json(self, key, content):
        """
        Uploads a JSON string to an S3 bucket.
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType="application/json",
            )
            logger.info(f"Uploaded {key} to S3 bucket {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to upload {key} to S3: {e}")
