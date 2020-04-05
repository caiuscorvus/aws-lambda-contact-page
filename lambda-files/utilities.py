from os import environ
from base64 import b64decode
from boto3 import resource, client

from exceptions import *

# gets environmental variables
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


# pulls html file from the s3 bucket
def get_S3_file(bucket_name, file_name):
    """
    Wrapper for getting html files from connected S3 service
    """
    s3 = resource('s3')
    bucket = s3.Bucket(bucket_name)
    obj = bucket.Object(file_name)
    return obj.get()['Body']


def send_SES_email(subject, text_body, html_body, reply_to=""):
    """
    Wrapper for connected AWS Simple Email Service; raises EmailError on failure.
    """
    RECIPIENT = get_environ_var("SES_TARGET")
    SENDER = get_environ_var("SES_SENDER")
    REGION = get_environ_var("SES_REGION")
    CHARSET = "UTF-8"

    body = {}

    if text_body is not None:
        body.update({'Text': {
            'Charset': CHARSET,
            'Data': text_body,
        }})
    if html_body is not None:
        body.update({'Html': {
            'Charset': CHARSET,
            'Data': html_body,
        }})

    client_ = client('ses', region_name=REGION)

    try:
        response = client_.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': body,
                'Subject': {
                    'Charset': CHARSET,
                    'Data': subject,
                },
            },
            Source=SENDER,
            ReplyToAddresses=[
                reply_to,
            ],
        )
    except ClientError as e:
        raise EmailError(e)
    else:
        return response['MessageId']


def send_SES_text_email(subject, text_body, reply_to=""):
    """See: send_SES_email."""
    return send_SES_email(subject, text_body, None, reply_to)


def send_SES_html_email(subject, html_body, reply_to=""):
    """See: send_SES_email."""
    return send_SES_email(subject, None, html_body, reply_to)