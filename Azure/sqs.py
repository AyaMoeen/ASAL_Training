import json
import os
import boto3
from dotenv import load_dotenv # type: ignore
load_dotenv()

QUEUE_URL = os.getenv('QUEUE_URL')
sqs = boto3.client('sqs')

def send_to_sqs(command: str, data: dict, token: str, webhook:str, message_group_id: str = 'default'):
    """Send CLI command data to SQS"""
    message = {
        'token': token,
        'webhook': webhook,
        'command': command,
        'data': data
    }
    try:
        if not command:
            raise ValueError("Invalid command or data")
        
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(message),  
            MessageGroupId=message_group_id
        )
        print(f"Message sent to SQS: {response['MessageId']}")
        return response
    except Exception as e:
        print(f"Error sending message to SQS: {e}")
        return None
