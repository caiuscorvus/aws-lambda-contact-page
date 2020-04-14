from os import environ
from base64 import b64decode
from boto3 import resource, client

from exceptions import *


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


def get_S3_file(bucket_name, file_name):
    """
    Wrapper for getting files from connected S3 service
    """
    s3 = resource('s3')
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(file_name)
    return obj.get()['Body'].read()


def send_SES_email(subject, text_body=None, html_body=None, reply_to=None):
    """
    Wrapper for connected AWS Simple Email Service; raises EmailError on failure.
    """
    RECIPIENT = get_environ_var("SES_TARGET").split(",")
    SENDER = get_environ_var("SES_SENDER")
    REGION = get_environ_var("SES_REGION")
    CHARSET = "UTF-8"

    body = dict()
    if text_body is not None:
        body['Text'] = {'Charset': CHARSET,
                        'Data': text_body, }
    if html_body is not None:
        body['Html'] = {'Charset': CHARSET,
                        'Data': html_body, }

    email = dict()
    email['Destination'] = {'ToAddresses': RECIPIENT, }
    email['Message'] = {'Body': body,
                        'Subject': {'Charset': CHARSET, 'Data': subject, }, }
    email['Source'] = SENDER
    if reply_to is not None:
        email['ReplyToAddresses'] = reply_to,

    try:
        response = client('ses', region_name=REGION).send_email(**email)
    except ClientError as e:
        raise EmailError(e)
    else:
        return response['MessageId']
