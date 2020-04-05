from urllib.request import Request, urlopen
from urllib.parse import urlencode, parse_qs
from json import load
from html import escape

from utilities import get_environ_var
from exceptions import *

DEFAULT_MAX = 30


class FormData:
    """
    Class to hold form data and error messages.
    """

    def __init__(self, required_fields=[]):
        """
        Creates an empty form object with required fields set to empty strings.

        Attributes of this class include:
            required_fields -- fields which must have content (non-empty)
            data -- dictionary with elements accessible by obj.get("key")
            error_messages -- dictionary of keys:messages for responses and log
            last_post -- latest post element passed to add_event method
        """
        self.required_fields = required_fields
        self.data = {k: "" for k in self.required_fields}
        self.error_messages = {}
        self.last_post = None

    def add_event(self, event, max_fields=DEFAULT_MAX):
        """
        Processes, cleans, and validates new form data

        Ths supplied event must be a a dictionary with data urlencoded in
        event['body']. Optionally, provided the expected number of fields
        to prevent loading extraneous data.
        """
        # reset error message list
        self.error_messages = {}

        # get info from form page
        self.last_post = event['body']

        # convert url encoded form data into dictionary
        new_data = parse_qs(
            self.last_post,
            keep_blank_values=True,
            strict_parsing=False,
            encoding='utf-8',
            errors='replace',
            max_num_fields=max_fields)

        # collapse the dictionary, strip whitespace, and escape html characters
        self.data = ({k: escape(v[0].strip()) for k, v in new_data.items()})

        # Notice: the captcha check is only called if there are no missing values
        self.find_missing_values()
        self.check_captcha_result()

        return self

    def get(self, key):
        """
        Returns values from form data
        """
        return self.data[key]

    def find_missing_values(self):
        """
        Raises ClientError if any values from required_values are None or empty
        """
        new_errors = {k: "This field is required"
                      for k in self.required_fields if not self.data.get(k)}
        if new_errors:
            self.error_messages.update(new_errors)
            raise FormInputError("Missing values in required fields in " + self.last_post)

        return None

    def check_captcha_result(self):
        """
        Checks submitted captcha value against google api and raises exceptions
        """
        CAPTCHA_SECRET = get_environ_var("CAPTCHA_SECRET", encrypted=True)
        CAPTCHA_API = get_environ_var("CAPTCHA_API")

        post_fields = {'secret': CAPTCHA_SECRET,
                       'response': self.data['g-recaptcha_response']}

        request = Request(CAPTCHA_API, urlencode(post_fields).encode())
        response = load(urlopen(request))

        if not response.get('success', False):
            """
            Google api errors

            missing-input-secret 	The secret parameter is missing.
            invalid-input-secret 	The secret parameter is invalid or malformed.
            missing-input-response 	The response parameter is missing.
            invalid-input-response 	The response parameter is invalid or malformed.
            bad-request 	        The request is invalid or malformed.
            timeout-or-duplicate 	The response is no longer valid: either is too old or has been used previously.
            """
            error_codes = response.get('error-codes')

            possible_server_errors = {'missing-input-response': "captcha returned missing-input-response",
                                      'invalid-input-response': "captcha returned invalid-input-response",
                                      'bad-request': "captcha returned bad-request"}

            server_errors = {k: possible_server_errors[k] for k in error_codes}
            if server_errors:
                self.error_messages.update(server_errors)
                raise ValueError("Captcha error on " + self.get_last())

            possible_client_errors = {'missing-input-secret': "The captcha response was incorrect",
                                      'invalid-input-secret': "The captcha response was incorrect",
                                      'timeout-or-duplicate': "Recaptcha has timed out--please try again"}

            client_errors = {k: possible_client_errors[k] for k in error_codes}
            if not client_errors:
                client_errors = {'g-recaptcha-response': "The captcha was incorrect"}

            raise FormInputError("Captcha error on " + self.get_last())
        else:
            return None

    def __repr__(self):
        return {'data': self.data,
                'last_post': self.last_post,
                'error_messages': self.error_messages,
                'required_fields': self.required_fields,
                'default_max': DEFAULT_MAX
                }

    def __str__(self):
        return str(self.data)
