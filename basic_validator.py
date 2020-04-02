from urllib.request import Request, urlopen
from urllib.parse import urlencode
from json import load

import utilities

REQUIRED_FIELDS = ["name", "email", "subject", "message",
                   "g-recaptcha-response"]
                   
OPTIONAL_FIELDS = []


class UserError(ValueError):
    def __init__(self, arg):
        self.args = arg


def basic_validation(form_data):
    error_messages = {}
    
    for f in REQUIRED_FIELDS:
        # get messages for any errors
        error_messages.update(
            validate_string(f, form_data.get(f, "")))
    
    # if the form data already has error, don't bother captcha check
    if len(error_messages) > 0:
        raise UserError(error_messages)
    
    # if the form data passes validation, check captcha
    error_messages.update(
        validate_captcha("g-recaptcha-response",
                         form_data.get("g-recaptcha-response", "")))
    
    if len(error_messages) > 0:
        raise UserError(error_messages)
    
    return None


def validate_string(field, s = ""):
    if len(s) < 1:
        return {field: "This field is required"}
        
    return {}


def validate_captcha(field, captcha_response):
    CAPTCHA_SECRET = utilities.get_environ_var("CAPTCHA_SECRET", encrypted=True)
    CAPTCHA_API = utilities.get_environ_var("CAPTCHA_API")
    
    post_fields = {'secret': CAPTCHA_SECRET,
                   'response': captcha_response}

    request = Request(CAPTCHA_API, urlencode(post_fields).encode())
    response = load(urlopen(request))
    
    if not response.get('success', False):
        return {field: "The captcha was incorrect"}

    return {}