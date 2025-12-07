from youtube_transcript_api import YouTubeTranscriptApi
print(dir(YouTubeTranscriptApi))
try:
    print(YouTubeTranscriptApi.get_transcript("jNQXAC9IVRw"))
except Exception as e:
    print(e)
