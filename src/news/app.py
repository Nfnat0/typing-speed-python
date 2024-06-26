import json
import requests
import boto3
import os
from datetime import datetime, timezone

ALLOWED_ORIGIN = os.environ['ALLOWED_ORIGIN']


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type,X-CSRF-TOKEN",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
    }
    # Define the news API endpoint and parameters
    news_api_url = "https://newsapi.org/v2/top-headlines"
    ssm = boto3.client('ssm')

    parameter_name = os.environ['PARAMETER_NAME']
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    api_key = response['Parameter']['Value']
    params = {
        'country': 'us',
        'apiKey': api_key
    }

    # Fetch the latest news
    response = requests.get(news_api_url, params=params)
    news_data = response.json()

    # Check if the request was successful
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'headers': headers,
            'body': json.dumps(news_data)
        }

    # Retrieve the titles of the latest news
    titles = [article['title'].split(' - ')[0]
              for article in news_data['articles']]

    # Create the file content
    file_content = "\n".join(titles)

    # Get the current time for the file name
    execution_time = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')

    # Define the file name
    file_name = f"latest_news_{execution_time}.txt"

    # Get the S3 bucket name from the environment variables
    s3_bucket_name = os.environ['S3_BUCKET_NAME']

    # Save the file to S3
    s3 = boto3.client('s3')
    s3.put_object(
        Bucket=s3_bucket_name,
        Key=file_name,
        Body=file_content.encode('utf-8')
    )

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps('File saved to S3 successfully')
    }
