import logging

from response_handler import WebPage
from event_handler import FormData
from utilities import *
from exceptions import *

REQUIRED_FIELDS = ['name', 'email', 'message']
FIELD_COUNT = 7

S3_BUCKET = get_environ_var("S3_BUCKET")
S3_KEY = get_environ_var("S3_KEY")
TEMPLATE_PAGE = get_S3_file(S3_BUCKET, S3_KEY).read()


def lambda_handler(event, context):
    """
    The driver function that triggers on API call
    """
    # set up logging facility to record messages
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    user_input = FormData(REQUIRED_FIELDS)
    response_page = WebPage(TEMPLATE_PAGE)

    try:
        # process and validate user input and captcha
        # may raise UserError
        user_input.add_event(event, FIELD_COUNT)
        logger.debug(str(user_input))

        # if data was good, try to send the email
        # may raise ClientError
        confirmation = send_email(user_input)

        # log email transmission and return a success page
        logger.info('email sent: ' + confirmation)
        return response_page.success()

    except FormInputError as e:
        # user supplied invalid input
        logger.debug(e)
        logger.debug(user_input.error_messages)
        # refill submitted form data and return the an annotated page
        response_page.repopulate(user_input.data)
        return response_page.errors(user_input.error_messages)
    
    except EmailError as e:
        # email handler failed
        logger.error(e.response['Error']['Message'])
        logger.error("unsent contact attempt: " + str(user_input))
        # return a web page with a failure notification
        return response_page.failure()

    except Exception as e:
        # all other (unknown) errors
        logger.error('server error on: ' + user_input.last_post)
        logger.error(e)
        # return a web page with a failure notification
        return response_page.failure()


def send_email(user_input):
    """
    Gets email content and formats it before sending.
    """
    subject = 'Website contact from {}'.format(
        user_input.data["name"])

    text_body = '{}'.format(
        user_input.get('message'))

    html_body = '<p>{}</p>'.format(
        user_input.get('message'))

    reply_to = user_input.get('email')

    confirmation = send_SES_email(
        subject, text_body, html_body, reply_to)

    return confirmation
