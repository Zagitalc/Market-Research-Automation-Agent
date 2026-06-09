from django.conf import settings
from rest_framework.throttling import ScopedRateThrottle


class ConfiguredScopedRateThrottle(ScopedRateThrottle):
    def get_rate(self):
        return settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][self.scope]
