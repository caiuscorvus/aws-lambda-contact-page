from botocore.exceptions import ClientError


class InvalidInputError(ValueError):
    def __init__(self, message, last_input, error_messages):
        # *args is used to get a list of the parameters passed in
        self.message = message
        self.last_input = last_input
        self.error_messages = error_messages

    def __str__(self):
        return str(self.message)

class EmailError(ClientError):
    """
    Indicates a problem in sending an email
    """
    def __init__(self, arg):
        self.args = arg


class PageBuildingError(ValueError):
    """
    Indicates a problem with supplied data
    """
    def __init__(self, arg):
        self.args = arg

