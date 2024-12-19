from celery import shared_task # type: ignore
import openai
import requests # type: ignore
from Blog.services.services import fetch_authors, fetch_posts, fetch_comments
from .models import Post, Subscription, Notification
from django.core.mail import send_mail
from django.conf import settings
from transformers import pipeline # type: ignore
from Blog.models import Comment

sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

openai.api_key = settings.OPENAI_API_KEY

@shared_task
def fetch_all_data():
    fetch_authors()
    fetch_posts()
    fetch_comments()


@shared_task
def create_notifications_task(post_title, author_username):
    """
    Creates notification entries for subscribers when a new post is created.
    """
    subscriptions = Subscription.objects.filter(subscribed_to__username=author_username)
    notifications = [
        Notification(
            user=subscription.subscriber,
            message=f"{author_username} has posted a new article: {post_title}"
        )
        for subscription in subscriptions
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)

@shared_task
def send_email_notifications_task(post_title, author_username, post_id):
    """
    Sends email notifications to subscribers when a new post is created.
    """
    subscriptions = Subscription.objects.filter(subscribed_to__username=author_username)
    for subscription in subscriptions:
        send_mail(
            'New Post Published',
            f"{author_username} has posted a new article: {post_title}",
            'from@example.com',
            [subscription.subscriber.email],
            fail_silently=False,
        )
        
@shared_task     
def generate_text_task(prompt, max_tokens=100, temperature=0.7):
    """
    A background task to generate text using OpenAI API.
    """
    try:
        response = openai.completions.create(
            model="gpt-3.5-turbo",  
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response['choices'][0]['text'].strip()
    except Exception as e:
        return f"Error: {str(e)}"
    

@shared_task(bind=True, max_retries=3)
def analyze_sentiment_task(self, instance_id, instance_type, text):
    """
    Sends the text to the Lambda function for sentiment analysis and returns the result.
    """
    sentiment_url = settings.SENTIMENT_LAMBDA_URL

    try:
        response = requests.post(
            sentiment_url,
            json={"text": text}
        )
        response.raise_for_status()
        sentiment_data = response.json()

        if isinstance(sentiment_data, list) and len(sentiment_data) > 0:
            first_entry_list = sentiment_data[0]
            if isinstance(first_entry_list, list) and len(first_entry_list) > 0:
                first_entry = first_entry_list[0]
                sentiment = first_entry.get('label')  
                confidence = first_entry.get('score')
            else:
                raise ValueError("Unexpected inner list format in API response")
        else:
            raise ValueError("Unexpected API response format")

        if instance_type == 'post':
            Post.objects.filter(pk=instance_id).update(
                sentiment_label=sentiment,
                sentiment_score=confidence
            )
        elif instance_type == 'comment':
            Comment.objects.filter(pk=instance_id).update(
                sentiment_label=sentiment,
                sentiment_score=confidence
            )
    except requests.HTTPError as e:
        raise self.retry(exc=e, countdown=5)
    except Exception:
        raise