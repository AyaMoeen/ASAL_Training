       
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Like, UserActivity, Post, Comment
from .tasks import create_notifications_task, send_email_notifications_task
from django.contrib.auth.signals import user_logged_in
from Blog.utils.achievement_utils import check_achievements

@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    if not hasattr(instance, 'useractivity'):
        UserActivity.objects.create(user=instance)
    else:
        instance.useractivity.save()
        
@receiver(post_save, sender=Post)
def notify_subscribers(sender, instance, created, **kwargs):
    """
    Notify users when a new post is published by triggering background tasks.
    """
    if created and instance.status == 'published':
        create_notifications_task.delay(instance.title, instance.author.username)
        send_email_notifications_task.delay(instance.title, instance.author.username, instance.id)

@receiver(post_save, sender=Post)
def post_created(sender, instance, created, **kwargs):
    if created:
        check_achievements(instance.author)

@receiver(post_save, sender=Like)
def like_added(sender, instance, created, **kwargs):
    if created:
        check_achievements(instance.user)
        check_achievements(instance.post.author)

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    check_achievements(user)
    
@receiver(post_save, sender=Post)
def update_post_metrics(sender, instance, **kwargs):
    user_activity, _ = UserActivity.objects.get_or_create(user=instance.author)
    user_activity.leaderboard_by_posts()

@receiver(post_save, sender=Like)
def update_like_metrics(sender, instance, **kwargs):
    user_activity, _ = UserActivity.objects.get_or_create(user=instance.post.author)
    user_activity.leaderboard_by_likes()

@receiver(post_save, sender=Comment)
def update_comment_metrics(sender, instance, **kwargs):
    user_activity, _ = UserActivity.objects.get_or_create(user=instance.post.author)
    user_activity.leaderboard_by_comments()