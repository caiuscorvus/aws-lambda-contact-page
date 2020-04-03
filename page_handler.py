from bs4 import BeautifulSoup

SUCCESS_CONTENT = """
<main id='response'>
<H1>Thank you for contacting us.</H1>
<p>You can expect a response within 2-3 business days.
</main>"""

FAILURE_CONTENT = """
<main id='response'>
<H1>Something went wrong.</H1>
<p>We know something is not working correctly are are working to fix it.</p>
<p>Please try to send you message again tomorrow.</p>
</main>"""

ERROR_MARKUP = """<b class="error"></b>"""


def __new_tag(markup):
    """Generates an html tag from markup and returns it as a BeautifulSoup."""
    return BeautifulSoup(markup, 'html.parser')


class WebPage:
    """
    Creates a web page with the supplied template (form).
    """

    def __init__(self, template_page):
        self.soup = BeautifulSoup(template_page, 'html.parser')

    def as_is(self):
        """
        Returns the current page as a bytestring.
        """
        return self.soup.encode(formatter="minimal")

    def repopulate(self, form_data):
        """
        Repopulates page with supplied values and returns page as bytestring.

        Supplied dictionary keys should match form field 'name' attributes
        """
        # iterate over form data
        for field, response in form_data.items():
            # find submitted element on form page
            form_element = self.soup.find(
                ["input", "textarea", "checkbox", "radio"],
                {"name": field})

            # if the form element exists on the page and there is data to fill
            if form_element and len(response) > 0:
                if form_element.type == "input":
                    form_element['value'] = response
                elif form_element.type == "textarea":
                    form_element.string = response
                elif form_element.type == "checkbox" or type == "radio":
                    form_element['checked'] = "checked"

        return self.soup.encode(formatter="minimal")

    def errors(self, error_data, markup=ERROR_MARKUP):
        """
        Adds listed error messages to page and returns page as bytestring.

        The messages are only inserted if the error key matches a form element
        'name' attribute or is 'g-recaptcha-response'. Messages are inserted
        with a default error markup tag if no markup is provided
        """
        # iterate over error messages
        for field, error_message in error_data.items():
            # find submitted element on form page
            if field == "g-recaptcha-response":
                form_element = self.soup.find("div", {"class": "g-recaptcha"})
            else:
                form_element = self.soup.find(field)

            if form_element is None:
                # this field does not exist
                break

            error_tag = __new_tag(markup)

            if error_tag is None:
                raise ValueError("Improper error markup")

            error_tag.string = error_message
            form_element.insert_before(error_tag)

        return self.soup.encode(formatter="minimal")

    def success(self):
        """
        Creates a web page with a success message and returns it as a bytestring.

        The message replaces the <main id='content'> tag and contents. If no
        such tag exists, then this function silently returns the supplied
        (template) page with no change
        """
        return __replace_content(SUCCESS_CONTENT)

    def failure(self):
        """
        Creates a web page with a failure message and returns it as a bytestring.

        The message replaces the <main id='content'> tag and contents. If no
        such tag exists, then this function silently returns the supplied
        (template) page with no change
        """
        return __replace_content(FAILURE_CONTENT)

    def custom(self, markup):
        """
        Creates a web page with the supplied markup and returns it as a bytestring.

        The markup replaces the <main id='content'> tag and contents. If no
        such tag exists, then this function silently returns the supplied
        (template) page with no change
        """
        return __replace_content(markup)

    def __replace_content(self, markup):
        """
        Replaces <main id='content'> tag with markup.

        The markup replaces the <main id='content'> tag and contents. If no
        such tag exists, then this function silently returns the supplied
        (template) page with no change
        """
        new_content = __new_tag(markup)
        content_tag = self.soup.find(["main"], {"id": "content"})

        if content_tag is not None:
            content_tag.replace_with(new_content)

        return self.soup.encode(formatter="minimal")

    def __repr__(self):
        return {'page': self.soup.encode(formatter="minimal"),
                'success_message': SUCCESS_CONTENT,
                'error_message': FAILURE_CONTENT,
                'default_markup': ERROR_MARKUP
                }

    def __str__(self):
        return str(self.soup.prettify())
