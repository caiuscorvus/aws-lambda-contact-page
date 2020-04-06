from botocore.exceptions import ClientError


class InvalidInputError(ValueError):
    """
    Indicates a problem with supplied data
    """
    def __init__(self, input_values, error_messages):
        ValueError.__init__(self, raw_input, error_messages)
        self.input_values = input_values
        self.error_messages = error_messages


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

