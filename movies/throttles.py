from rest_framework.throttling import UserRateThrottle

class VideoStreamRateThrottle(UserRateThrottle):
    scope = 'video_stream'