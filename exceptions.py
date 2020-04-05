from botocore.exceptions import ClientError


class ClientError(ValueError):
    """
    Indicates a problem with data from client
    """

    def __init__(self, arg):
        self.args = arg


class EmailError(ClientError):
    """
    Indicates a problem in sending an email
    """

    def __init__(self, arg):
        self.args = arg