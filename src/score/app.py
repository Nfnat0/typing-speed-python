import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])
ALLOWED_ORIGIN = os.environ['ALLOWED_ORIGIN']


def lambda_handler(event, context):
    headers = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type,X-CSRF-TOKEN",
        "Access-Control-Allow-Methods": "PUT, OPTIONS",
    }

    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({})
        }

    body = json.loads(event['body'])
    user_id = body.get('userId')
    high_score = body.get('highScore')
    # not used but included for completeness

    if not user_id or high_score is None:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'message': 'Missing parameters'})
        }

    try:
        response = table.get_item(Key={'UserID': user_id})
        user_record = response.get('Item')

        new_high_score = high_score

        if user_record:
            existing_high_score = user_record.get('HighScore', 0)
            if high_score > existing_high_score:
                table.put_item(Item={
                    'UserID': user_id,
                    'HighScore': new_high_score,
                })

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'UserID': user_id,
                'HighScore': new_high_score,
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': 'Internal Server Error',
                'error': str(e)
            })
        }
