from boto3 import client
from botocore.exceptions import ClientError

from utilities import get_environ_var


class EmailError(ClientError):
    def __init__(self, arg):
        self.args = arg


class email


def send_ses_email(form_data):
    SES_REGION = get_environ_var("SES_REGION")
    
    params = text_email_params(form_data)
    
    try:
        response = client('ses', region_name=SES_REGION).send_email(params)
    except ClientError as e:
        raise EmailError(e)
        
    return response['MessageId']


def text_email_params(form_data):
    SES_TARGET = get_environ_var("SES_TARGET")
    SES_SENDER = get_environ_var("SES_SENDER")
    
    Destination = {'ToAddresses': [SES_TARGET]}
    
    Message = {'Body': {
                   'Text': {'Charset': 'UTF-8',
                            'Data': "SUBJECT: " + form_data.get("subject") 
                            + "\r\n\r\n"
                            + form_data.get("message")
                   },
               },
               'Subject': {'Charset': 'UTF-8',
                           'Data': "Webpage contact from "
                                   + form_data.get("name")
               }
    }

    Source = SES_SENDER
    
    ReplyToAddresses = [form_data.get("email"),]

    return Destination, Message, Source, ReplyToAddresses
