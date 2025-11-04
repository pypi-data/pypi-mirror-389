import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

class UtilityAWS:
    def __init__(self, region='us-east-1'):
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.sqs = boto3.client('sqs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)

    # S3 Methods
    def upload_file_to_s3(self, bucket_name, local_path, remote_key):
        try:
            self.s3.upload_file(local_path, bucket_name, remote_key)
            print(f"Uploaded {local_path} to S3 as {remote_key}")
            return True
        except ClientError as e:
            print(f"S3 upload error: {e}")
            return False

    def download_file_from_s3(self, bucket_name, remote_key, local_path):
        try:
            self.s3.download_file(bucket_name, remote_key, local_path)
            print(f"Downloaded {remote_key} from S3 to {local_path}")
            return True
        except ClientError as e:
            print(f"S3 download error: {e}")
            return False

    def list_s3_files(self, bucket_name, prefix=''):
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            print(f"S3 list error: {e}")
            return []

    # DynamoDB Methods
    def add_utility_record(self, table_name, utility_id, utility_type, usage, date, notes=''):
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item={
                'utility_id': str(utility_id),
                'type': utility_type,
                'usage': usage,
                'date': date,
                'notes': notes
            })
            print(f"Added record {utility_id} to {table_name}")
            return True
        except ClientError as e:
            print(f"DynamoDB add error: {e}")
            return False

    def get_utility_record(self, table_name, utility_id):
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key={'utility_id': str(utility_id)})
            return response.get('Item', None)
        except ClientError as e:
            print(f"DynamoDB get error: {e}")
            return None

    def delete_utility_record(self, table_name, utility_id):
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key={'utility_id': str(utility_id)})
            print(f"Deleted record {utility_id} from {table_name}")
            return True
        except ClientError as e:
            print(f"DynamoDB delete error: {e}")
            return False

    # SQS Methods
    def send_sqs_message(self, queue_name, message_body):
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            self.sqs.send_message(QueueUrl=queue_url, MessageBody=message_body)
            print(f"Sent message to {queue_name}")
            return True
        except ClientError as e:
            print(f"SQS send error: {e}")
            return False

    def receive_sqs_messages(self, queue_name, max_messages=1):
        try:
            response = self.sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            response = self.sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=5
            )
            return response.get('Messages', [])
        except ClientError as e:
            print(f"SQS receive error: {e}")
            return []

    # SNS Methods
    def publish_sns_notification(self, topic_arn, message, subject='Notification'):
        try:
            self.sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
            print(f"Notification sent: {subject}")
            return True
        except ClientError as e:
            print(f"SNS publish error: {e}")
            return False

if __name__ == '__main__':
    aws = UtilityAWS(region='us-east-1')
    print("S3 files:", aws.list_s3_files('utility-management-files-2025', 'uploads/'))
    success = aws.add_utility_record('UtilityRecords2025', 999, 'electricity', Decimal('250.5'), '2025-11-02', 'Test')
    print("Record added:", success)
    success = aws.send_sqs_message('utility-tasks-queue-2025', 'Test message')
    print("Message sent:", success)
    success = aws.publish_sns_notification('arn:aws:sns:us-east-1:263072075949:utility-alerts-topic-2025', 'Test notification', 'Test Subject')
    print("Notification sent:", success)
