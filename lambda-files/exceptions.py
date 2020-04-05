from botocore.exceptions import ClientError


class FormInputError(ValueError):
    """
    Indicates a problem with supplied data
    """
    def __init__(self, arg):
        self.args = arg

class EmailError(ClientError):
    """
    Indicates a problem in sending an email
    """
    def __init__(self, arg):
        self.args = arg
