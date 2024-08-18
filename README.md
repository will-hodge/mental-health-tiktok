# mental-health-tiktok

### Functionality so far
- Retrieves list of videos for a hashtag
- For each video: retrieves the comments and details about the user who posted it
- Spits out the files as a JSON

### To do
- Download the videos
- Batch the calls efficiently to get videos for all hashtags and for all of 2023 while working around [the research quota](https://developers.tiktok.com/doc/research-api-faq/)
- WhisperAI?
- AWS integration so all files and videos will be in S3

### Resources
- Requirements: https://docs.google.com/document/d/1pOrS59hZuZtZX5fDWDVVr6zphGXIvgBguwJUzzvIZQY/
- TikTok Research API: https://developers.tiktok.com/doc/research-api-get-started/
