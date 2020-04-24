import utilities

from datetime import datetime
import re
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode


class FormData:
    """
    Class to hold form data
    """
    def __init__(self, state=None, headers=None, body=None, comments=''):
        # create a 'unique' id for each record
        # (with really low throughput I'm using date time to the micro second)
        # alternatively, could use python's UUID functions
        self.uid = datetime.now().isoformat(sep=' ')
        self.state = state
        self.headers = headers
        self.body = body
        self.comments = comments

    def check_honey_pots(self, honey_pots):
        """
        Raises SpamError if any values from required_values are None or empty
        """
        honey_pots = map(str.strip, honey_pots.split(','))
        new_errors = {}

        for k, v in {k: self.body.get(k, None) for k in honey_pots}.items():
            if v:
                new_errors.update(
                    {f"Honey pot field: {k}": f"Honey pot value: {v}"}
                )
        if new_errors:
            self.state = 'SPAM'
            raise SpamError(errors=new_errors)

    def check_for_missing_values(self, required_fields):
        """
        Raises InvalidInputError if any values from required_values are None or empty
        """
        required_fields = map(str.strip, required_fields.split(','))
        new_errors = {k: "This field is required" for k in required_fields if not self.body.get(k, None)}
        if new_errors:
            self.state = 'INVALID'
            raise InvalidInputError(new_errors)

    def check_email_address(self, email_field):
        """
        Raises InvalidInputError if email address is not correctly formatted
        """
        pattern = re.compile(r"[^\s]+@[^@\s]+\.[a-zA-Z][a-zA-Z0-9]?[a-zA-Z]$")
        if re.fullmatch(pattern, self.body.get(email_field, '')) is None:
            self.state = 'INVALID'
            raise InvalidInputError({email_field: "The e-mail address seems to be incorrect"})

    def check_email_server(self, email_field):
        """
        Raises InvalidInputError if email servers don't exist
        """
        pass  # todo

    def check_captcha_result(self):
        """
        Sends captcha value to google api and raises FormDataError or InvalidInputError on failure
        """
        CAPTCHA_SECRET = utilities.get_environ_var("CAPTCHA_SECRET", encrypted=True)
        CAPTCHA_API = utilities.get_environ_var("CAPTCHA_API")

        client_response = self.body.get('g-recaptcha-response', None)

        # call google api if there is a g-recaptcha-response value in form
        if client_response:
            post_fields = {'secret': CAPTCHA_SECRET,
                           'response': client_response}
            request = Request(CAPTCHA_API, urlencode(post_fields).encode())
            google_response = json.load(urlopen(request))
        # otherwise, raise InvalidInputError
        else:
            self.state = 'INVALID'
            raise InvalidInputError({'g-recaptcha-response': "Please complete the captcha"})

        # check if google passes the captcha
        if google_response.get('success', False):
            return
        # otherwise, identify the problem and raise an exception
        else:
            error_codes = google_response.get('error-codes')
            """
            missing-input-secret   -- The secret parameter is missing. \n
            invalid-input-secret   -- The secret parameter is invalid or malformed.\n
            bad-request            -- The request is invalid or malformed.\n
            missing-input-response -- The response parameter is missing.\n
            invalid-input-response -- The response parameter is invalid or malformed.\n
            timeout-or-duplicate   -- The response is no longer valid: either is too old or has been used previously.
            """

            client_errors = {'missing-input-response',
                             'invalid-input-response',
                             'timeout-or-duplicate'} & set(error_codes)

            server_errors = {'missing-input-secret',
                             'invalid-input-secret',
                             'bad-request'} & set(error_codes)

            # if problems were solely in client response, raise InvalidInputError
            if client_errors and not server_errors:
                self.state = 'INVALID'
                raise InvalidInputError({'g-recaptcha-response': f"Captcha errors {google_response!s}"})
            # error_messages={'g-recaptcha-response': "There was a problem with the captcha. Please try again."}
            # otherwise raise ValueError
            else:
                self.state = 'ERROR'
                raise FormDataError(google_response)

    def json_string(self):
        return json.dumps({'uid': self.uid,
                           'state': self.state,
                           'headers': self.headers,
                           'body': self.body,
                           'comments': self.comments})

    @classmethod
    def create_from_json(cls, json_string):
        form_data = cls.__new__(cls)
        super(FormData, form_data).__init__()

        data = json.loads(json_string)

        form_data.uid = data['uid']
        form_data.state = data['state']
        form_data.headers = data['headers']
        form_data.body = data['body']
        form_data.comments = data['comments']

        return form_data

    def add_to_db(self):
        utilities.create_record(uid=self.uid,
                                state=self.state,
                                headers=self.headers,
                                comments=self.comments)

    @classmethod
    def read_from_db(cls, uid):
        form_data = cls.__new__(cls)
        super(FormData, form_data).__init__()

        record = utilities.read_record(uid=uid)

        form_data._event = None
        form_data.uid = record['uid']
        form_data.state = record['state']
        form_data.headers = record['headers']
        form_data.body = record['body']
        form_data.comments = record['comments']

        return form_data

    def update_in_db(self):
        utilities. update_record(uid=self.uid,
                                 state=self.state,
                                 headers=self.headers,
                                 body=self.body,
                                 comments=self.comments)

    def delete_from_db(self):
        utilities.delete_record(uid=self.uid)

    def is_in_db(self):
        return False


class FormDataError(ValueError):
    """
    The base exception class for FormData exceptions.
    """
    fmt = 'An unspecified error occurred: {errors}'

    def __init__(self, errors):
        message = self.fmt.format(errors=errors)
        Exception.__init__(self, message)
        self.errors = errors


class InvalidInputError(FormDataError):
    """
    Indicates that validation detected an error with user input
    """
    fmt = 'User input failed validation: {errors}'


class SpamError(FormDataError):
    """
    Indicates that validation detected probable spam
    """
    fmt = 'Probable spam submission: {data_path}'
