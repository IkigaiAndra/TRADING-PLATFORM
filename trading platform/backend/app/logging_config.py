"""Structured logging configuration"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add component name (logger name)
        log_record['component'] = record.name
        
        # Add context if available
        if hasattr(record, 'context'):
            log_record['context'] = record.context
        
        # Add stack trace for errors
        if record.exc_info:
            log_record['stack_trace'] = self.formatException(record.exc_info)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application"""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set JSON formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(component)s %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add context to log record"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        if 'context' in kwargs:
            kwargs['extra']['context'] = kwargs.pop('context')
        
        return msg, kwargs
