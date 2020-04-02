import logging

from html import escape
from urllib.parse import parse_qs

import basic_validator as validator
from basic_validator import UserError

import ses_email as emailer
from ses_email import EmailError

import page_builder


MAX_FIELD_COUNT = 7


def validate(form_data):
    # this function must return None or raise UserError
    # UserError must pass dictionary of error messages
    return validator.basic_validation(form_data)
    
    
def email(form_data):
    # this function must return a confirmation or raise EmailError
    return emailer.send_ses_email(form_data)


def lambda_handler(event, context):
    # set up logging facility to record messages
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # collect and clean form data
    form_data = get_form_data(event)
    
    logger.debug("user submission: " + str(form_data))

    try:
        # validate user input and captcha
        # may raise UserError
        validate(form_data)

        # if data was good, try to send the email
        # may raise EmailError
        confirmation = email(form_data)
        
        # log email transmission and load success page
        logger.info('email sent: ' + confirmation)
        return page_builder.success_page()

    except UserError as e:
        # user supplied invalid input
        logger.debug('invalid input on: ' + str(form_data))
        logger.debug(e)
        return page_builder.error_page(form_data, e)
    
    except EmailError as e:
        # email handler failed
        logger.error(e.response['Error']['Message'])
        logger.error("unsent contact attempt: " + str(form_data))
        return page_builder.failure_page()

    except Exception as e:
        # all other (unknown) errors
        logger.error('server error on: ' + str(form_data))
        logger.error(e)
        return page_builder.failure_page()


def get_form_data(event):
    # get info from form page
    form_data_url_encoded = event['body']

    # convert url encoded form data into dictionary
    form_data = parse_qs(
        form_data_url_encoded,
        keep_blank_values=True,
        strict_parsing=False,
        encoding='utf-8',
        errors='replace',
        max_num_fields=MAX_FIELD_COUNT)
        
    # collapse the dictionary, strip whitespace, and escape html characters
    return {k: escape(v[0].strip()) for k, v in form_data.items()}
