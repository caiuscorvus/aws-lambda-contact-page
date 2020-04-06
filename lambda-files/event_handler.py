from urllib.request import Request, urlopen
from urllib.parse import urlencode, parse_qs
from json import load
from html import escape

from utilities import get_environ_var
from exceptions import InvalidInputError

DEFAULT_MAX = 30


class FormData:
    """
    Class to hold form data and error messages.
    """

    def __init__(self, required_fields=None):
        """
        Creates an empty form object with required fields set to empty strings.

        Attributes of this class include:
            required_fields -- fields which must have content (non-empty)
            data -- dictionary with elements accessible by obj.get("key")
            error_messages -- dictionary of keys:messages for responses and log
            last_post -- latest post element passed to add_event method
        """
        self._data = {}
        self._required_fields = required_fields
        self._input = None

    @property
    def last_input(self):
        return self._input

    @property
    def required_fields(self):
        return self._required_fields

    @property
    def default_max(self):
        return DEFAULT_MAX

    def post(self, event, max_fields=DEFAULT_MAX):
        """
        Processes, cleans, and validates new form data.

        Data must be in event['body']. Optionally, provide the expected number of
        fields to raise ValueError on loading extraneous data.
        """
        # get info from form page
        self._input = event['body']

        # convert url encoded form data into dictionary
        new_data = parse_qs(
            self._input,
            keep_blank_values=True,
            strict_parsing=False,
            encoding='utf-8',
            errors='replace',
            max_num_fields=max_fields)

        # collapse the dictionary, strip whitespace, and escape html characters
        clean_data = ({k: escape(v[0].strip()) for k, v in new_data.items()})

        self._validate(clean_data)
        self._data = clean_data

    def get(self, key=None):
        """
        Returns values from form data by key or None if not found

        Omitting 'key' returns a copy of the entire data dictionary
        """
        if key:
            return self._data.get(key, None)
        else:
            return self._data.copy()

    def _validate(self, new_data):
        """
        Raises errors on invalid data
        """
        # Notice: the captcha check is only called if there are no missing values
        self._check_for_missing_values(new_data)
        self._check_captcha_result(new_data)

    def _check_for_missing_values(self, new_data):
        """
        Raises InvalidInputError if any values from required_values are None or empty
        """
        if not self._required_fields:
            return

        new_errors = {k: "This field is required"
                      for k in self._required_fields if not new_data.get(k, None)}
        if new_errors:
            raise InvalidInputError(message="Missing values in required fields",
                                    last_input=self._input,
                                    error_messages=new_errors)

    def _check_captcha_result(self, new_data):
        """
        Checks submitted captcha value against google api and raises exceptions
        """
        CAPTCHA_SECRET = get_environ_var("CAPTCHA_SECRET", encrypted=True)
        CAPTCHA_API = get_environ_var("CAPTCHA_API")

        client_response = new_data.get('g-recaptcha_response', None)

        # call google api if there is a g-recaptcha_response value in form
        if client_response:
            post_fields = {'secret': CAPTCHA_SECRET,
                           'response': client_response}
            request = Request(CAPTCHA_API, urlencode(post_fields).encode())
            google_response = load(urlopen(request))
        # otherwise, raise InvalidInputError
        else:
            raise InvalidInputError(message="Client captcha error",
                                    last_input=self._input,
                                    error_messages={'g-recaptcha-response': "Please complete the captcha"})

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
                raise InvalidInputError(message="Client captcha error",
                                        last_input=self._input,
                                        error_messages={'g-recaptcha-response': "There was a problem with the "
                                                                                "captcha. Please try again."})
            # otherwise raise ValueError
            else:
                raise ValueError(f"Captcha errors {google_response!s}")

    def __repr__(self):
        return {'data': self._data,
                'last_input': self.last_input,
                'required_fields': self.required_fields,
                'default_max': self.default_max}

    def __str__(self):
        return str(self._data)
