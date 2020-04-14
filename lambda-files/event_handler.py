from urllib.request import Request, urlopen
from urllib.parse import urlencode, parse_qs
from json import load
from html import escape
from datetime import datetime

from utilities import get_environ_var
from exceptions import InvalidInputError, SpamError

DEFAULT_MAX = 30


class FormData:
    """
    Class to hold form data and error messages.
    """

    def __init__(self, required=None, honey=None, captcha=True):
        """
        Creates an empty form object with required fields set to empty strings.

        Attributes of this class include:
            required_fields -- fields which must have content (non-empty)
            data -- dictionary with elements accessible by obj.get("key")
            error_messages -- dictionary of keys:messages for responses and log
            last_post -- latest post element passed to add_event method
        """
        self._body = {}
        self._headers = {}
        self._input = None
        self._time = None

        self._required_fields = required
        self._honey_pots = honey
        self._check_captcha = captcha

        self.state = "empty"

    @property
    def last_input(self):
        return self._input

    @property
    def time(self):
        return self._time

    @property
    def required_fields(self):
        return self._required_fields

    @required_fields.setter
    def required_fields(self, required):
        self._required_fields = required
        if self._body and self.required_fields:
            self._check_for_missing_values()

    @property
    def honey_pots(self):
        return self._honey_pots

    @honey_pots.setter
    def honey_pots(self, honey):
        self._honey_pots = honey
        if self._body and self.honey_pots:
            self._check_honey_pots()

    @property
    def check_captcha(self):
        return self._check_captcha

    @check_captcha.setter
    def check_captcha(self, captcha):
        self._check_captcha = captcha
        if self._body and self.check_captcha:
            self._check_captcha()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, s):
        self._state = s

    @property
    def default_max(self):
        return DEFAULT_MAX

    def read_event(self, event, max_fields=DEFAULT_MAX):
        """
        Processes, cleans, and validates new form data.

        Data must be in event['body']. Optionally, provide the expected number of
        fields to raise ValueError on loading extraneous data.
        """
        # get info from form page
        self._input = event['body']
        self._time = datetime.now().isoformat(sep=' ')
        self.state = "post"

        # convert url encoded form data into dictionary
        new_data = parse_qs(
            self._input,
            keep_blank_values=True,
            strict_parsing=False,
            encoding='utf-8',
            errors='replace',
            max_num_fields=max_fields)

        # collapse the dictionary, strip whitespace, and escape html characters
        self._body = ({k: escape(v[0].strip()) for k, v in new_data.items()})

        # run validation checks
        self.validate()

    def get(self, key=None):
        """
        Returns values from form data by key or None if not found

        Omitting 'key' returns a copy of the entire data dictionary
        """
        if key:
            return self._headers.get(key, self._body.get(key, None))
        else:
            copy = {}
            copy.update(self._body)
            copy.update(self._headers)
            return copy

    def validate(self):
        """
        Raises errors on invalid data
        """
        # Notice: each check raises an error on failure, so call in desired order
        if self.honey_pots:
            self._check_honey_pots()
        if self.required_fields:
            self._check_for_missing_values()
        if self.check_captcha:
            self._check_captcha_result()

        self.state = "valid"

    def _check_honey_pots(self):
        """
        Raises HoneyPotError if any values from required_values are None or empty
        """
        for k in self._honey_pots:
            if self.get(k):
                self.state = "spam"
                raise SpamError("Value detected in honey pot")

    def _check_for_missing_values(self):
        """
        Raises InvalidInputError if any values from required_values are None or empty
        """
        # if _required_fields is not iterable, this will throw a TypeError
        new_errors = {k: "This field is required" for k in self._required_fields if not self.get(k)}
        if new_errors:
            self.state = "invalid"
            raise InvalidInputError(
                message="Missing values in required fields",
                last_input=self._input,
                error_messages=new_errors
            )

    def _check_captcha_result(self):
        """
        Checks submitted captcha value against google api and raises exceptions
        """
        CAPTCHA_SECRET = get_environ_var("CAPTCHA_SECRET", encrypted=True)
        CAPTCHA_API = get_environ_var("CAPTCHA_API")

        client_response = self.get('g-recaptcha-response')

        # call google api if there is a g-recaptcha-response value in form
        if client_response:
            post_fields = {'secret': CAPTCHA_SECRET,
                           'response': client_response}
            request = Request(CAPTCHA_API, urlencode(post_fields).encode())
            google_response = load(urlopen(request))
        # otherwise, raise InvalidInputError
        else:
            self.state = "invalid"
            raise InvalidInputError(
                message="Client captcha error",
                last_input=self.last_input,
                error_messages={'g-recaptcha-response': "Please complete the captcha"}
            )

        # check if google passes the captcha
        if google_response.get('success', False):
            return
        # otherwise, identify the problem and raise an exception
        else:
            """
            Google api errors

            missing-input-secret 	The secret parameter is missing.
            invalid-input-secret 	The secret parameter is invalid or malformed.
            missing-input-response 	The response parameter is missing.
            invalid-input-response 	The response parameter is invalid or malformed.
            bad-request 	        The request is invalid or malformed.
            timeout-or-duplicate 	The response is no longer valid: either is too old or has been used previously.
            """
            error_codes = google_response.get('error-codes')

            client_errors = {'missing-input-response',
                             'invalid-input-response',
                             'timeout-or-duplicate'} & set(error_codes)

            server_errors = {'missing-input-secret',
                             'invalid-input-secret',
                             'bad-request'} & set(error_codes)

            # if problems were solely in client response, raise InvalidInputError
            if client_errors and not server_errors:
                self.state = "invalid"
                raise InvalidInputError(
                    message="Client captcha error",
                    last_input=self.last_input,
                    error_messages={'g-recaptcha-response': f"Captcha errors {google_response!s}"}
                )
            # error_messages={'g-recaptcha-response': "There was a problem with the captcha. Please try again."}
            # otherwise raise ValueError
            else:
                self.state = "error"
                raise ValueError(f"Captcha errors {google_response!s}")

    def __repr__(self):
        return {'data': self._body,
                'last_input': self.last_input,
                'required_fields': self.required_fields,
                'default_max': self.default_max}

    def __str__(self):
        return str(self._body)
