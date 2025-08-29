"""
Centralized logging configuration for AWS Chatbot
Structured logging with different levels and formatters
"""

import logging
import sys
from datetime import datetime
from decouple import config
import json
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Create colored log message
        log_message = (
            f"{color}[{timestamp}] "
            f"{record.levelname:8} "
            f"{record.name}:{record.lineno} "
            f"- {record.getMessage()}{reset}"
        )
        
        return log_message

def setup_logger(name: str, extra_fields: Dict[str, Any] = None) -> logging.Logger:
    """
    Setup logger with appropriate handlers and formatters
    
    Args:
        name: Logger name (usually __name__)
        extra_fields: Additional fields to include in logs
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Get configuration
    log_level = config("LOG_LEVEL", default="INFO").upper()
    log_format = config("LOG_FORMAT", default="console")  # console or json
    debug_mode = config("DEBUG", default=False, cast=bool)
    
    # Set log level
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Choose formatter based on configuration
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        if debug_mode:
            formatter = ColoredFormatter()
        else:
            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for production
    if not debug_mode:
        file_handler = logging.FileHandler('app.log')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    # Add extra fields as a filter
    if extra_fields:
        def add_extra_fields(record):
            for key, value in extra_fields.items():
                setattr(record, key, value)
            return True
        
        logger.addFilter(add_extra_fields)
    
    return logger

def log_aws_operation(logger: logging.Logger, 
                     operation: str, 
                     service: str, 
                     resource_id: str = None,
                     status: str = "started",
                     extra_data: Dict[str, Any] = None):
    """
    Log AWS operations with structured data
    
    Args:
        logger: Logger instance
        operation: Operation type (create, read, update, delete)
        service: AWS service name
        resource_id: AWS resource identifier
        status: Operation status (started, success, error)
        extra_data: Additional data to log
    """
    log_data = {
        "operation": operation,
        "aws_service": service,
        "resource_id": resource_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    message = f"AWS {service.upper()} {operation} - {status}"
    
    if status == "error":
        logger.error(message, extra=log_data)
    elif status == "success":
        logger.info(message, extra=log_data)
    else:
        logger.debug(message, extra=log_data)

def log_security_event(logger: logging.Logger,
                      event_type: str,
                      user_id: str = None,
                      ip_address: str = None,
                      details: Dict[str, Any] = None):
    """
    Log security events with enhanced tracking
    
    Args:
        logger: Logger instance
        event_type: Type of security event
        user_id: User identifier
        ip_address: Client IP address
        details: Additional security details
    """
    log_data = {
        "security_event": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    message = f"Security Event: {event_type}"
    logger.warning(message, extra=log_data)

# Pre-configured loggers for different components
def get_auth_logger():
    """Get logger for authentication module"""
    return setup_logger("auth", {"component": "authentication"})

def get_aws_logger():
    """Get logger for AWS operations"""
    return setup_logger("aws", {"component": "aws_services"})

def get_chat_logger():
    """Get logger for chat operations"""
    return setup_logger("chat", {"component": "chat_engine"})

def get_security_logger():
    """Get logger for security events"""
    return setup_logger("security", {"component": "security"})

def get_aws_logger():
    """Get AWS service-specific logger"""
    return setup_logger("aws_services", {"component": "aws_services"})

# Export main logger setup function
__all__ = ["setup_logger", "log_aws_operation", "log_security_event", 
           "get_auth_logger", "get_aws_logger", "get_chat_logger", "get_security_logger"]
