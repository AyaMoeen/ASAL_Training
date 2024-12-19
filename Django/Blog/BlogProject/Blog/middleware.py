from django.utils.deprecation import MiddlewareMixin

class DisableCSRFForAPI(MiddlewareMixin):
    def process_request(self, request):
        if request.path.startswith('/Blog/posts/'): 
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None

class ResetLimitDay(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            useractivity = request.user.useractivity
            useractivity.reset_daily_limits()