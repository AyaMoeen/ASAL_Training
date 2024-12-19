from django.forms import ValidationError
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from better_profanity import profanity # type: ignore
from Blog.tasks import analyze_sentiment_task
from .forms import CommentForm, PostForm, UserRegistrationForm
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.views import View
from Blog.models import Post, Comment, Like, Subscription, UserActivity
from django.contrib import messages
from .serializers import PostSerializer, CommentSerializer
from rest_framework import generics
from .permissions import IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly
from rest_framework.authentication import TokenAuthentication
from Blog.utils.utils import check_user_block_status
from django.http import JsonResponse
from typing import Optional
from django.conf import settings
from Blog.utils.activity_utils import check_daily_limit
from Blog.services.openai_service import generate_text

profanity.load_censor_words()

class AuthorsView(View):
    def get(self, request):
        try:
            return render(request, 'blog/author_list.html')
        except ValueError as e:
            return HttpResponse(str(e), status=500)
        
class PostView(ListView):
    model = Post
    template_name = 'blog/post.html'
    context_object_name = 'posts'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        """Fetches the posts and applies any filters."""
        source_filter = self.request.GET.get('source', None)
        queryset = Post.objects.all()
        if source_filter:
            queryset = queryset.filter(source=source_filter)
        return queryset

    def get_context_data(self, **kwargs):
        """Adds additional context such as user-specific like/dislike info."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            for post in context['posts']:
                like_obj = post.likes.filter(user=user).first()
                post.user_reaction = like_obj.value if like_obj else None
        return context

    def get(self, request, *args, **kwargs):
        """Handles pagination and returns the page with updated context."""
        try:
            paginator = Paginator(self.get_queryset(), self.paginate_by)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            user = request.user
            if user.is_authenticated:
                for post in page_obj:
                    like_obj = post.likes.filter(user=user).first()
                    post.user_reaction = like_obj.value if like_obj else None

            return render(
                request, 
                self.template_name, 
                {
                    'page_obj': page_obj,
                    'posts': page_obj,
                }
            )
        except ValueError as e:
            return HttpResponse(str(e), status=500)
        
class PostDetailView(DetailView):
    """ Post Detail VIEW with comment """
    model = Post
    template_name = 'blog/detail_of_post.html'
    context_object_name = 'post'
    queryset = Post.published.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        post = self.get_object()
        
        context['sentiment'] = post.sentiment_label  
        context['sentiment_confidence'] = post.sentiment_score 
        
        context['user_like'] = None
        if user.is_authenticated:
            like = post.likes.filter(user=user).first()
            context['user_like'] = like.value if like else None

        context['comments']  = self.object.comments.filter(active=True)
        return context
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_profile = request.user.useractivity
            
            if not check_daily_limit(user_profile, settings.COUNT_FOR_DAY, settings.COUNT_TO_WARNINGS, request, limit_type="read"):
                return redirect('post_page')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        comment_form = CommentForm(request.POST, request=request)  
        new_comment = None

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = self.object

            if request.user.is_authenticated:
                new_comment.name = request.user.username
                new_comment.email = request.user.email
            else:
                messages.error(request, "You must be logged in to post a comment.")
                return redirect('login') 
            
            try:
                new_comment.save()
                analyze_sentiment_task.delay(new_comment.id, 'comment', new_comment.body)
                if new_comment.active:
                    messages.success(request, "Your comment has been submitted successfully!")
                else:
                    user = User.objects.get(email=new_comment.email)
                    useractivity = user.useractivity
                    if useractivity.is_blocked():
                        messages.error(request, f"You are blocked until {useractivity.blocked}.")
                    else:
                        messages.warning(request, f"You received a warning! Total warnings: {useractivity.warnings}")
            except ValidationError as e:
                messages.error(request, e.message)
        
        context = self.get_context_data()
        context['new_comment'] = new_comment
        context['comment_form'] = comment_form
        context['current_view_count'] = self.request.user.useractivity.view_count_day if self.request.user.is_authenticated else settings.CONST_ZERO
        return self.render_to_response(context)    

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            return render(request, 'registration/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'user_form': user_form})


def welcome(request):
    email = request.GET.get('email')  
    
    if email:
        user_exists = User.objects.filter(email=email).exists()
        if user_exists:
            return redirect('login')  
        else:
            return redirect('register') 
    else:
        return render(request, 'blog/welcome.html')

class AddPostView(CreateView):
    model = Post
    fields = ['title', 'body', 'status']
    template_name = 'blog/add_post.html'
    success_url = reverse_lazy('post_page')
    
    def form_valid(self, form):
        block_check = check_user_block_status(self.request.user, self.request)
        if block_check:
            return block_check  
        
        useractivity = self.request.user.useractivity
        if not check_daily_limit(useractivity, settings.COUNT_FOR_DAY, settings.COUNT_TO_WARNINGS, self.request, limit_type="post"):
            return redirect('post_page')

        form.instance.author = self.request.user
        messages.success(self.request, "Your post has been added successfully!")
        response = super().form_valid(form)

        analyze_sentiment_task.delay(self.object.id, 'post', self.object.body)

        return response

    def form_invalid(self, form):
        messages.error(self.request, "There was an error adding your post. Please try again.")
        return super().form_invalid(form)

    def get_success_url(self):
        return self.object.get_absolute_url() 

class EditPostView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/edit_post.html'
    
    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        if post.author != self.request.user:
            messages.error(self.request, "You are not allowed to edit this post.")
            return redirect('post_page') 
        return post

    def form_valid(self, form):
        block_check = check_user_block_status(self.request.user, self.request)
        if block_check:
            return block_check 
        messages.success(self.request, "Your post has been updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating your post. Please try again.")
        return super().form_invalid(form)

class PostCreateAPIView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        return post

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
       
class DetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

class CommentCreateAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

class CommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

class PostReactionView(View):
    reaction_type: Optional[int] = None  

    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        reaction = Like.objects.filter(user=request.user, post=post).first()
        
        if reaction:
            if reaction.value == self.reaction_type:
                reaction.delete()  
            else:
                reaction.value = self.reaction_type  
                reaction.save()
        else:
            Like.objects.create(user=request.user, post=post, value=self.reaction_type) 

        return redirect('post_page')
    
class LikePostView(PostReactionView):
    reaction_type = Like.LIKE

class DislikePostView(PostReactionView):
    reaction_type = Like.DISLIKE


class SubscriptionUnsubscriptionView(View):
    def post(self, request, user_id):
        try:
            author = User.objects.get(id=user_id)
            subscription, created = Subscription.objects.get_or_create(
                subscriber=request.user, 
                subscribed_to=author
            )
            if not created:  
                subscription.delete()
                return JsonResponse({'status': 'unsubscribed'})
            return JsonResponse({'status': 'subscribed'})
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

class ChatGPTGeneratePostView(View):
    def post(self, request):
        data = request.POST
        prompt = data.get("prompt", "")
        if not prompt:
            return JsonResponse({"error": "Prompt is required."}, status=400)

        generated_text = generate_text(prompt, max_tokens=500)
        return JsonResponse({"generated_text": generated_text})

class ChatGPTSummarizePostView(View):
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)
        
        summary_prompt = f"Summarize this post:\n\n{post.body}"

        try:
            generated_text = generate_text(summary_prompt)
            return JsonResponse({"summary": generated_text})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

class ChatGPTFixGrammarView(View):
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return JsonResponse({"error": "Post not found."}, status=404)

        grammar_prompt = f"Fix grammar and typos in this post:\n\n{post.body}"
        fixed_text = generate_text(grammar_prompt, max_tokens=500)
        post.body = fixed_text
        post.save()
        return JsonResponse({"fixed_grammar": fixed_text}) 

class AnalyzeSentimentView(View):
    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except post.DoesNotExist:
            return JsonResponse({'error': 'Post not found.'}, status=404)
        
        analyze_sentiment_task.delay(post.id, 'post', post.body)

        return JsonResponse({'message': 'Sentiment analysis queued.'})

class LeaderboardView(View):
    def get(self, request, *args, **kwargs):
        leaderboard_posts = UserActivity.leaderboard_by_posts()
        leaderboard_likes = UserActivity.leaderboard_by_likes()
        leaderboard_comments = UserActivity.leaderboard_by_comments()

        context = {
            'leaderboard_posts': leaderboard_posts,
            'leaderboard_likes': leaderboard_likes,
            'leaderboard_comments': leaderboard_comments,
        }

        return render(request, 'blog/leaderboard.html', context)
