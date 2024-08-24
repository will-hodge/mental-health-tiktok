# mental-health-tiktok

### Functionality so far
- Retrieves list of videos for all six hashtags
- For each video: retrieves all comments and details about the user who posted it
- Spits out the files as a JSON and uploads to S3
- Creates a summary file documenting how many videos were retrieved, duration, and total API calls

### To do
- Download the videos
- Batch the calls efficiently to get videos for all hashtags and for all of 2023 while working around [the research quota of 1000 API calls per day](https://developers.tiktok.com/doc/research-api-faq/)
  - Use SQS -> Lambda?
- WhisperAI?

### Resources
- Requirements: https://docs.google.com/document/d/1pOrS59hZuZtZX5fDWDVVr6zphGXIvgBguwJUzzvIZQY/
- TikTok Research API: https://developers.tiktok.com/doc/research-api-get-started/
