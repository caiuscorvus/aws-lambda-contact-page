import logging

from event_handler import FormData
from response_handler import WebPage
from utilities import *
from exceptions import *

REQUIRED_FIELDS = ['name', 'email', 'message']
FIELD_COUNT = 7

FORM_PAGE = get_S3_file(
    get_environ_var("S3_BUCKET"),
    get_environ_var("S3_KEY")).read()


def lambda_handler(event, context):
    """
    The driver function that triggers on API call
    """
    # set up logging facility to record messages
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # instantiate objects
    user_input = FormData(REQUIRED_FIELDS)
    target_page = WebPage(FORM_PAGE)

    try:
        # process and validate user input and captcha
        # may raise UserError
        user_input.add_event(event, FIELD_COUNT)
        logger.debug('input passed: ' + str(user_input))

        # if data was good, try to send the email
        # may raise ClientError
        confirmation = send_email(user_input)
        logger.info('email sent: ' + confirmation)

        # configure target_page
        target_page.success()

    except InvalidInputError as e:  # user supplied invalid input
        logger.debug(e.raw_input)
        logger.debug(e.error_messages)

        target_page.populate(user_input._data)
        target_page.annotate(e.error_messages)

    except EmailError as e:  # email handler failed
        logger.error(e.response['Error']['Message'])
        logger.error("unsent contact attempt: " + str(user_input))

        target_page.failure()

    except Exception as e:  # all other (unknown) errors
        logger.error('server error on: ' + user_input._last_post)
        logger.error(e)

        target_page.failure()

    finally:
        return target_page.body


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
