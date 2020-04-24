import form_reader
import contact_page
import utilities

import logging
from html import escape
from urllib.parse import parse_qs


def api_handler(event, context):
    """
    The driver function that triggers on API call
    """
    logger = None
    form_data = None
    target_page = None

    try:  # wrap everything in a try to make sure we return something
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        template_file = utilities.get_file(
            utilities.get_environ_var("S3_BUCKET"),
            utilities.get_environ_var("FORM_NAME"))
        target_page = contact_page.ContactPage(template_file)

        form_data = get_form_data(event)

        fmt = "Passed request {request_id} sent to queue: {message_id}"

        try:
            form_data.check_honey_pots('')
            # form_data.check_captcha()
            form_data.check_for_missing_values('name,email,message')
            form_data.check_email_address('email')
            target_page.sent_notice()
        except form_reader.SpamError as e:  # user input is probably spam
            logger.debug(e)
            target_page.failure_notice()
            fmt = "Spam request {request_id} sent to queue: {message_id}"

        except form_reader.InvalidInputError as e:  # user input failed validation
            logger.debug(e)
            target_page.populate(form_data.body)
            target_page.annotate(e.errors)
            fmt = "Invalid request {request_id} sent to queue: {message_id}"

        finally:
            js = form_data.json_string()
            message_id = utilities.send_to_queue(js)
            logger.info(fmt.format(request_id=form_data.uid,
                                   message_id=message_id))

    except Exception as be:
        logger.error(f"error on: {event!s}")
        logger.error(be)
        try:
            form_data.state = 'ERROR'
        except Exception as e:
            logger.error(e)
        try:
            target_page.failure_notice()
        except Exception as e:
            target_page = contact_page.ContactPage.PANIC_PAGE
            logger.error(e)

    finally:
        return target_page.body


def get_form_data(event):
    # convert url encoded form data into dictionary
    body = parse_qs(
        event['body'],
        keep_blank_values=True,
        strict_parsing=False,
        encoding='utf-8',
        errors='replace',
        max_num_fields=7)

    for key, value in body.items():
        # collapse the dictionary, strip whitespace, and escape html characters
        body[key] = escape(value[0].strip())

    return form_reader.FormData(state='POSTED',
                                headers=None,
                                body=body)
