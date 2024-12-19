from django import template
from ..models import Subscription  

register = template.Library()

@register.filter
def is_subscribed_to(user, author):
    """Checks if a user is subscribed to a specific author."""
    if user.is_authenticated:
        return Subscription.objects.filter(subscriber=user, subscribed_to=author).exists()
    return False
