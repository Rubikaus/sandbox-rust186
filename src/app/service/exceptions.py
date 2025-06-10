from typing import Optional, Any
from app import messages


class ServiceException(Exception):

    default_message = None

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class CheckerException(ServiceException):

    default_message = messages.MSG_5


class ExecutionException(ServiceException):

    default_message = messages.MSG_6


class CompileException(ServiceException):

    default_message = messages.MSG_7
