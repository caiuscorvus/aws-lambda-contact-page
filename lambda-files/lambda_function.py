import logging

from event_handler import FormData
from response_handler import WebPage, ReportPage
from utilities import *
from exceptions import *


class ContactFormData(FormData):
    """
    This class extends FormData with more default values and email and database schemas
    """
    def __init__(self):
        super().__init__(required_fields=['name', 'email', 'message'],
                         honey_pots=[],
                         check_captcha=True)

    def read_event(self, event, max_fields=7):
        super().read_event(event, max_fields)

    def email(self):
        confirmation = send_SES_email(
            subject=f"Website contact from {self.get('name')}",
            text_body=self.get('message'),
            html_body=f"<p>{self.get('message')}</p",
            reply_to=self.get('email')
        )
        self.state = 'sent'
        return confirmation

    def record(self):
        return


class ContactPage(WebPage):
    """
    This class extends FormData with more default values and pages
    """
    def __init__(self):
        form_page = get_S3_file(get_environ_var("S3_BUCKET"),
                                get_environ_var("FORM_NAME"))
        super().__init__(form_page)

    def success(self):
        """
        Replaces the contents of the <main> tag with a success message.

        Also, sets main tag id="response".
        """
        markup = """<H1>Thank you for contacting us.</H1>
                    <p>You can expect a response within 2-3 business days."""
        self.custom(markup, "response")

    def failure(self):
        """
        Replaces the contents of the <main> tag with a failure message.

        Also, sets main tag id="response".
        """
        markup = """<H1>Something went wrong.</H1>
                    <p>We know something is not working correctly are are working to fix it.</p>
                    <p>Please try to send you message again tomorrow.</p>"""
        self.custom(markup, "response")

    def annotate(self, message_dict, tag_markup="""<b class="error"></b>""", insert_before=True):
        super().annotate(message_dict, tag_markup=tag_markup, insert_before=True)


def lambda_handler(event, context):
    """
    The driver function that triggers on API call
    """
    # set up logging facility to record messages
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # instantiate objects
    form_data = ContactFormData()
    target_page = ContactPage()

    try:
        # process and validate user input and captcha
        form_data.read_event(event)
        logger.debug(f'input passed: {form_data.last_input!s}')

        # check submission type (report request or standard contact email
        if form_data.get("name") == "report" and form_data.get("email") in reply_to
            # handle this as a report request
            report = ReportPage(form_data)
            form_data.record()
            email_confirmation = form_data.email()
            logger.info(f'report made: {email_confirmation}')

            target_page = report

        else:
            # handle this as an email attempt
            form_data.record()
            email_confirmation = form_data.email()
            logger.info(f'email sent: {email_confirmation}')

            target_page.success()

    except InvalidInputError as e:  # user supplied invalid input
        logger.debug(f"{e.message}: {form_data!s}")

        target_page.populate(form_data.get())
        target_page.annotate(e.error_messages)

    except Exception as e:  # all other (unknown) errors
        logger.error(f"error on: {event!s}")
        logger.error(e)

        target_page.failure()

    finally:
        return target_page.body
