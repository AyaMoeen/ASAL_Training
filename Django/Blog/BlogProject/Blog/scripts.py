import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('BASE_URL')
TOKEN = os.getenv('TOKEN')

if not BASE_URL or not TOKEN:
    raise ValueError("BASE_URL or TOKEN is not set in .env file")

HEADERS = {
    'Authorization': f'Token {TOKEN}'
}

def list_posts():
    """List all posts from the API."""
    response = requests.get(f'{BASE_URL}posts/', headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return {'error': response.status_code, 'message': response.text}

def create_post(title, body, status):
    """Create a new post via the API."""
    data = {
        'title': title,
        'body': body,
        'status': status
    }
    response = requests.post(f'{BASE_URL}posts/', json=data, headers=HEADERS)
    if response.status_code == 201:
        return response.json()
    return {'error': response.status_code, 'message': response.text}

def create_comment(post_id, name, email, body):
    """Create a new comment on a post."""
    data = {
        'post': post_id,
        'name': name,
        'email': email,
        'body': body
    }
    response = requests.post(f'{BASE_URL}comments/', json=data, headers=HEADERS)
    if response.status_code == 201:
        return response.json()
    return {'error': response.status_code, 'message': response.text}

if __name__ == "__main__":
    list_posts()
    create_post('Ayosh', 'Test post', 'published')
    create_comment(5023, 'Ayosh', 'ayamoeenawwad@gmail.com', 'hhhh')
