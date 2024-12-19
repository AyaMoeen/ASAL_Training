import json
import requests
import os
from dotenv import load_dotenv # type: ignore
load_dotenv()

HUGGING_FACE_URL = os.getenv('HUGGING_FACE_URL')
API_TOKEN_HUGGING_FACE = os.getenv('API_TOKEN_HUGGING_FACE')
def analyze_sentiment(event, context):
    try:
        if 'body' not in event or not event['body']:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Request body is missing.'})
            }

        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON format in request body.'})
            }

        text = request_body.get('text', '').strip()

        if not text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Text field is required.'})
            }

        huggingface_url = HUGGING_FACE_URL
        api_token = API_TOKEN_HUGGING_FACE

        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        payload = {'inputs': [text]}  
        response = requests.post(huggingface_url, json=payload, headers=headers)

        response.raise_for_status()

        result = response.json()

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except requests.exceptions.HTTPError as http_err:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'HTTP error: {http_err}'})
        }
    except Exception:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }
