from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from Blog.utils.utils import check_for_bad_words
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count


class UserActivity(models.Model):
    user: models.OneToOneField = models.OneToOneField(User, on_delete=models.CASCADE)
    warnings: models.IntegerField = models.IntegerField(default=0)
    blocked: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    count_post_day: models.IntegerField = models.IntegerField(default=0)
    view_count_day: models.IntegerField = models.IntegerField(default=0)
    last_action_time: models.DateField = models.DateField(default=timezone.now)
    last_login_date: models.DateField = models.DateField(null=True, blank=True)  
    weekly_login_streak: models.IntegerField = models.IntegerField(default=0)
    
    def is_blocked(self):
        return self.blocked and self.blocked > timezone.now()
    
    def reset_daily_limits(self):
        """ Reset the limits of user when change the date"""
        if self.last_action_time is None or self.last_action_time < timezone.now().date():
            self.count_post_day = settings.CONST_ZERO
            self.view_count_day = settings.CONST_ZERO
            self.last_action_time = timezone.now().date()
            self.save()
    
    def get_weekly_login_streak(self):
        """
        Calculates the weekly login streak of the user.
        Updates the streak count if necessary.
        """
        today = timezone.now().date()
        if self.last_login_date == today:
            return self.weekly_login_streak  
        
        if self.last_login_date and (today - self.last_login_date).days == settings.ONE:
            self.weekly_login_streak += settings.ONE
        else:
            self.weekly_login_streak = settings.ONE

        self.last_login_date = today
        self.save()
        return self.weekly_login_streak
    
    @staticmethod
    def leaderboard_by_posts():
        return User.objects.annotate(
            post_count=Count('blog_posts')
        ).order_by('-post_count')[:10]

    @staticmethod
    def leaderboard_by_likes():
        return User.objects.annotate(
            like_count=Sum('blog_posts__likes__value')
        ).order_by('-like_count')[:10]

    @staticmethod
    def leaderboard_by_comments():
        return User.objects.annotate(
            comment_count=Count('blog_posts__comments')
        ).order_by('-comment_count')[:10]
    
    def __str__(self):
        return f'{self.user.username} Activity'

class PublishedManager(models.Manager):
    """
    custom manager for post model
    """
    def get_queryset(self):
        return super().get_queryset().filter(status='published')

class Post(models.Model):
    SOURCE_CHOICES = (
        ('blog', 'Blog'),
        ('api', 'API'),
    )
    Choices  = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title: models.CharField = models.CharField(max_length=250)
    slug: models.SlugField = models.SlugField(max_length=250, unique_for_date='publish')
    author: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    body: models.TextField = models.TextField()
    publish: models.DateTimeField = models.DateTimeField(default=timezone.now)
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated: models.DateTimeField = models.DateTimeField(auto_now=True)
    status: models.CharField = models.CharField(max_length=10, choices=Choices)
    source: models.CharField = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='blog')
    objects = models.Manager() 
    published = PublishedManager() 

    sentiment_label: models.CharField = models.CharField(max_length=20, null=True, blank=True)  
    sentiment_score: models.FloatField = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ('-publish',)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
        if self.author.useractivity.count_post_day >= settings.COUNT_FOR_DAY:
            raise ValidationError("You have reached your daily limit for creating posts.")

        super().save(*args, **kwargs)

    def total_likes(self):
        return self.likes.filter(value=Like.LIKE).count()

    def total_dislikes(self):
        return self.likes.filter(value=Like.DISLIKE).count()

    def user_reaction(self, user):
        like = self.likes.filter(user=user).first()
        return like.value if like else None

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'slug': self.slug})
    
    def __str__(self):
        return self.title
    
    
class Comment(models.Model):
     
    post: models.ForeignKey = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name: models.CharField = models.CharField(max_length=80)
    email: models.EmailField = models.EmailField()
    body: models.TextField = models.TextField()
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated: models.DateTimeField = models.DateTimeField(auto_now=True)
    active: models.BooleanField = models.BooleanField(default=True)
    sentiment_label: models.CharField = models.CharField(max_length=20, null=True, blank=True)
    sentiment_score: models.FloatField = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ('-created',)

    def clean(self):
        if not self.email:
            raise ValidationError(_("Email is required for commenting."))

        try:
            user = User.objects.get(email=self.email)
            self.name = user.username
        except User.DoesNotExist:
            raise ValidationError(_("The provided email does not correspond to any registered user."))
        super().clean()
        
    def save(self, *args, **kwargs):
        user = User.objects.get(email=self.email)
        
        if user.useractivity.is_blocked():
            raise ValidationError("You are blocked from posting comments until {}".format(user.useractivity.blocked))
        
        time_of_last_commant = Comment.objects.filter(email=self.email).order_by('-created').first()
        if time_of_last_commant and (timezone.now() - time_of_last_commant.created).total_seconds() < settings.TIME_BETWEEN_COMMENT:
            raise ValidationError(f"Please wait {int(settings.TIME_BETWEEN_COMMENT)} seconds before submitting another comment.")
 
        active_status, censored_body = check_for_bad_words(self.body, self.email)
        self.body = censored_body
        self.active = active_status

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Comment by {self.name} on {self.post}' 
   
class Like(models.Model):
    LIKE = 1
    DISLIKE = -1

    LIKE_CHOICES = [
        (LIKE, "Like"),
        (DISLIKE, "Dislike"),
    ]
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post: models.ForeignKey = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    value: models.IntegerField = models.IntegerField(choices=LIKE_CHOICES, default=LIKE)
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated: models.DateTimeField = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'post')
        
    def __str__(self):
       return f'{self.user.username} liked {self.post.title}'
 
class Subscription(models.Model):
    subscriber: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions_as_subscriber')
    subscribed_to: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions_as_subscribed_to')
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together =  ('subscriber', 'subscribed_to')

    def __str__(self):
        return f'{self.subscriber.username} subscribed to {self.subscribed_to.username}'

class Notification(models.Model):
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message: models.TextField = models.TextField()
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    is_read: models.BooleanField = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.message}'
    
class Badge(models.Model):
    name: models.CharField = models.CharField(max_length=100)
    description: models.TextField = models.TextField()
    condition: models.CharField = models.CharField(max_length=100, help_text="Condition to earn this badge")
    created: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user: models.ForeignKey = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    badge: models.ForeignKey = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_achievements')
    earned_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"
