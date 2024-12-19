from Blog.models import UserActivity
from django.conf import settings
from django.contrib import messages
from django.db.models import F
from django.db import transaction

def check_daily_limit(useractivity, limit, warning_limit, request, limit_type="read"):
    """
    Check if a user has reached their daily limit for reads or posts.
    """
    with transaction.atomic():
        if limit_type == "read":
            if useractivity.view_count_day >= limit:
                messages.error(request, "You have reached your daily read limit.")
                return False
            rows_updated = UserActivity.objects.filter(id=useractivity.id, view_count_day__lt=limit).update(
                view_count_day=F('view_count_day') + settings.ONE
            )
            if rows_updated:  
                useractivity.refresh_from_db()
                if useractivity.view_count_day == warning_limit:
                    messages.warning(request, "You can read 1 more post today.")
                
        elif limit_type == "post":
            if useractivity.count_post_day >= limit:
                messages.error(request, "You have reached your daily post limit.")
                return False

            rows_updated = UserActivity.objects.filter(id=useractivity.id, count_post_day__lt=limit).update(
                count_post_day=F('count_post_day') + settings.ONE
            )
            if rows_updated:  
                useractivity.refresh_from_db()
                if useractivity.count_post_day == warning_limit:
                    messages.warning(request, "You can add 1 more post today.")
    
    return True

