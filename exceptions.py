class BluvoException(Exception):
    """Base class for exceptions."""
    pass

class StampInvalid(BluvoException):
    """Stamp is invalid"""
    def __init__(self):
        self.message = "API request denied due to invalid stamp"
        super().__init__(self.message)