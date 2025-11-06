# -*- coding: utf-8 -*-
"""
Unpublished work.
Copyright (c) 2018 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: rameshchandra.d@teradata.com
Secondary Owner:

teradataml.common.exceptions
----------
An Error class for the teradataml python module
"""


import warnings
import json
import pprint
import traceback


class TeradataMlException(Exception):
    """
    Teradata Ml Exception class.
    All public functions and methods should only raise TeradataMlException so that
    application code need only catch TeradataMlException.
    Public functions and methods should use the following form

        try:
            # do something useful
        except TeradataMlError:
            # re-raise a TeradataMlException that was raised by one of our internal functions.
            raise
        exception Exception as err:
            # all other exceptions (like driver exceptions) are wrapped in a TeradataMlException
            raise TeradataMlException(msg, code) from err

    Both public and internal functions should raise TeradataMlException for any
    application errors like invalid argument.

    For example:
        if key is not in columnnames:
            raise TeradataMlException(msg, code)


    Internal functions should let other exceptions from the driver bubble up.
    If internal functions would like to do something in a try: except: block like logging,
    then it should use the form

        try:
            # do something useful
        except:
            logger.log ("log something useful")
            # re-raise the error so that it is caught by the calling public function.
            # the calling public function will take care of wrapping the exception in TeradataMlError
            # this will avoid a lot of unnecessary exception handling code.
            raise

    If TeradataMlException was the result of another exception, then the
    attribute __cause__ will be set with the root cause exception.

    """
    def __init__(self, msg, code):
        """
        Initializer for TeradataMlException. Call the parent class initializer and set the code.
        PARAMETERS:
            msg - The error message, should be a standard message from messages._getMessage().
            code - The code, should be from MessageCodes like MessageCodes.CONNECTION_FAILURE.

        RETURNS:
            A TeradataMlException with the error message and code.

        RAISES:

        EXAMPLES:
            if key is not in columnnames:
                raise TeradataMlException(message._getMessage(MessageCodes.CONNECTION_FAILURE), MessageCodes.CONNECTION_FAILURE)
        """
        super(TeradataMlException, self).__init__(msg)
        self.code = code
        
        # Automatically log the exception when it's created
        self._log_exception(msg, code)
    
    def _log_exception(self, msg, code):
        """Automatically log TeradataMlException instances.
        
        PARAMETERS:
            msg - The error message.
            code - The error code.

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            raise TeradataMlException("An error occurred", 1001)
        
        """
        try:
            # Import here to avoid circular imports
            from teradataml.common.logger import get_td_logger
            
            logger = get_td_logger()
            # This check prevents errors when logging is disabled (NONE level) because the _NullLogger uses __getattr__ 
            # for dynamic method creation, and without this check, the code would attempt expensive stack trace generation 
            # even when logging is disabled. 
            # NOTE: Removing it could cause AttributeError or unnecessary performance overhead during exception handling.
            if hasattr(logger, 'error'):
                # Get stack trace for context
                stack_trace = traceback.format_stack()
                # Remove the last 2 frames (this method and __init__)
                relevant_stack = ''.join(stack_trace[:-2])
                
                error_msg = f"TeradataMlException raised - Code: {code}, Message: {msg}"
                logger.error(f"{error_msg}\\nStack trace:\\n{relevant_stack}")
        except Exception:
            # If logging fails, don't interfere with the exception being raised
            pass

class TeradatamlRestException(TeradataMlException):
    def __init__(self, msg, code, raw_message=None):
        super().__init__(msg, code)

        self._msg = msg
        self._raw_message = raw_message
    
    @property
    def json_response(self):
        """
        Returns the JSON response from the server.
        """
        if self._raw_message is not None and self._raw_message.startswith("Error message: "):
            failure_msg = f"Could not convert msg to json. Message is \n{self._raw_message}"
            try:
                json_resp = self._msg.split("Error message: ")[1]
                json_resp = json.loads(json_resp)
                return pprint.pformat(json_resp)
            except json.JSONDecodeError as _:
                warnings.warn(failure_msg)
        elif self._raw_message is None:
            return None
        else:
            warnings.warn(failure_msg)
    