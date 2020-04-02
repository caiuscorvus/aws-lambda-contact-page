from bs4 import BeautifulSoup

from utilities import get_environ_var
from utilities import get_file


S3_BUCKET = get_environ_var("S3_BUCKET")
S3_KEY = get_environ_var("S3_KEY")
TEMPLATE_PAGE = get_file(S3_BUCKET, S3_KEY)

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


# constructs a web page and inserts error messages
def error_page(form_data=dict(), error_data=dict()):
    base_page = BeautifulSoup(TEMPLATE_PAGE, 'html.parser')
    
    # iterate over user submission
    for field, response in form_data.items():
        # find submitted element on form page
        if field == "g-recaptcha-response":
            form_element = base_page.find("div", {"class": "g-recaptcha"})
        else:    
            form_element = base_page.find(
                ["input","textarea","checkbox", "radio"],
                {"name": field})

        if form_element is None:
            # this response was not supplied by user
            # for example, submit button text
            break
        
        # check for and insert any error messages
        if field in error_data:
            error_tag = new_tag(ERROR_MARKUP)
            error_tag.string = error_data.get(field, "")
            form_element.insert_before(error_tag)

        # repopulate form data
        if len(response) > 0:
            if form_element.type == "input":
                form_element['value'] = response
            elif form_element.type == "textarea":
                form_element.string = response
            elif form_element.type == "checkbox" or type == "radio":
                form_element['checked'] = "checked"
    
    return base_page.encode(formatter="minimal")


def success_page(form_data=dict()):
    return replace_content(TEMPLATE_PAGE, SUCCESS_CONTENT)


def failure_page(form_data=dict()):
    return replace_content(TEMPLATE_PAGE, FAILURE_CONTENT)


def replace_content(page, markup):
    base_page = BeautifulSoup(page, 'html.parser')
    new_content = new_tag(markup)
        
    content_tag = base_page.find(["main"], {"id": "content"})
    content_tag.replace_with(new_content)
    
    return base_page.encode(formatter="minimal")


def new_tag(markup):
    return BeautifulSoup(markup, 'html.parser')
