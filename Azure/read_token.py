import boto3

def read_token_from_parameter() -> str:
    try:
        aws_client = boto3.client('ssm', region_name='us-east-1') 
        
        response = aws_client.get_parameter(
            Name='/azuredevops/apitoken',  
            WithDecryption=True 
        )
        token = response['Parameter']['Value']
        return token
    except Exception as e:

        return f"Error {e}"
        
def read_webhookurl_from_parameter() -> str:
    try:
        aws_client = boto3.client('ssm', region_name='us-east-1') 
        
        response = aws_client.get_parameter(
            Name='/discord/webhookurl',  
            WithDecryption=True 
        )
        webhookurl = response['Parameter']['Value']
        print(webhookurl)
        return webhookurl
    except Exception as e:

        return f"Error {e}"


