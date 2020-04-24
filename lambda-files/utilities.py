from os import environ
from base64 import b64decode
import json

from boto3 import resource, client
from botocore.exceptions import ClientError


def get_environ_var(key, encrypted=False):
    """
    Returns variables named in the lambda environment

    Optionally, set 'encrypted' to True to to use kms to decrypt the variable
    """
    if not encrypted:
        return environ[key]
    else:
        cipher_text_blob = b64decode(environ[key])
        return client('kms').decrypt(CiphertextBlob=cipher_text_blob)['Plaintext']


def get_file(bucket_name, file_name):
    """
    Wrapper for getting files from connected S3 service
    """
    s3 = resource('s3')
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(file_name)
    return obj.get()['Body'].read()


def send_email(subject, text_body=None, html_body=None, reply_to=None, target=None):
    """
    Wrapper for connected AWS Simple Email Service; raises EmailError on failure.
    """
    RECIPIENTS = get_environ_var("SES_TARGET").split(",")
    SENDER = get_environ_var("SES_SENDER")
    REGION = get_environ_var("SES_REGION")
    CHARSET = "UTF-8"

    if target is None:
        target = RECIPIENTS
    else:
        target = target.split(",")
        if not set(target).issubset(RECIPIENTS):
            raise ValueError('invalid email target(s)')

    body = dict()
    if text_body is not None:
        body['Text'] = {'Charset': CHARSET,
                        'Data': text_body, }
    if html_body is not None:
        body['Html'] = {'Charset': CHARSET,
                        'Data': html_body, }

    email = dict()
    email['Destination'] = {'ToAddresses': target, }
    email['Message'] = {'Body': body,
                        'Subject': {'Charset': CHARSET, 'Data': subject, }, }
    email['Source'] = SENDER
    if reply_to is not None:
        email['ReplyToAddresses'] = reply_to,

    try:
        response = client('ses', region_name=REGION).send_email(**email)
    except ClientError as e:
        raise EmailClientError(e)
    else:
        return response['MessageId']


def write_item(**kwargs):
    with open('file.txt', 'a') as file:
        file.write(json.dumps(kwargs)+'\n')


def read_all_items():
    table = []
    with open('file.txt', 'r') as file:
        for line in file:
            table.append(json.loads(line))
    return table


def erase_all_items():
    open('file.txt', 'w').close()


def create_record(**kwargs):
    pass  # todo


def update_record(**kwargs):
    pass  # todo


def delete_record(**kwargs):
    pass  # todo


def read_record(**kwargs):
    pass  # todo


def find_record(**kwargs):
    return kwargs  # todo


def send_to_queue(s):
    QUEUE_URL = "none"

    try:
        # sqs = boto3.resource('sqs')
        # queue = sqs.get_queue_by_name(QueueName='test')
        # response = queue.send_message(MessageBody=s)
        return client('sqs').send_message(QueueURL=QUEUE_URL,
                                          MessageBody=s)['MessageId']
    except ClientError as e:
        raise QueueClientError(e)


class EmailClientError(ClientError):
    """
    Indicates a problem with supplied data
    """
    def __init__(self, arg):
        self.args = arg


class QueueClientError(ClientError):
    """
    Indicates a problem with supplied data
    """

    def __init__(self, arg):
        self.args = arg
