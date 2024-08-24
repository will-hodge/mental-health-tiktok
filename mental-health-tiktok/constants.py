# Environment variables
AWS_REGION = "AWS_REGION"
CLIENT_KEY = "CLIENT_KEY"
CLIENT_SECRET = "CLIENT_SECRET"

# API URLs
API_BASE_URL = "https://open.tiktokapis.com/v2/"
TOKEN_ENDPOINT = "oauth/token/"
USER_ENDPOINT = "research/user/info/"
VIDEO_ENDPOINT = "research/video/query/"
VIDEO_COMMENTS_ENDPOINT = "research/video/comment/list/"

# Headers
URL_ENCODED_CONTENT_TYPE = "application/x-www-form-urlencoded"
CACHE_CONTROL = "no-cache"

# HTTP status codes
HTTP_STATUS_OK = 200
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

# API handling
RESPONSE_CODE_KEY = "code"
ERROR_KEY = "error"
ERROR_MESSAGE_KEY = "message"

# Other
VIDEO_URL_FORMAT = "https://www.tiktok.com/@{username}/video/{video_id}"
DATE_FORMAT = "%Y-%m-%d"
EXPORT_FOLDER = "video_files"
EXPORT_SUMMARY_FILE = "summary.json"
S3_BUCKET_NAME = "tik-tok-mental-health-analysis"

HASHTAGS = [
    "suicideprevention",
    "suicideawareness",
    "suiawareness",
    "shawareness",
    "shrecovering",
    "shtok",
]
