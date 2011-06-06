"""Cement core log module."""

import logging
from zope import interface

from cement2.core import exc, util
        
def log_handler_invariant(obj):
    invalid = []
    members = [
        '__handler_label__',
        '__handler_type__',
        'setup',
        'clear_loggers',
        'set_level',
        'level',
        'info', 
        'warn',
        'error', 
        'fatal', 
        'debug', 
        ]
        
    for member in members:
        if not hasattr(obj, member):
            invalid.append(member)
    
    if invalid:
        raise exc.CementInterfaceError, \
            "Invalid or missing: %s in %s" % (invalid, obj)
            
class ILogHandler(interface.Interface):
    """
    This class defines the Log Handler Interface.  Classes that 
    implement this handler must provide the methods and attributes defined 
    below.
        
    """
    # internal mechanism for handler registration
    __handler_type__ = interface.Attribute('Handler Type Identifier')
    __handler_label__ = interface.Attribute('Handler Label Identifier')
    interface.invariant(log_handler_invariant)
    
    def setup(config_obj):
        """
        The setup function is called during application initialization and
        must 'setup' the handler object making it ready for the framework
        or the application to make further calls to it.
        
        Required Arguments:
        
            config_obj
                The application configuration object.  This is a config object 
                that implements the IConfigHandler interface and not a config 
                dictionary, though some config handler implementations may 
                also function like a dict (i.e. configobj).
                
        Returns: n/a
        
        """
        
    def clear_loggers():
        """
        Clear all existing loggers.
        
        """
        
    def set_level(self):
        """
        Set the log level.  Must except one of: 'INFO', 'WARN', 'ERROR', 
        'DEBUG', or 'FATAL'.
        
        """
        
    def level(self):
        """
        Return a string representation of the log level.
        """
    
    def info(self, msg):
        """
        Log to the 'INFO' facility.
        
        Required Arguments:
        
            msg
                The message to log.
        
        """
        
    def warn(self, msg):
        """
        Log to the 'WARN' facility.
        
        Required Arguments:
        
            msg
                The message to log.
        
        """
    
    def error(self, msg):
        """
        Log to the 'ERROR' facility.
        
        Required Arguments:
        
            msg
                The message to log.
        
        """
    
    def fatal(self, msg):
        """
        Log to the 'FATAL' facility.
        
        Required Arguments:
        
            msg
                The message to log.
        
        """
    
    def debug(self, msg):
        """
        Log to the 'DEBUG' facility.
        
        Required Arguments:
        
            msg
                The message to log.
        
        """
        
        
class LoggingLogHandler(object):  
    __handler_type__ = 'log'
    __handler_label__ = 'logging'
    interface.implements(ILogHandler)
    levels = ['INFO', 'WARN', 'ERROR', 'DEBUG', 'FATAL']

    def __init__(self, **kw):
        """
        This is an implementation of the ILogHandler interface, and sets up the 
        logging facility using the standard 'logging' module.

        Optional Arguments:
        
            config
                The application configuration object.
                
            namespace
                The logging namespace.  Default: application name.
                
            backend
                The logging backend.  Default: logging.getLogger().
            
            file
                The log file path. Default: None.
                
            to_console
                Whether to log to the console.  Default: True.
            
            rotate
                Whether to rotate the log file.  Default: False.
            
            max_bytes
                The number of bytes at which to rotate the log file.
                Default: 512000.
            
            max_files
                The max number of files to keep when rotation the log file.
                Default: 4
                
            file_formatter
                The logging formatter to use for the log file.
                
            console_formatter
                The logging formatter to use for the console output.
                
            debug_formatter
                The logging formatter to use for debug output.
                
            clear_loggers
                Whether or not to clear previous loggers first.  
                Default: False.
               
            level
                The level to log at.  Must be one of ['INFO', 'WARN', 'ERROR', 
                'DEBUG', 'FATAL'].  Default: INFO.
                
        The following configuration options are recognized in this class:
        
            base.app_name
            base.debug
            log.file
            log.to_console
            log.rotate
            log.max_bytes
            log.max_files
            log.clear_loggers
            
        """  
        self.config = kw.get('config', None)
        self.namespace = kw.get('namespace', None)
        self.backend = kw.get('backend', None)
        self.file = kw.get('file', None)
        self.to_console = kw.get('to_console', None)
        self.rotate = kw.get('rotate', None)
        self.max_bytes = kw.get('max_bytes', None)
        self.max_files = kw.get('max_files', None)
        self.file_formatter = kw.get('file_formatter', None)
        self.console_formatter = kw.get('console_formatter', None)
        self.debug_formatter = kw.get('debug_formatter', None)
        self._clear_loggers = kw.get('clear_loggers', None)
        self._level = kw.get('level', None)
        
    def setup(self, config_obj):
        self.config = config_obj
        
        # first handle anything passed to __init__, fall back on config.
        if self.namespace is None:
            self.namespace = self.config.get('base', 'app_name')
        if self.backend is None:
            self.backend = logging.getLogger(self.namespace)
        if self.file is None:
            self.file = self.config.get('log', 'file')
        if self.to_console is None:
            self.to_console = self.config.get('log', 'to_console')
        if self.rotate is None:
            self.rotate = self.config.get('log', 'rotate')
        if self.max_bytes is None:
            self.max_bytes = self.config.get('log', 'max_bytes')
        if self.max_files is None:
            self.max_files = self.config.get('log', 'max_files')
        if self.file_formatter is None:
            format_str = "%(asctime)s (%(levelname)s) %(name)s : %(message)s"
            self.file_formatter = logging.Formatter(format_str)
        if self.console_formatter is None:
            format_str = "%(levelname)s: %(message)s"
            self.console_formatter = logging.Formatter(format_str)
        if self.debug_formatter is None:
            format_str = "%(asctime)s (%(levelname)s) %(name)s : %(message)s"
            self.debug_formatter = logging.Formatter(format_str)
        if self._clear_loggers is None:
            self._clear_loggers = self.config.get('log', 'clear_loggers')
        if self._level is None:
            level = self.config.get('log', 'level').upper()
            if level not in self.levels:
                level = 'INFO'

        # the king trumps all
        if util.is_true(self.config.get('base', 'debug')):
            level = 'DEBUG'
            
        self.set_level(level)
        
        # clear loggers?
        if util.is_true(self._clear_loggers):
            self.clear_loggers()
            
        # console
        if util.is_true(self.to_console):
            self._setup_console_log()
        
        # file
        if self.file:
            self._setup_file_log()
            
        self.debug("logging initialized for '%s' using LoggingLogHandler" % \
                   self.namespace)
                 
    def set_level(self, level):
        if level not in self.levels:
            level = 'INFO'
        level = getattr(logging, level.upper())
        
        self.backend.setLevel(level)  
        
        for handler in logging.getLogger(self.namespace).handlers:
            handler.setLevel(level)
            
    def clear_loggers(self):
        if not self.namespace:
            # setup() probably wasn't run
            return
            
        for i in logging.getLogger(self.namespace).handlers:
            logging.getLogger(self.namespace).removeHandler(i)
            self.backend = logging.getLogger(self.namespace)
    
    def _setup_console_log(self):
        console_handler = logging.StreamHandler()
        if self.level() == logging.getLevelName(logging.DEBUG):
            console_handler.setFormatter(self.debug_formatter)
        else:
            console_handler.setFormatter(self.console_formatter)
            
        console_handler.setLevel(getattr(logging, self.level()))   
        self.backend.addHandler(console_handler)
    
    def _setup_file_log(self):
        if self.rotate:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                path, 
                maxBytes=int(self.max_bytes), 
                backupCount=int(self.max_files),
                )
        else:
            from logging import FileHandler
            file_handler = FileHandler(self.file)
        
        if self.level() == logging.getLevelName(logging.DEBUG):
            file_handler.setFormatter(self.debug_formatter)
        else:
            file_handler.setFormatter(self.file_formatter)
            
        file_handler.setLevel(getattr(logging, self.level())) 
        self.backend.addHandler(file_handler)
        
    def level(self):
        return logging.getLevelName(self.backend.level)
    
    def info(self, msg):
        self.backend.info(msg)
        
    def warn(self, msg):
        self.backend.warn(msg)
    
    def error(self, msg):
        self.backend.error(msg)
    
    def fatal(self, msg):
        self.backend.fatal(msg)
    
    def debug(self, msg):
        self.backend.debug(msg)
        