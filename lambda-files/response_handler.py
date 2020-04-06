from bs4 import BeautifulSoup
from exceptions import PageBuildingError

_SUCCESS_CONTENT = """
<H1>Thank you for contacting us.</H1>
<p>You can expect a response within 2-3 business days.
"""

_FAILURE_CONTENT = """
<H1>Something went wrong.</H1>
<p>We know something is not working correctly are are working to fix it.</p>
<p>Please try to send you message again tomorrow.</p>
"""

_ERROR_FORMAT = """<b class="error"></b>"""


class WebPage:
    """
    Creates a web page with the supplied template (form).
    """

    def __init__(self, template_page):
        self._soup = BeautifulSoup(template_page, 'html.parser')
        if self._soup.main is None:
            raise PageBuildingError('Template page is missing <main> tag')

    """
    Todo: Implement an as_json(self) method and a headers property to return
          HTML Headers along with the WebPage body.

          Of course this means refactoring the API response, as well.
    """

    def populate(self, form_data):
        """
        Repopulates page with supplied values and returns page as bytestring.

        Supplied dictionary keys should match form field 'name' attributes
        """
        for tag in self._soup.find_all(['input', 'textarea', 'checkbox', 'radio']):
            response = form_data.get(tag['name'], None)
            if response is not None:
                if tag.name == 'input':
                    tag['value'] = response
                elif tag.name == 'checkbox' or tag.name == 'radio':
                    tag['checked'] = "checked" if response else ""
                else:
                    tag.string = response

    def annotate(self, message_dict, tag_markup=None, insert_before=True):
        """
        Adds listed messages to page, immediately before the element.

        The messages are only inserted if the message key matches a an element
        'name' attribute or is 'g-recaptcha-response'. Messages are inserted
        with a default error markup tag if no markup is provided
        """
        if not message_dict:
            return

        if tag_markup is None:
            tag_markup = self.error_format

        # iterate over error messages
        for field, message in message_dict.items():
            if not message:
                continue
            elif field == 'g-recaptcha-response':
                form_element = self._soup.find('div', {'class': "g-recaptcha"})
            else:
                form_element = self._soup.find(attrs={'name': field})

            # check if field exists on web page
            if not form_element:
                continue

            # make and insert a new tag
            new_tag = self._new_tag(tag_markup)
            new_tag.string = message
            if insert_before:
                form_element.insert_before(new_tag)
            else:  # insert after
                form_element.insert_after(new_tag)

    def by_status_code(self, http_code, error_messages=None, error_format=None):
        if http_code == 200:
            self.success()
        elif http_code == 400:
            self.annotate(error_messages, error_format)
        elif http_code == 500:
            self.failure()
        else:
            raise PageBuildingError("No page defined with that status code")

    def success(self):
        """
        Replaces the contents of the <main> tag with a success message.

        Also, sets main tag id="response".
        """
        self._replace_content(self.success_message, "response")

    def failure(self):
        """
        Replaces the contents of the <main> tag with a failure message.

        Also, sets main tag id="response".
        """
        self._replace_content(self.failure_message, "response")

    def custom(self, markup, main_id=None):
        """
        Replaces the contents of the <main> tag with markup and assigns new id.
        """
        self._replace_content(markup, main_id)

    def _replace_content(self, markup, main_id=None):
        """
        Replaces contents of <main> tag with supplied markup and optional id tag.
        """
        self._soup.main.contents = self._new_tag(markup)
        if main_id is not None:
            self._soup.main['id'] = main_id

    @staticmethod
    def _new_tag(markup):
        """Generates an html tag from markup and returns it as a BeautifulSoup.

        If the markup is poorly formatted, a PageBuildingError will be raised
        """
        new_tag = BeautifulSoup(markup, 'html.parser').contents[0]
        if new_tag is None:
            raise PageBuildingError('Improper markup supplied')
        return new_tag

    @property
    def body(self):
        return self._soup.encode(formatter='minimal')

    @property
    def success_message(self):
        return _SUCCESS_CONTENT

    @property
    def failure_message(self):
        return _FAILURE_CONTENT

    @property
    def error_format(self):
        return _ERROR_FORMAT

    def __repr__(self):
        return {'body': self.body,
                'success_message': self.success_message,
                'failure_message': self.failure_message,
                'error_format': self.error_format
                }

    def __str__(self):
        return str(self._soup.prettify())
