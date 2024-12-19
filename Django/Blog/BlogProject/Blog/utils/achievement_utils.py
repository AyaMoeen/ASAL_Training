import math
from django.conf import settings
from Blog.models import Badge, Like, Post, UserAchievement
from django.db import transaction


def check_achievements(user):
    post_count = Post.objects.filter(author=user, status='published').count()
    if post_count and is_power_of_ten(post_count):
        award_badge(user, f"Posts: {post_count}", f"Published {post_count} posts.")

    like_count = sum(post.total_likes() for post in Post.objects.filter(author=user))
    if like_count and like_count % settings.NUMBER_LIKES_IN_HIS_POST == settings.CONST_ZERO:
        award_badge(user, f"Likes Received: {like_count}", f"Received {like_count} likes on posts.")

    given_likes = Like.objects.filter(user=user, value=Like.LIKE).count()
    if given_likes and given_likes % settings.NUMBER_LIKES_IN_POSTS == settings.CONST_ZERO:
        award_badge(user, f"Likes Given: {given_likes}", f"Given {given_likes} likes.")

    weekly_logins = user.useractivity.get_weekly_login_streak()
    if weekly_logins and weekly_logins % settings.WEEKLY_LOGIN_STREAK == settings.CONST_ZERO:
        award_badge(user, f"Weekly Login Streak: {weekly_logins}", f"Logged in for {weekly_logins} consecutive weeks.")

def is_power_of_ten(num):
    return num > settings.CONST_ZERO and (10 ** int(math.log10(num)) == num)

@transaction.atomic
def award_badge(user, name, description):
    try:
        badge, created = Badge.objects.get_or_create(name=name, defaults={"description": description})
        achievement, created  = UserAchievement.objects.get_or_create(user=user, badge=badge)
    except Exception as e:
        return f"Error: {str(e)}"
       