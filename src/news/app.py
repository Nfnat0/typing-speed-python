import json
import requests
import boto3
import os
import pytz
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_ORIGIN = os.environ['ALLOWED_ORIGIN']
TIME_ZONE = os.environ['TIME_ZONE']


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type,X-CSRF-TOKEN",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
    }

    news_api_url = "https://newsapi.org/v2/top-headlines"
    ssm = boto3.client('ssm')

    parameter_name = os.environ['PARAMETER_NAME']
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    api_key = response['Parameter']['Value']

    genres = ["business", "science", "technology",
              "general", "entertainment", "health"]
    logger.info(f"Fetching news for genres: {genres}")

    s3_bucket_name = os.environ['S3_BUCKET_NAME']
    s3 = boto3.client('s3')

    for genre in genres:
        params = {
            'country': 'us',
            'category': genre,
            'apiKey': api_key
        }

        logger.info(f"Fetching news for genre: {genre}")
        response = requests.get(news_api_url, params=params)
        news_data = response.json()

        if response.status_code != 200:
            logger.error(f"Failed to fetch news for genre {genre}: {
                         response.status_code} {news_data}")
            continue

        # Retrieve and filter the titles of the latest news
        titles = [
            article['title'].split(' - ')[0] for article in news_data['articles']
            if '[Removed]' not in article['title']
        ]

        if not titles:
            logger.info(f"No valid news titles found for genre {genre}")
            continue

        file_content = "\n".join(titles)

        # Get the current time for the file name
        tz = pytz.timezone(TIME_ZONE)
        execution_time = datetime.now(tz).strftime('%Y/%m/%d')

        # Define the file name
        file_name = f"{execution_time}/{genre}.txt"

        # Save the file to S3
        try:
            logger.info(f"Saving news for genre {genre} to S3 bucket {
                        s3_bucket_name} with file name {file_name}")
            s3.put_object(
                Bucket=s3_bucket_name,
                Key=file_name,
                Body=file_content.encode('utf-8')
            )
            logger.info(f"Successfully saved news for genre {
                        genre} to {file_name}")
        except Exception as e:
            logger.error(f"Error saving news for genre {
                         genre} to S3: {str(e)}")

    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps('News files saved to S3 successfully')
    }
