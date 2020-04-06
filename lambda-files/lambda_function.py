import logging

from event_handler import FormData
from response_handler import WebPage
from utilities import *
from exceptions import *

REQUIRED_FIELDS = ['name', 'email', 'message']
FIELD_COUNT = 7

FORM_PAGE = get_S3_file(get_environ_var("S3_BUCKET"),
                        get_environ_var("S3_KEY"))


def lambda_handler(event, context):
    """
    The driver function that triggers on API call
    """
    # set up logging facility to record messages
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # instantiate objects
    form_data = FormData(REQUIRED_FIELDS)
    target_page = WebPage(FORM_PAGE)

    try:
        # process and validate user input and captcha
        # may raise InvalidInputError
        form_data.post(event, FIELD_COUNT)
        logger.debug(f'input passed: {form_data.last_input!s}')

        # if data was good, try to send the email
        # may raise EmailError
        confirmation = send_SES_email(
            subject=f"Website contact from {form_data.get('name')}",
            text_body=form_data.get('message'),
            html_body=f"<p>{form_data.get('message')}</p",
            reply_to=form_data.get('email')
        )
        logger.info(f'email sent: {confirmation}')

        # configure target_page
        target_page.success()

    except InvalidInputError as e:  # user supplied invalid input
        logger.debug(f"{e.message}: {e.last_input!s}")

        target_page.populate(form_data.get())
        target_page.annotate(e.error_messages)

    except EmailError as e:  # email utility failed
        logger.error(e.response['Error']['Message'])
        logger.error(f"unsent contact attempt: {form_data!s}")

        target_page.failure()

    except Exception as e:  # all other (unknown) errors
        logger.error(f"error on: {event!s}")
        logger.error(e)

        target_page.failure()

    finally:
        return target_page.body
