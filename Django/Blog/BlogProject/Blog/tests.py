from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from Blog.utils.achievement_utils import check_achievements
from .models import Like, Post, Comment, Subscription, UserAchievement, UserActivity
from .forms import CommentForm
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User


PAGINATION_NUMBER = 3 
STATUS = list(dict(Post.Choices).keys())[1]
WARNINGS = 1

def create_post(title='Test Post', body='Test body', author=None, 
                status=STATUS):
    """
    Utility function to create a Post object.
    """
    if not author:
        author = get_user_model().objects.first()

    return Post.objects.create(
        title=title,
        body=body,
        slug=title.lower().replace(" ", "-"),
        author=author,
        status=status 
    )
    
class ModelTest(TestCase):
    def setUp(self):
        """
        Setup for the test, creating posts for the list view to display.
        """
        self.user = get_user_model().objects.create_user(
            username='aya',
            email='aya@gmail.com',
            password='123456'
        )
        posts = []
        
        for i in range(4):
             posts.append(
                Post(
                    title=f"Post {i+1}",
                    body=f"This is post {i+1}",
                    slug=f"post-{i+1}",
                    publish=timezone.now(),
                    author=self.user,
                    status=STATUS
                )
             )
        Post.objects.bulk_create(posts)
        self.post1 = Post.objects.get(slug='post-1')
        self.post2 = Post.objects.get(slug='post-2')
        self.post3 = Post.objects.get(slug='post-3')
        self.post4 = Post.objects.get(slug='post-4')
        
        self.other_user = get_user_model().objects.create_user(
            username="user1",
            email="user1@gmail.com",
            password="123456"
        )
        self.comment_user = get_user_model().objects.create_user(
            username="ahmed",
            email="ahmedawwad@gmail.com",
            password="testpassword"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
 
class PostViewTest(ModelTest):

    def test_post_list_view_status_code(self):
        """
        Test the status code of the post list view.
        """
        url = reverse('post_page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
    
    def test_post_list_view_template(self):
        """
        Test if the post list view uses the correct template.
        """
        url = reverse('post_page')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/post.html')

    def test_post_list_pagination(self):
        """
        Test pagination by checking that only 3 posts are shown on the each page.
        """
        url = reverse('post_page')
        response = self.client.get(url)
        self.assertEqual(len(response.context['page_obj']), PAGINATION_NUMBER)
        
class PostDetailViewTest(ModelTest):

    def test_post_detail_view_status_code(self):
        """
        Test the status code of the post detail view.
        """
        url = reverse('post_detail', args=[self.post1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_post_detail_view_template(self):
        url = reverse('post_detail', args=[self.post1.slug])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/detail_of_post.html')
        
    def test_post_detail_view_comments(self):
        """
        Test that comments are displayed in the post detail view.
        """
        Comment.objects.create(
            post=self.post1, 
            name="ahmed", 
            email="ahmedawwad@gmail.com", 
            body="test comment"
        )
        url = reverse('post_detail', args=[self.post1.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test comment")

class CommentFormTest(TestCase):
    def test_comment_form_valid_data(self):
        factory = RequestFactory()
        request = factory.get('/some-path/')
        user = User.objects.create_user(username='ahmed', email='ahmedawwad@gmail.com', password='123456')
        request.user = user

        data = {
            'body': 'This is a test comment',
        }

        form = CommentForm(data=data, request=request)
        if not form.is_valid():
            print(form.errors)  
        self.assertTrue(form.is_valid())

    def test_comment_form_invalid_data(self):
        """
        Test if the comment form is invalid with missing data.
        """
        form = CommentForm(data={
            'name': '',
            'email': 'ahmedawwad@gmail.com',
            'body': ''
        })
        self.assertFalse(form.is_valid())


       
class SpamProtectionTest(ModelTest):
    
    def setUp(self):
        super().setUp()
        self.client.login(username='aya', password='123456') 

    def test_spam_protection(self):
        """
        Test that spam protection works by blocking rapid successive comments.
        """
        url = reverse('post_detail', args=[self.post1.slug])
        form_data = {
            'name': 'aya',
            'email': 'aya165@gmail.com',
            'body': 'spam test comment.'
        }
        self.client.post(url, data=form_data)
        response = self.client.post(url, data=form_data)
        self.assertContains(response, "Please wait 30 seconds before submitting another comment.")

    def test_bad_word_filtering(self):
        """
        Test that bad words in a comment are censored and comment activation is handled.
        """
        url = reverse('post_detail', args=[self.post1.slug])
        form_data = {
            'name': 'aya',
            'email': 'aya165@gmail.com',
            'body': 'dumbass'
        }
        response = self.client.post(url, data=form_data)
        self.assertContains(response, '****')
       
class AuthorsViewTest(ModelTest):
    def test_author_list_view_status_code(self):
        """
        Test if the AuthorsView renders correctly.
        """
        url = reverse('author_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_author_list_view_template(self):
        """
        Test if the AuthorsView uses the correct template.
        """
        url = reverse('author_list')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'blog/author_list.html')
        
class AddPostViewTest(ModelTest):
    def test_add_post_view(self):
        """
        Test adding a new post using AddPostView.
        """
        self.client.force_login(self.user)  
        url = reverse('add_post')
        data = {
            'title': 'Test1',
            'body': 'Post for test',
            'status': STATUS
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.filter(title='Test1').exists())
        
        new_post = Post.objects.get(title='Test1')
        self.assertEqual(new_post.status, 'published')
        
class EditPostViewTest(ModelTest):
    def test_edit_post_by_author(self):
        """
        Test editing a post by the author.
        """
        self.client.login(username="aya", password="123456")
        
        url = reverse('edit_post', args=[self.post1.slug]) 

        data = {
            'title': 'Updated Post',
            'body': 'Updated body content.',
            'status': STATUS
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, 'Updated Post')
    
class PostCreateAPITest(ModelTest):
    POST_COUNT = 5
    def test_post_creation_api(self):
        """
        Test creating a post via the API.
        """
        url = reverse('create_post')
        data = {
            'title': 'API Post',
            'body': 'Body Post',
            'status': STATUS
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), self.POST_COUNT)
        self.assertEqual(Post.objects.first().title, 'API Post')
        
class CommentCreateAPITest(ModelTest):
    COMMENT_COUNT = 1
    def test_comment_creation_api(self):
        """
        Test creating a comment via the API.
        """
        get_user_model().objects.create_user(
            username="testuser",
            password="password123",
            email="moinaya@gmail.com"
        )
    
        url = reverse('create_comment')
        data = {
            'post': self.post1.id,
            'name': 'Test',
            'email': 'moinaya@gmail.com',  
            'body': 'Test Comment'
        }
    
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), self.COMMENT_COUNT)
        self.assertEqual(Comment.objects.first().body.strip(), 'Test Comment'.strip())

    def test_comment_creation_without_authentication(self):
        """
        Test creating a comment without being authenticated.
        """
        self.client.logout()  
        url = reverse('create_comment')
        data = {
            'post': self.post1.id,
            'name': 'userA',
            'email': 'userA@gmail.com',
            'body': 'comment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class WarningSystemTestCase(ModelTest):
    
    def test_warning_for_bad_words(self):
        comment = Comment.objects.create(
            post=self.post1, 
            name="ahmed", 
            email="ahmedawwad@gmail.com", 
            body="shit shit shit shit"
        )
        self.comment_user.refresh_from_db()
        self.comment_user.useractivity.refresh_from_db()
        self.assertFalse(comment.active)
        self.assertEqual(self.comment_user.useractivity.warnings, WARNINGS)

class PostReactionViewTests(ModelTest):

    def test_like_post(self):
        """
        Test liking a post
        """
        self.client.login(username='aya', password='123456')  
        url = reverse('like_post', args=[self.post1.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post1, value=Like.LIKE).exists())

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post1).exists())

    def test_dislike_post(self):
        """
        Test disliking a post
        """
        self.client.login(username='aya', password='123456') 
        url = reverse('dislike_post', args=[self.post1.id])
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post1, value=Like.DISLIKE).exists())

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post1).exists())

class SubscriptionUnsubscriptionViewTests(ModelTest):
    USER_NOT_FOUND = 99999
    def test_subscription(self):
        """
        Test subscribing and unsubscribing functionality
        """
        self.client.login(username='aya', password='123456') 
        url = reverse('subscription', args=[self.other_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'subscribed')
        self.assertTrue(Subscription.objects.filter(subscriber=self.user, subscribed_to=self.other_user).exists())
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'unsubscribed')
        self.assertFalse(Subscription.objects.filter(subscriber=self.user, subscribed_to=self.other_user).exists())

    def test_subscription_user_not_found(self):
        """
        Test when the user to subscribe to is not found
        """
        self.client.login(username='aya', password='123456')  
        url = reverse('subscription', args=[self.USER_NOT_FOUND]) 
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'User not found')

class ProfileTests(ModelTest):
    
    COUNT_IN_DAY = 3
    DAY = 1
    CONST_ZERO = 0
    
    def setUp(self):
        """
        Setup for the test, creating a user profile.
        """
        super().setUp()  
        self.useractivity = self.user.useractivity 

    def test_reset_daily_limits(self):
        """
        Test if daily post and view limits reset properly.
        """
        self.useractivity.count_post_day = self.COUNT_IN_DAY
        self.useractivity.view_count_day = self.COUNT_IN_DAY
        self.useractivity.last_action_time = timezone.now().date() - timedelta(days=self.DAY)
        self.useractivity.save()

        self.useractivity.reset_daily_limits()
        self.useractivity.refresh_from_db()

        self.assertEqual(self.useractivity.count_post_day, self.CONST_ZERO)
        self.assertEqual(self.useractivity.view_count_day, self.CONST_ZERO)

    def test_is_blocked(self):
        """
        Test if the user is blocked.
        """
        self.useractivity.blocked = timezone.now() + timedelta(days=self.DAY)
        self.useractivity.save()

        self.assertTrue(self.useractivity.is_blocked())

    def test_is_not_blocked(self):
        """
        Test if the user is not blocked.
        """
        self.useractivity.blocked = timezone.now() - timedelta(days=self.DAY)
        self.useractivity.save()

        self.assertFalse(self.useractivity.is_blocked())
        
class ChatGPTSummarizePostViewTest(ModelTest):
    
    def test_summarize_post_success(self):
        """
        Test that a successful summary is generated for an existing post.
        """
        url = reverse('chatgpt_summarize_post', args=[self.post1.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.json())

    def test_summarize_post_not_found(self):
        """
        Test that an error is returned when the post does not exist.
        """
        url = reverse('chatgpt_summarize_post', args=[999])  
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Post not found.')

class ChatGPTFixGrammarViewTest(ModelTest):
    
    def test_fix_grammar_success(self):
        """
        Test that grammar and typos are fixed successfully for an existing post.
        """
        url = reverse('chatgpt_fix_grammar', args=[self.post1.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('fixed_grammar', response.json())

    def test_fix_grammar_post_not_found(self):
        """
        Test that an error is returned when the post does not exist.
        """
        url = reverse('chatgpt_fix_grammar', args=[999])  
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Post not found.')
        
class AnalyzeSentimentViewTest(ModelTest):
    
    def test_analyze_sentiment_success(self):
        """
        Test that a sentiment analysis task is successfully queued for a post.
        """
        url = reverse('analyze_sentiment', args=[self.post1.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_analyze_sentiment_post_not_found(self):
        """
        Test that an error is returned when the post does not exist.
        """
        url = reverse('analyze_sentiment', args=[999])  
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Post not found.')


class AchievementsTestCase(ModelTest):
    def test_post_count_badge(self):
        posts = [
            Post(
                title=f"Post {i+5}",
                author=self.user,
                body="Test body",
                status="published",
            )
            for i in range(6)
        ]
        Post.objects.bulk_create(posts)

        check_achievements(self.user)

        badges = UserAchievement.objects.filter(user=self.user, badge__name="Posts: 10")
        self.assertEqual(badges.count(), settings.ONE)

    def test_likes_received_badge(self):
        users = [
            User(username=f'user{i+2}', password='password123')
            for i in range(100)
        ]
        User.objects.bulk_create(users)

        likes = [
            Like(post=self.post1, user=users[i], value=Like.LIKE)
            for i in range(100)
        ]
        Like.objects.bulk_create(likes)
        check_achievements(self.user)

        badges = UserAchievement.objects.filter(user=self.user, badge__name="Likes Received: 100")
        self.assertEqual(badges.count(), settings.ONE)
        
class LeaderboardTestCase(ModelTest):
    def test_leaderboard_by_posts(self):
        leaderboard = UserActivity.leaderboard_by_posts()

        self.assertEqual(leaderboard[0], self.user) 
        self.assertEqual(leaderboard[1], self.comment_user)