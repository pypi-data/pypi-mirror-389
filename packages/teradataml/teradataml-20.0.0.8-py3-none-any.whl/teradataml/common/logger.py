"""
Unpublished work.
Copyright (c) 2025 by Teradata Corporation. All rights reserved.
TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET

Primary Owner: akhil.bisht@teradata.com
Secondary Owner: pankajvinod.purandare@teradata.com

This file implements the TeradataMlLogger for session-level logging in teradataml.
"""

import os
import sys
import time
import logging
import functools
import traceback
from teradataml.utils.validators import _Validators
from teradataml.common.constants import LoggingLevel

# Define logging methods for dynamic access
_LOG_METHODS = ['info', 'debug', 'warning', 'error', 'exception']

class _TeradataMlLogger:
    """
    Isolated teradataml-specific logger instance that doesn't interfere with global logging.
    """

    def __init__(self, name="teradataml", level=logging.INFO, prf_time=False):
        """
        DESCRIPTION:
            Initialize the teradataml-specific logger instance.
            Note:
                * This logger is isolated and does not propagate to the root logger.
                * By default, it uses '%(asctime)s | %(levelname)-8s | %(message)s' format for log messages.

        PARAMETERS:
            name:
                Optional Argument.
                Specifies the name for the logger instance.
                Default Value: "teradataml"
                Types: str

            level:
                Optional Argument.
                Specifies the initial logging level.
                Default Value: logging.INFO
                Permitted Values: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
                Types: int

            prf_time:
                Optional Argument.
                Specifies whether to show performance time logging in all functions.
                Default Value: False
                Types: bool

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> logger = _TeradataMlLogger("CustomLogger", logging.DEBUG, True)
        """
        # Validate argument types
        argument_validation_params = []
        argument_validation_params.append(['name', name, False, str, True])
        argument_validation_params.append(['level', level, False, int, True, [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]])
        argument_validation_params.append(['prf_time', prf_time, False, bool, True])
        _Validators._validate_function_arguments(argument_validation_params)

        self._logger = logging.getLogger(f"{name}")
        self._logger.setLevel(logging.DEBUG)  # Allow all levels internally
        self._current_level = level
        self._handlers = []
        self._prf_time = prf_time  # Simple boolean flag
        self._formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')  # Default formatter with fixed-width levels
        
        # Clear any existing handlers to ensure clean state
        self._logger.handlers.clear()
        self._logger.propagate = False  # Don't propagate to root logger - ISOLATED!
    
    def _set_level(self, level):
        """
        DESCRIPTION:
            Set the effective logging level for the logger instance.

        PARAMETERS:
            level:
                Required Argument.
                Specifies the logging level to set.
                Permitted Values: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
                Types: int

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> logger._set_level(logging.DEBUG)
            >>> logger._set_level(logging.WARNING)
        """
        self._current_level = level
        # Update all handlers
        for handler in self._handlers:
            handler.setLevel(level)
    
    def _set_formatter(self, formatter=None):
        """
        DESCRIPTION:
            Set a custom formatter for the logger instance and update all existing handlers.
            If no formatter is provided, resets to default formatter.

        PARAMETERS:
            formatter:
                Optional Argument.
                Specifies the logging formatter to use.
                Default Value: None (uses default formatter)
                Types: logging.Formatter

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> custom_formatter = logging.Formatter('%(levelname)s: %(message)s')
            >>> logger._set_formatter(custom_formatter)
            >>> logger.set_formatter()  # Reset to default
        """
        if formatter is not None:
            self._formatter = formatter
        
        # Update all existing handlers with the new formatter
        for handler in self._handlers:
            handler.setFormatter(self._formatter)
    
    def _add_console_handler(self, formatter=None):
        """
        DESCRIPTION:
            Add console handler to the isolated logger for output to console.
            Note:
                * Only one console handler is added, subsequent calls return the existing handler.

        PARAMETERS:
            formatter:
                Optional Argument.
                Specifies the logging formatter to use.
                Default Value: None (uses default formatter)
                Types: logging.Formatter

        RETURNS:
            logging.StreamHandler
                The console handler that was added.

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> handler = logger._add_console_handler()
            >>> custom_formatter = logging.Formatter('%(message)s')
            >>> handler = logger.add_console_handler(custom_formatter)
        """
        # Check if console handler already exists
        for handler in self._handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                return handler  # Console handler already exists
        
        if formatter is None:
            formatter = self._formatter
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(self._current_level)
        
        self._logger.addHandler(handler)
        self._handlers.append(handler)
        return handler
    
    def _add_file_handler(self, file_path, formatter=None):
        """
        DESCRIPTION:
            Add file handler to the isolated logger for output to file.
            Note:
                * Only one file handler is added, subsequent calls return the existing handler.

        PARAMETERS:
            file_path:
                Required Argument.
                Specifies the path to the log file.
                Types: str

            formatter:
                Optional Argument.
                Specifies the logging formatter to use.
                Default Value: None (uses default formatter)
                Types: logging.Formatter

        RETURNS:
            logging.FileHandler
                The file handler that was added.

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> handler = logger._add_file_handler("app.log")
            >>> custom_formatter = logging.Formatter('%(message)s')
            >>> handler = logger._add_file_handler("app.log", custom_formatter)
        """
        # Check if file handler for this path already exists
        # Use normcase for Windows case-insensitive path comparison
        normalized_target_path = os.path.normcase(os.path.abspath(file_path))
        for handler in self._handlers:
            if isinstance(handler, logging.FileHandler):
                normalized_handler_path = os.path.normcase(handler.baseFilename)
                if normalized_handler_path == normalized_target_path:
                    return handler  # File handler for this path already exists
        
        if formatter is None:
            formatter = self._formatter

        handler = logging.FileHandler(file_path)
        handler.setFormatter(formatter)
        handler.setLevel(self._current_level)

        self._logger.addHandler(handler)
        self._handlers.append(handler)
        return handler
    
    def _add_external_handler(self, handler):
        """
        DESCRIPTION:
            Add an external handler to the isolated logger.

        PARAMETERS:
            handler:
                Required Argument.
                Specifies the external logging handler to add.
                Types: logging.Handler

        RETURNS:
            logging.Handler
                The handler that was added.

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> external_handler = logging.FileHandler("external.log")
            >>> handler = logger._add_external_handler(external_handler)
        """
        # Only set the level if the handler doesn't already have one
        if handler.level == 0:
            handler.setLevel(self._current_level)

        self._logger.addHandler(handler)
        self._handlers.append(handler)
        return handler
    
    def __getattr__(self, name):
        """
        DESCRIPTION:
            Dynamically access logging methods (info, debug, warning, error, exception, prf_time).

        PARAMETERS:
            name:
                Required Argument.
                Specifies the name of the attribute being accessed.
                Types: str

        RETURNS:
            function
                The logging method corresponding to the name.

        RAISES:
            AttributeError
                If the attribute name is not a recognized logging method.

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> logger.info("Info message")
            >>> logger.debug("Debug message")
            >>> logger.warning("Warning message")
            >>> logger.error("Error message")
            >>> logger.exception("Exception message")
            >>> logger.prf_time("Performance timing message")
        """

        if name in _LOG_METHODS:
            def log_method(message, *args, **kwargs):
                """
                DESCRIPTION:
                    Log a message with the specified logging level.

                PARAMETERS:
                    message:
                        Required Argument.
                        Specifies the message to log.
                        Types: str

                    *args:
                        Optional Arguments.
                        Specifies additional positional arguments for message formatting.
                        Types: Any

                    **kwargs:
                        Optional Arguments.
                        Specifies additional keyword arguments for logging.
                        Types: Any

                RETURNS:
                    None

                RAISES:
                    None
                """
                return getattr(self._logger, name)(message, *args, **kwargs)
            return log_method
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def prf_time(self, message, *args, **kwargs):
        """
        DESCRIPTION:
            Log performance timing message using standard DEBUG level.

        PARAMETERS:
            message:
                Required Argument.
                Specifies the performance timing message to log.
                Types: str

            *args:
                Optional Arguments.
                Specifies additional positional arguments for message formatting.
                Types: Any

            **kwargs:
                Optional Arguments.
                Specifies additional keyword arguments for logging.
                Types: Any

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> logger.prf_time("Operation completed in 2.5 seconds")
            >>> logger.prf_time("Method %s took %f seconds", method_name, elapsed_time)
        """
        # Validate argument types
        argument_validation_params = []
        argument_validation_params.append(['message', message, True, str, True])
        _Validators._validate_function_arguments(argument_validation_params)

        # Only log if PRF_TIME flag is enabled
        if self._prf_time:
            self._logger.debug(f"PRF_TIME | {message}", *args, **kwargs)
    
    def _is_enabled_for_level(self, level_name):
        """
        DESCRIPTION:
            Check if logging is enabled for the given level name.

        PARAMETERS:
            level_name:
                Required Argument.
                Specifies the logging level name to check.
                Permitted Values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'PRF_TIME'
                Types: str

        RETURNS:
            bool
                True if logging is enabled for the level, False otherwise.

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> if logger._is_enabled_for_level('DEBUG'):
            ...     logger.debug("Debug message")
            >>> enabled = logger._is_enabled_for_level('PRF_TIME')
        """
        if level_name == 'PRF_TIME':
            return self._prf_time
        level_num = LoggingLevel.level_map.value.get(level_name, logging.INFO)
        return self._current_level <= level_num
    
    def remove_handlers(self, handler_type=None):
        """
        DESCRIPTION:
            Remove specific types of handlers or all handlers from the logger.

        PARAMETERS:
            handler_type:
                Optional Argument.
                Specifies the type of handler to remove. If None, removes all handlers.
                Default Value: None
                Permitted Values: 'console', 'file', a specific handler class or type
                Types: str or type of logging.Handler

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> logger = _TeradataMlLogger()
            >>> logger.remove_handlers('console')  # Remove only console handlers
            >>> logger.remove_handlers('file')     # Remove only file handlers  
            >>> logger.remove_handlers()           # Remove all handlers
            >>> logger.remove_handlers(RotatingFileHandler)  # Remove specific type
        """
        for handler in self._handlers[:]:
            remove = False

            if handler_type is None:
                remove = True
            elif handler_type == 'console':
                remove = isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler)
            elif handler_type == 'file':
                remove = isinstance(handler, logging.FileHandler)
            elif isinstance(handler_type, type):
                remove = isinstance(handler, handler_type)
            elif isinstance(handler_type, str):
                remove = handler_type.lower() in handler.__class__.__name__.lower()

            if remove:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                self._logger.removeHandler(handler)
                self._handlers.remove(handler)

        # Clear all handlers lists if removing all
        if handler_type is None:
            self._logger.handlers.clear()

class _ExternalLoggerWrapper:
    """
    Wrapper for external logger that provides the same interface as _TeradataMlLogger.
    """
    
    def __init__(self, external_logger, prf_time=False):
        """
        DESCRIPTION:
            Initialize wrapper with external logger instance.

        PARAMETERS:
            external_logger:
                Required Argument.
                Specifies the external logger to wrap.
                Types: logging.Logger

            prf_time:
                Optional Argument.
                Specifies whether PRF_TIME logging is enabled.
                Default Value: False
                Types: bool

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> import logging
            >>> external_logger = logging.getLogger("external")
            >>> wrapper = _ExternalLoggerWrapper(external_logger, True)
        """
        # Validate argument types
        argument_validation_params = []
        argument_validation_params.append(['external_logger', external_logger, True, logging.Logger, True])
        argument_validation_params.append(['prf_time', prf_time, False, bool, True])
        _Validators._validate_function_arguments(argument_validation_params)

        self._external_logger = external_logger
        self._handlers = []  # Track handlers we add
        self._prf_time = prf_time

    def __getattr__(self, name):
        if name in _LOG_METHODS:
            def log_method(message, *args, **kwargs):
                return getattr(self._external_logger, name)(message, *args, **kwargs)
            return log_method
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def prf_time(self, message, *args, **kwargs):
        """
        DESCRIPTION:
            Log performance timing message via external logger using DEBUG level.

        PARAMETERS:
            message:
                Required Argument.
                Specifies the performance timing message to log.
                Types: str

            *args:
                Optional Arguments.
                Specifies additional positional arguments for message formatting.
                Types: Any

            **kwargs:
                Optional Arguments.
                Specifies additional keyword arguments for logging.
                Types: Any

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> wrapper = _ExternalLoggerWrapper(external_logger)
            >>> wrapper.prf_time("Operation took 1.5 seconds")
        """
        # Validate argument types
        argument_validation_params = []
        argument_validation_params.append(['message', message, True, str, True])
        _Validators._validate_function_arguments(argument_validation_params)

        # Only log if PRF_TIME flag is enabled
        if self._prf_time:
            self._external_logger.debug(f"PRF_TIME | {message}", *args, **kwargs)
    
    def _is_enabled_for_level(self, level_name):
        """
        DESCRIPTION:
            Check if logging is enabled for the given level via external logger.

        PARAMETERS:
            level_name:
                Required Argument.
                Specifies the logging level name to check.
                Permitted Values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'PRF_TIME'
                Types: str

        RETURNS:
            bool
                True if logging is enabled for the level, False otherwise.

        RAISES:
            None

        EXAMPLES:
            >>> wrapper = _ExternalLoggerWrapper(external_logger)
            >>> enabled = wrapper._is_enabled_for_level('DEBUG')
        """
        # Validate argument type
        argument_validation_params = []
        argument_validation_params.append(['level_name', level_name, True, str, True, ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'PRF_TIME']])
        _Validators._validate_function_arguments(argument_validation_params)

        if level_name == 'PRF_TIME':
            return self._prf_time
        
        level_num = LoggingLevel.level_map.value.get(level_name, logging.INFO)
        return self._external_logger.isEnabledFor(level_num)


class TDLogLevel:
    """
    Internal class to define log levels for TeradataML.
    """
    NONE = "NONE"
    INFO = "INFO"
    DEBUG = "DEBUG"
    PRF_TIME = "PRF_TIME"


class _NullLogger:
    """
    Null logger implementation for NONE level providing zero overhead.
    """

    def __getattr__(self, name):
        """
        DESCRIPTION:
            Dynamically provide no-operation methods for logging methods.

        PARAMETERS:
            name:
                Required Argument.
                Specifies the name of the attribute being accessed.
                Types: str

        RETURNS:
            function
                A no-operation function for logging methods.

        RAISES:
            AttributeError
                If the attribute name is not a recognized logging method.

        EXAMPLES:
            >>> null_logger = _NullLogger()
            >>> null_logger.info("This message is ignored")
            >>> null_logger.debug("This debug message is ignored")
        """
        if name in _LOG_METHODS:
            def noop(*args, **kwargs):
                pass
            return noop
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def prf_time(self, message, *args, **kwargs):
        """
        DESCRIPTION:
            No-operation method for performance timing logging (ignored).

        PARAMETERS:
            message:
                Required Argument.
                Specifies the performance timing message to log (ignored).
                Types: str

            *args:
                Optional Arguments.
                Specifies additional positional arguments (ignored).
                Types: Any

            **kwargs:
                Optional Arguments.
                Specifies additional keyword arguments (ignored).
                Types: Any

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> null_logger = _NullLogger()
            >>> null_logger.prf_time("This performance timing message is ignored")
        """
        pass
    
    def _is_enabled_for_level(self, level_name):
        """
        DESCRIPTION:
            Check if logging is enabled for the given level (always False for null logger).

        PARAMETERS:
            level_name:
                Required Argument.
                Specifies the logging level name to check (ignored).
                Permitted Values: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'PRF_TIME'
                Types: str

        RETURNS:
            bool
                Always returns False for null logger.

        RAISES:
            None

        EXAMPLES:
            >>> null_logger = _NullLogger()
            >>> enabled = null_logger._is_enabled_for_level('DEBUG')  # Returns False
        """
        return False


class TeradataMlLogger:
    """
    Session-level logger manager for teradataml with performance timing capabilities.
    """
    # Singleton instance and initialization flag for TeradataMlLogger
    _instance = None
    # Flag to indicate if the logger has been initialized to prevent multiple initializations
    _initialized = False
    # Current log level for the TeradataMlLogger instance
    _level = TDLogLevel.NONE
    # Internal logger instance for teradataml logging
    _teradata_logger = None
    # External logger instance for integration with external logging systems
    _external_logger = None
    # Performance timing flag to indicate if performance timing logging is enabled
    _prf_time_flag = False

    def __new__(cls, cls_to_wrap=None):
        """
        DESCRIPTION:
            Create or return singleton instance, or perform class decoration.

        PARAMETERS:
            cls_to_wrap:
                Optional Argument.
                Specifies the class to wrap with logging decoration.
                Default Value: None
                Types: type

        RETURNS:
            TeradataMlLogger or decorated class
                Returns singleton instance or decorated class if cls_to_wrap provided.

        RAISES:
            None

        EXAMPLES:
        # Example 1: Normal singleton instantiation (without decorator)
        >>> from teradataml.common.logger import TeradataMlLogger, TDLogLevel, get_td_logger
        >>> TeradataMlLogger.init(level=TDLogLevel.INFO)
        >>> logger_instance = TeradataMlLogger()
        >>> logger = logger_instance.get_logger()
        >>> logger.info("This is a test message")
        2025-09-23 11:27:52,976 | INFO     | This is a test message
        
        # Example 2: Using as decorator
        >>> @TeradataMlLogger
        ... class DataProcessor:
        ...     def __init__(self, name):
        ...         self.name = name
        ...         # self._logger is automatically available
        ...     
        ...     def process_data(self, data):
        ...         self._logger.info(f"Processing {len(data)} items")
        ...         return [x * 2 for x in data]
        >>> TeradataMlLogger.init(level=TDLogLevel.PRF_TIME)
        >>> processor = DataProcessor("test")
        >>> result = processor.process_data([1, 2, 3])
        2025-09-23 11:31:24,389 | INFO     | PRF_TIME | Started DataProcessor.__init__
        2025-09-23 11:31:24,389 | INFO     | PRF_TIME | Completed DataProcessor.__init__ in 0.00000 secs
        2025-09-23 11:31:24,389 | INFO     | PRF_TIME | Started DataProcessor.process_data
        2025-09-23 11:31:24,389 | INFO     | Processing 3 items
        2025-09-23 11:31:24,389 | INFO     | PRF_TIME | Completed DataProcessor.process_data in 0.00053 secs
        
        # Example 3: Using as decorator with debug logging
        >>> @TeradataMlLogger
        ... class Calculator:
        ...     def __init__(self):
        ...         self._logger.info("Calculator initialized")
        ...         pass
        ...     
        ...     def add(self, a, b):
        ...         self._logger.debug(f"Adding {a} + {b}")
        ...         return a + b
        >>> TeradataMlLogger.init(level=TDLogLevel.DEBUG)
        >>> calc = Calculator()
        >>> result = calc.add(5, 3)
        2025-09-23 11:35:47,674 | INFO     | Calculator initialized
        2025-09-23 11:35:47,675 | DEBUG    | Adding 5 + 3
        
        # Example 4: Without decorator - manual logger usage
        >>> class SimpleClass:
        ...     def __init__(self):
        ...         self.logger = get_td_logger()
        ...     
        ...     def do_work(self):
        ...         self.logger.info("Doing some work")
        >>> TeradataMlLogger.init(level=TDLogLevel.INFO)
        >>> obj = SimpleClass()
        >>> obj.do_work()
        2025-09-23 11:44:21,840 | INFO     | Doing some work
        """
        # If called with a class (decorator usage), perform decoration
        if cls_to_wrap is not None and isinstance(cls_to_wrap, type):
            return cls.decorate(cls_to_wrap)
        
        # Normal singleton instantiation
        if cls._instance is None:
            cls._instance = super(TeradataMlLogger, cls).__new__(cls)
        return cls._instance

    @classmethod
    def init(cls, 
             name="teradataml_logger",
             level=TDLogLevel.NONE,
             logger=None,
             log_file=None):
        """
        DESCRIPTION:
            Initialize the teradataml session logger. If already initialized, reset and reinitialize.
            Note:
                * If level is NONE, uses null logger for zero overhead.
                * If external logger is provided, uses it directly instead of copying handlers.
                * If log_file is specified, logs to file in ~/.teradataml/logs directory.
                * If no log_file and no external logger, logs to console by default.
                * Performance timing logging is enabled only if level is PRF_TIME.
                * By default, it uses console handler with '%(asctime)s | %(levelname)-8s | %(message)s' format.

        PARAMETERS:
            name:
                Optional Argument.
                Specifies the name of the logger instance.
                Default Value: 'teradataml_logger'
                Types: str

            level:
                Optional Argument.
                Specifies the log level to set.
                Default Value: TDLogLevel.NONE
                Permitted Values: 
                    * TDLogLevel.NONE : 'NONE' no logging, zero overhead
                    * TDLogLevel.INFO : 'INFO' standard logging
                    * TDLogLevel.DEBUG : 'DEBUG' detailed logging
                    * TDLogLevel.PRF_TIME : 'PRF_TIME' logging with performance timing enabled
                Types: str

            logger:
                Optional Argument.
                Specifies external logger to use for integration.
                Default Value: None
                Types: logging.Logger

            log_file:
                Optional Argument.
                Specifies file name for log file.
                Default Value: None
                Types: str

        RETURNS:
            None

        RAISES:
            ValueError
                If invalid log level is provided.

        EXAMPLES:
            >>> TeradataMlLogger.init()
            >>> TeradataMlLogger.init(level='DEBUG')
            >>> TeradataMlLogger.init(level='INFO', log_file='app.log')
            >>> TeradataMlLogger.init(level='PRF_TIME')
            >>> import logging
            >>> external_logger = logging.getLogger('external')
            >>> TeradataMlLogger.init(logger=external_logger)
        """
        argument_validation_params = []
        argument_validation_params.append(['name', name, False, str, True])
        argument_validation_params.append(['level', level, False, str, True, ['NONE', 'INFO', 'DEBUG', 'PRF_TIME']])
        argument_validation_params.append(['logger', logger, True, logging.Logger, True])
        argument_validation_params.append(['log_file', log_file, True, str, True])

        # Validate argument types
        _Validators._validate_function_arguments(argument_validation_params)

        # If already initialized, reset first
        if cls._initialized:
            cls.reset()
        
        cls._level = level
        cls._external_logger = logger
        cls._initialized = True
        
        # Set PRF_TIME flag for conditional wrapper
        cls._prf_time_flag = (level == TDLogLevel.PRF_TIME)

        # If external logger provided, use it directly instead of copying handlers
        if cls._external_logger is not None:
            # Create a wrapper that uses the external logger directly
            # This avoids confusion between internal and external logger instances
            cls._teradata_logger = _ExternalLoggerWrapper(cls._external_logger, cls._prf_time_flag)
        else:
            
            # If level is NONE, use null logger for zero overhead
            if level == TDLogLevel.NONE:
                cls._teradata_logger = _NullLogger()
                return
            
            # Create our isolated teradataml logger
            level_map = {
                TDLogLevel.INFO: logging.INFO,
                TDLogLevel.DEBUG: logging.DEBUG,
                TDLogLevel.PRF_TIME: logging.DEBUG
            }
            
            effective_level = level_map[level]
            cls._teradata_logger = _TeradataMlLogger(name, effective_level, cls._prf_time_flag)
            
            # Add file handler if specified
            if log_file is not None:
                # Use default ~/.teradataml/logs directory
                home_dir = os.path.expanduser("~")
                log_dir = os.path.join(home_dir, ".teradataml", "logs")
                os.makedirs(log_dir, exist_ok=True)
                
                file_path = os.path.join(log_dir, log_file)
                cls._teradata_logger._add_file_handler(file_path)
            else:
                # Add console handler only if no file handler is specified and no external logger
                if cls._external_logger is None:
                    cls._teradata_logger._add_console_handler()
    
    @classmethod
    def get_logger(cls):
        """
        DESCRIPTION:
            Get the teradataml logger instance.

        PARAMETERS:
            None

        RETURNS:
            _TeradataMlLogger or _NullLogger
                The teradataml logger instance or null logger if NONE level.

        RAISES:
            None

        EXAMPLES:
            >>> logger = TeradataMlLogger.get_logger()
            >>> logger.info("Some message")
        """
        if not cls._initialized or cls._level == TDLogLevel.NONE:
            return _NullLogger()
        return cls._teradata_logger
    
    @classmethod
    def get_level(cls):
        """
        DESCRIPTION:
            Get current log level.

        PARAMETERS:
            None

        RETURNS:
            str
                The current logging level.

        RAISES:
            None

        EXAMPLES:
            >>> level = TeradataMlLogger.get_level()
            >>> print(f"Current level: {level}")
        """
        return cls._level
    
    @classmethod
    def is_performance_enabled(cls):
        """
        DESCRIPTION:
            Check if performance timing is enabled.

        PARAMETERS:
            None

        RETURNS:
            bool
                True if performance timing is enabled, False otherwise.

        RAISES:
            None

        EXAMPLES:
            >>> if TeradataMlLogger.is_performance_enabled():
            ...     print("Performance timing is enabled")
        """
        return cls._level == TDLogLevel.PRF_TIME
    
    @classmethod
    def reset(cls):
        """
        DESCRIPTION:
            Reset the logger state.

        PARAMETERS:
            None

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> TeradataMlLogger.reset()
        """
        if cls._teradata_logger and hasattr(cls._teradata_logger, 'remove_handlers'):
            cls._teradata_logger.remove_handlers()
        
        cls._instance = None
        cls._initialized = False
        cls._level = TDLogLevel.NONE
        cls._teradata_logger = None
        cls._external_logger = None
        cls._prf_time_flag = False
    
    def __call__(self, cls_to_wrap):
        """
        DESCRIPTION:
            Allow TeradataMlLogger to be used directly as a class decorator.
            Always injects an instance attribute _logger = TeradataMlLogger.get_logger().
            Timing wrappers only activate when session level == TDLogLevel.PRF_TIME.
            Delegates to TeradataMlLogger.decorate().

        PARAMETERS:
            cls_to_wrap:
                Required Argument.
                Specifies the class to decorate.
                Types: type

        RETURNS:
            type
                The decorated class with method timing.

        RAISES:
            None

        EXAMPLES:
            >>> @TeradataMlLogger()
            ... class MyClass:
            ...     def method(self):
            ...         pass
        """
        return self.__class__.decorate(cls_to_wrap)
    
    @classmethod
    def decorate(cls, cls_to_wrap):
        """
        DESCRIPTION:
            Class decorator that:
                * Always injects an instance attribute _logger = TeradataMlLogger.get_logger() into each constructed object.
                * Conditionally (only when session level == TDLogLevel.PRF_TIME) wraps __init__ and all methods defined
                    directly on the class (instance, @classmethod, @staticmethod) with lightweight timing logic that:
                    - Logs "Started <Class>.<method>"
                    - Executes the method
                    - Logs "Completed ..." with elapsed seconds (or "Failed ..." on exception)
                * When PRF_TIME is NOT enabled, methods execute with effectively zero added overhead.
                * Automatically logs exceptions (except TeradataMlException) via the session logger while still re-raising them.
                * Avoids wrapping dunder methods (other than __init__) to keep behavior predictable.

        PARAMETERS:
            cls_to_wrap:
                Required Argument.
                Specifies the class to decorate.
                Types: type

        RETURNS:
            type
                The decorated class with method timing.

        RAISES:
            None

        EXAMPLES:
            >>> @TeradataMlLogger.decorate
            ... class MyClass:
            ...     def method(self):
            ...         pass
            >>> # Or use as decorator
            >>> @TeradataMlLogger
            ... class MyClass:
            ...     pass
        """
        # ALWAYS inject logger, even if not PRF_TIME level
        original_init = cls_to_wrap.__init__
        
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):   
            try:
                # Only add timing if PRF_TIME is enabled
                if cls._prf_time_flag:
                    method_signature = f"{cls_to_wrap.__name__}.__init__"
                    self._logger.prf_time(f"Started {method_signature}")
                    start_time = time.perf_counter()
                    
                    try:
                        result = original_init(self, *args, **kwargs)
                        elapsed = time.perf_counter() - start_time
                        self._logger.prf_time(f"Completed {method_signature} in {elapsed:.5f} secs")
                        return result
                    except Exception as e:
                        elapsed = time.perf_counter() - start_time
                        self._logger.prf_time(f"Failed {method_signature} in {elapsed:.5f} secs")
                        raise
                else:
                    # No timing, just call original __init__
                    return original_init(self, *args, **kwargs)
            except Exception as e:
                # Automatic exception logging for __init__ method
                cls._log_exception_helper(e, f"{cls_to_wrap.__name__}.__init__()")
                # Re-raise the exception to maintain normal behavior
                raise
        
        cls_to_wrap.__init__ = new_init

        # Inject a dynamic property only once so every access reflects latest init().
        if not isinstance(getattr(cls_to_wrap, "_logger", None), property):
            def _dynamic_logger(self):
                return TeradataMlLogger.get_logger()
            cls_to_wrap._logger = property(_dynamic_logger)
        
        # Use conditional decoration for minimal overhead
        # Wrap all methods defined in this class (not inherited ones)
        for attr_name, attr_value in cls_to_wrap.__dict__.items():
            if not attr_name.startswith('__') and not attr_name.endswith('__'):
                # Check if it's a method we should wrap
                if isinstance(attr_value, staticmethod):
                    wrapped = cls._create_conditional_method_wrapper(attr_value.__func__, cls_to_wrap.__name__, attr_name)
                    setattr(cls_to_wrap, attr_name, staticmethod(wrapped))
                elif isinstance(attr_value, classmethod):
                    wrapped = cls._create_conditional_method_wrapper(attr_value.__func__, cls_to_wrap.__name__, attr_name)
                    setattr(cls_to_wrap, attr_name, classmethod(wrapped))
                elif callable(attr_value) and not isinstance(attr_value, type):
                    # Regular instance methods
                    if hasattr(attr_value, '__call__') and hasattr(attr_value, '__name__'):
                        wrapped = cls._create_conditional_method_wrapper(attr_value, cls_to_wrap.__name__, attr_name)
                        setattr(cls_to_wrap, attr_name, wrapped)
        
        return cls_to_wrap
    
    @classmethod
    def _log_exception_helper(cls, exception, context_info):
        """
        DESCRIPTION:
            Helper function to log exceptions with consistent formatting.
            Skips TeradataMlException as it logs itself.

        PARAMETERS:
            exception:
                Required Argument.
                Specifies the exception to log.
                Types: Exception

            context_info:
                Required Argument.
                Specifies context information about where the exception occurred.
                Types: str

        RETURNS:
            None

        RAISES:
            None

        EXAMPLES:
            >>> cls._log_exception_helper(e, "MyClass.__init__()")
        """
        # Skip TeradataMlException as it logs itself
        if not exception.__class__.__name__ == 'TeradataMlException':
            try:
                # Log using teradataml logger
                logger = TeradataMlLogger.get_logger()
                # Check if logger has 'error' method for _NullLogger compatibility
                if hasattr(logger, 'error'):
                    # Log exception with traceback
                    error_msg = f"Exception in {context_info}: {type(exception).__name__}: {exception}"
                    tb_lines = traceback.format_exc()
                    logger.error(f"{error_msg}\nTraceback:\n{tb_lines}")
            except Exception:
                # If logging fails, continue
                pass

    @classmethod
    def _create_conditional_method_wrapper(cls, method, class_name, method_name):
        """
        DESCRIPTION:
            Build a wrapper for a class (instance / class / static) method that:
              * Always preserves original method signature (__name__, __doc__, etc.).
              * At call time checks the session flag (cls._prf_time_flag):
                  - If PRF_TIME enabled: logs start/end (or failure) with elapsed wall time in seconds
                    using logger.prf_time().
                  - If PRF_TIME disabled: directly invokes the original method (single if branch cost).
              * On any exception (other than ones logging themselves) logs a formatted traceback via
                _log_exception_helper(), then re-raises to preserve original behavior.
            This keeps non‑PRF_TIME overhead to a single cheap conditional while still giving rich
            timing diagnostics when enabled.

        PARAMETERS:
            method:
                Required Argument.
                Specifies the method to wrap.
                Types: Callable

            class_name:
                Required Argument.
                Specifies the name of the class containing the method.
                Types: str

            method_name:
                Required Argument.
                Specifies the name of the method to wrap.
                Types: str

        RETURNS:
            Callable
                A conditional wrapper that switches between timing and direct execution.

        RAISES:
            None

        EXAMPLES:
            >>> wrapped = TeradataMlLogger._create_conditional_method_wrapper(method, "MyClass", "my_method")
        """
        
        # Use functools.wraps for standard attribute preservation
        @functools.wraps(method)
        def conditional_wrapper(*args, **kwargs):
            try:
                # Runtime check: if PRF_TIME flag enabled, add timing, else call method directly
                if cls._prf_time_flag:
                    # Add timing for PRF_TIME level
                    logger = TeradataMlLogger.get_logger()
                    method_signature = f"{class_name}.{method_name}"
                    
                    logger.prf_time(f"Started {method_signature}")
                    start_time = time.perf_counter()
                    
                    try:
                        result = method(*args, **kwargs)
                        elapsed = time.perf_counter() - start_time
                        logger.prf_time(f"Completed {method_signature} in {elapsed:.5f} secs")
                        return result
                    except Exception as e:
                        elapsed = time.perf_counter() - start_time
                        logger.prf_time(f"Failed {method_signature} in {elapsed:.5f} secs")
                        raise
                else:
                    # Direct method call
                    return method(*args, **kwargs)
            except Exception as e:
                # Automatic exception logging for all decorated methods
                cls._log_exception_helper(e, f"{class_name}.{method_name}()")
                # Re-raise the exception to maintain normal behavior so its visible to caller
                raise
        
        return conditional_wrapper


# Global convenience function for backward compatibility
def get_td_logger():
    """
    DESCRIPTION:
        Get the teradataml session logger (convenience function).

    PARAMETERS:
        None

    RETURNS:
        _TeradataMlLogger or _NullLogger
            The TeradataML logger instance or null logger if NONE level.

    RAISES:
        None

    EXAMPLES:
        >>> logger = get_td_logger()
        >>> logger.info("Using convenience function")
    """
    return TeradataMlLogger.get_logger()
