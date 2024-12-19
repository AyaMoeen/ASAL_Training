import json
import requests
from datetime import datetime
from django.conf import settings
from django.utils.timezone import make_aware
from ..models import User, Post, Comment
from django.utils.text import slugify
import redis

from utils.redis_helpers import (
    set_to_redis_hash,
    get_from_redis_hash,
    get_all_from_redis_hash,
    remove_from_redis_hash,
)

REDIS_AUTHOR_DICT_KEY = "cached_authors"
REDIS_POST_DICT_KEY = "cached_posts"

FIRST_PAGE = 1

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def get_last_page(last_page_key):
    """
    Fetches the last page from Redis for pagination.
    """
    return int(redis_client.get(last_page_key) or FIRST_PAGE)

def fetch_data_from_api(endpoint, params=None):
    """
    Fetches data from the given API endpoint.
    """
    url = f"{settings.GOBLOG_API_BASE_URL}/{endpoint}"
    headers = {'Authorization': f"Bearer {settings.GOBLOG_API_TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    return response


def get_author_from_api(author_id):
    """
    This fetches the author details from  API if not found in the dictionary.
    """
    author_data = get_from_redis_hash(REDIS_AUTHOR_DICT_KEY, str(author_id))
    if author_data:
        return User.objects.get(id=int(author_data))
    
    response = fetch_data_from_api(f'blog/authors/{author_id}')
    
    if response.status_code == requests.codes.OK:
        author_data = response.json()
        user, _ = User.objects.get_or_create(
            id=author_id,
            defaults={
                'username': author_data.get('username', f'user_{author_id}'),
                'email': author_data.get('email', ''),
                'name': author_data.get('name', '')
            }
        )
        set_to_redis_hash(REDIS_AUTHOR_DICT_KEY, str(author_id), str(user.id))
        return user
    else:
        return None
    
def get_post_from_api(post_id):
    """
    This fetches the post details from  API if not found in the dictionary.
    """
    post_data = get_from_redis_hash(REDIS_POST_DICT_KEY, str(post_id))
    if post_data:
        try:
            post_data = json.loads(post_data)
            if Post.objects.filter(slug=post_data['slug']).exists():
                return post_data
            else:
                remove_from_redis_hash(REDIS_POST_DICT_KEY, str(post_id))
                return None
        except (KeyError, ValueError):
            remove_from_redis_hash(REDIS_POST_DICT_KEY, str(post_id))
            return None
        
    
    response = fetch_data_from_api(f'blog/posts/{post_id}')
    
    if response.status_code == requests.codes.OK:
        post_data = response.json()
        title = post_data.get('title', 'Untitled')
        slug = slugify(post_data.get('slug', ''))
        author_id = post_data.get('author_id')
        
        if not author_id:
            return None
        author_user = None
        user_id = get_from_redis_hash(REDIS_AUTHOR_DICT_KEY, str(author_id))
        if user_id:
            try:
                author_user = {"id": user_id}
            except User.DoesNotExist:
                return None
        else:
            author = get_author_from_api(author_id)
            if author:
                user_id = author.id
                author_user = {"id": user_id}
            else:
                return None

        post_dict  = {
            'slug': slug,
            'title': title,
            'body': post_data.get('body', ''),
            'author': author_user,
            'status': post_data.get('status', 'draft').lower(),
            'publish': post_data.get('publishAt'),
            'source': 'api',
        }

        set_to_redis_hash(REDIS_POST_DICT_KEY, str(post_id), json.dumps(post_dict))
        
        existing_posts = Post.objects.filter(slug=post_dict['slug']).values_list('slug', flat=True)
        posts_to_create = []
        posts_to_update = []
        
        if post_dict['slug'] in existing_posts:
            post_instance = Post(
                slug=post_dict['slug'],
                title=post_dict['title'],
                body=post_dict['body'],
                author=author_user,
                status=post_dict['status'],
                publish=post_dict['publish'],
                source=post_dict['source']
            )
            posts_to_update.append(post_instance)
        else:
            post_instance = Post(**post_dict)
            posts_to_create.append(post_instance)
        
        if posts_to_create:
            Post.objects.bulk_create(posts_to_create)

        if posts_to_update:
            Post.objects.bulk_update(
                posts_to_update, fields=['title', 'body', 'status', 'publish', 'source']
            )
            
        return post_instance
        
    else:
        return None
     
def fetch_authors():
    """
    This fetches the author from your API
    """
    last_page_key = "authors_last_page"
    last_page = get_all_from_redis_hash(REDIS_AUTHOR_DICT_KEY) 
    
    users_to_create = []  
    redis_updates = {}
    existing_users = get_all_from_redis_hash(REDIS_AUTHOR_DICT_KEY) or {}
    
    while True:
        params = {'page': last_page}
        response = fetch_data_from_api('blog/authors', params)

        if response.status_code == requests.codes.OK:
            authors_data = response.json().get("Authors", [])
            if not authors_data:
                break 

            for author in authors_data:
                author_id = author.get('ID')
                email = author.get('email')
                if author_id and author_id not in existing_users:
                    username = author.get('username', f"user_{email}")
                    user = User(username=username, email=email)
                    user.save()
                    users_to_create.append(user)
                    redis_updates[str(author_id)] = str(user.id)

            if users_to_create:
                User.objects.bulk_create(users_to_create)

                set_to_redis_hash(REDIS_AUTHOR_DICT_KEY, redis_updates)
                
                users_to_create.clear()
                redis_updates.clear()
            
                last_page += 1
                redis_client.set(last_page_key, last_page) 
        else:
            break
        
        
        
def fetch_posts():
    """
    Fetches posts from the API and dynamically retrieves missing authors.
    """
    last_page_key = "posts_last_page"
    last_page = get_last_page(last_page_key)
    
    posts_to_create = []  
    authors_to_create = []  

    while True:
        params = {'page': last_page}
        response = fetch_data_from_api('blog/posts', params)

        if response.status_code == requests.codes.OK:
            posts_data = response.json().get("Posts", [])
            if not posts_data:
                break

            for post in posts_data:
                post_id = post.get('ID')
                if not post_id:
                    continue
                
                cached_post = get_from_redis_hash(REDIS_POST_DICT_KEY, str(post_id))
                if cached_post:
                    continue
                
                title = post.get('title', 'Untitled')
                slug = slugify(post.get('slug', ''))
                author_id = post.get('author_id')

                if not author_id:
                    continue

                user_id = get_from_redis_hash(REDIS_AUTHOR_DICT_KEY, str(author_id))

                if user_id:
                        author_user = User.objects.get(id=user_id)
                else:
                    author = get_author_from_api(author_id)
                    if author:
                        user_id = author.id
                        set_to_redis_hash(REDIS_AUTHOR_DICT_KEY, str(author.id), str(author.id))
                        authors_to_create.append(author)
                        
                    else:
                        continue

                db_post = Post(
                    slug=slug,
                    title=title,
                    body=post.get('body', ''),
                    author=author_user,
                    status=post.get('status', 'draft').lower(),
                    publish=post.get('publishAt'),
                    source='api',
                )
                posts_to_create.append(db_post)
                set_to_redis_hash(REDIS_POST_DICT_KEY, str(post_id), json.dumps(post))
                
            if authors_to_create:
                User.objects.bulk_create(authors_to_create)
                authors_to_create.clear()

            if posts_to_create:
                Post.objects.bulk_create(posts_to_create)
                last_page += 1
                redis_client.set(last_page_key, last_page)

                posts_to_create.clear()
                authors_to_create.clear()

        else:
            break
 
def fetch_comments():
    """
    This fetches the comment from API 
    """
    last_page_key = "comments_last_page"
    last_page = get_last_page(last_page_key)
    
    comments_to_create = []
    existing_comments = set()

    while True:
        params = {'page': last_page}
        response = fetch_data_from_api('blog/comments', params)
        
        if response.status_code == requests.codes.OK:
            comments_data = response.json().get("Comments", [])
            if not comments_data:
                break

            for comment in comments_data:
                post_id = comment.get('PostID')

                cached_post = get_from_redis_hash(REDIS_POST_DICT_KEY, str(post_id))

                if cached_post:
                    post = json.loads(cached_post)
                else:
                    post = get_post_from_api(post_id)

                if post:
                    set_to_redis_hash(REDIS_POST_DICT_KEY, str(post_id), json.dumps(post))
                    created_str = comment.get('CreatedAt')
                    try:
                        created_date = make_aware(datetime.strptime(created_str, '%Y-%m-%dT%H:%M:%S.%fZ'))
                        
                        comment_key = (post.id, comment['name'], comment['email'], comment['body'], created_date)
                        if comment_key not in existing_comments:
                            existing_comments.add(comment_key)
                            comments_to_create.append(Comment(
                                post=post,
                                name=comment.get('name'),
                                email=comment.get('email'),
                                body=comment.get('body'),
                                created=created_date,
                                active=True
                            ))
                    except ValueError:
                        continue

            if comments_to_create:
                Comment.objects.bulk_create(comments_to_create)
                comments_to_create.clear()

                last_page += 1
                redis_client.set(last_page_key, last_page)
        else:
            break 