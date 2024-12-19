from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('posts/', views.PostCreateAPIView.as_view(), name='create_post'),
    path('posts/<int:pk>/',views.DetailAPIView.as_view(),name='detail_post'),
    path('comments/', views.CommentCreateAPIView.as_view(), name='create_comment'),
    path('comments/<int:pk>/',views.CommentAPIView.as_view(),name='detail_comment'),
    path('', views.welcome, name='welcome'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('home/', views.PostView.as_view(), name="post_page"),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('authors/', views.AuthorsView.as_view(), name='author_list'), 
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('post/add/', views.AddPostView.as_view(), name='add_post'),
    path('post/edit/<slug:slug>/', views.EditPostView.as_view(), name='edit_post'),
    path('<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/<int:post_id>/like/', views.LikePostView.as_view(), name='like_post'),
    path('posts/<int:post_id>/dislike/', views.DislikePostView.as_view(), name='dislike_post'),
    path('subscription/<int:user_id>/',  views.SubscriptionUnsubscriptionView.as_view(), name='subscription'),
    path('chatgpt/generate-post/', views.ChatGPTGeneratePostView.as_view(), name='chatgpt_generate_post'),
    path('chatgpt/summarize-post/<int:pk>/', views.ChatGPTSummarizePostView.as_view(), name='chatgpt_summarize_post'),
    path('chatgpt/fix-grammar/<int:pk>/', views.ChatGPTFixGrammarView.as_view(), name='chatgpt_fix_grammar'),
    path('post/<int:pk>/analyze-sentiment/', views.AnalyzeSentimentView.as_view(), name='analyze_sentiment'),
]