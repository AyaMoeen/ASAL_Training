from better_profanity import profanity # type: ignore
from django.shortcuts import redirect
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.contrib import messages
from django.db.models import F

def register_user(username, password, email):
    """Register a new user on the Gopher Blog API platform."""
    url = f"{settings.GOBLOG_API_BASE_URL}/register"
    
    response = requests.post(url, json={
        'username': username,
        'password': password,
        'email': email,
    }) 
    if response.status_code == 201:
        try:
            return response.json()  
        except ValueError:
            return "Unexpected response format, not JSON."
    else:
        try:
            return response.json().get('error', 'Registration failed')
        except ValueError:
            return "Unexpected response format, not JSON."


def get_api_token(username, password):
    """ Login on the Gopher Blog API platform. """
    url = f"{settings.GOBLOG_API_BASE_URL}/login"
    response = requests.post(url, json={'username': username, 'password': password}) 
    
    if response.status_code == 200:
        token = response.json().get('token')
        return token
    return None

def check_for_bad_words(comment_body, user_email, request=None):
    """
    Check for bad words in a comment. If bad words are present, censor them and count their occurrences.
    """
    censored_body = profanity.censor(comment_body)
    bad_word_count = censored_body.count('*' * settings.CONSORED)
    user = User.objects.get(email=user_email)
    useractivity = user.useractivity
    if bad_word_count > settings.NUMBER_OF_WORD:
        useractivity.warnings = F('warnings') + settings.ONE
        if useractivity.warnings == settings.NUMBER_WARNING:
            useractivity.blocked = now() + timedelta(days=settings.DAY_BLOCKED)
            useractivity.save()
            if request:
                messages.warning(request, f"You have been blocked for using offensive language. Your block ends on {useractivity.blocked}.")
        else:
            useractivity.save()
            if request:
                messages.warning(request, f"You have received a warning! Total warnings: {useractivity.warnings}")
        return False, censored_body  
    return True, censored_body

def check_user_block_status(user, request):
    """
    Check if the user is blocked.
    """
    if user.useractivity.is_blocked():
        messages.error(request, f"You are blocked until {user.useractivity.blocked}.")
        return redirect('post_page')
    return None

