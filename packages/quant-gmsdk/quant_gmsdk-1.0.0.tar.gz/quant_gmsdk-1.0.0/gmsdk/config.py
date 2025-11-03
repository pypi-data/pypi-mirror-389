"""
Configuration management for the GM SDK.
"""

import os
from typing import Optional, Dict, Any
from .models.types import QueryConfig
from .models.exceptions import ConfigurationError


class Config:
    """Configuration management class."""
    
    def __init__(
        self,
        server_host: str = 'localhost',
        server_port: int = 50051,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_compression: bool = True,
        compression_level: int = 3,
        log_level: str = 'INFO',
        log_file: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration.
        
        Args:
            server_host: Server host address
            server_port: Server port
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            enable_compression: Whether to enable compression
            compression_level: Compression level (1-22)
            log_level: Logging level
            log_file: Optional log file path
            **kwargs: Additional configuration parameters
        """
        self.server_host = server_host
        self.server_port = server_port
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_compression = enable_compression
        self.compression_level = compression_level
        self.log_level = log_level
        self.log_file = log_file
        self.extra_config = kwargs
    
    @property
    def server_address(self) -> str:
        """Get server address string."""
        return f"{self.server_host}:{self.server_port}"
    
    def to_query_config(self) -> QueryConfig:
        """Convert to QueryConfig object."""
        return QueryConfig(
            timeout=self.timeout,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            enable_compression=self.enable_compression,
            compression_level=self.compression_level
        )
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Create configuration from environment variables.
        
        Returns:
            Configuration object
        """
        config = {
            'server_host': os.getenv('GM_SERVER_HOST', 'localhost'),
            'server_port': int(os.getenv('GM_SERVER_PORT', '50051')),
            'timeout': int(os.getenv('GM_TIMEOUT', '30')),
            'max_retries': int(os.getenv('GM_MAX_RETRIES', '3')),
            'retry_delay': float(os.getenv('GM_RETRY_DELAY', '1.0')),
            'enable_compression': os.getenv('GM_ENABLE_COMPRESSION', 'true').lower() == 'true',
            'compression_level': int(os.getenv('GM_COMPRESSION_LEVEL', '3')),
            'log_level': os.getenv('GM_LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('GM_LOG_FILE')
        }
        
        # Filter out None values
        config = {k: v for k, v in config.items() if v is not None}
        
        return cls(**config)
    
    def update(self, **kwargs) -> None:
        """
        Update configuration parameters.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.extra_config[key] = value
    
    def validate(self) -> None:
        """
        Validate configuration parameters.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not isinstance(self.server_host, str) or not self.server_host:
            raise ConfigurationError("Server host must be a non-empty string")
        
        if not isinstance(self.server_port, int) or not (1 <= self.server_port <= 65535):
            raise ConfigurationError("Server port must be an integer between 1 and 65535")
        
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ConfigurationError("Timeout must be a positive integer")
        
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ConfigurationError("Max retries must be a non-negative integer")
        
        if not isinstance(self.retry_delay, (int, float)) or self.retry_delay < 0:
            raise ConfigurationError("Retry delay must be a non-negative number")
        
        if not isinstance(self.enable_compression, bool):
            raise ConfigurationError("Enable compression must be a boolean")
        
        if not isinstance(self.compression_level, int) or not (1 <= self.compression_level <= 22):
            raise ConfigurationError("Compression level must be an integer between 1 and 22")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        config_dict = {
            'server_host': self.server_host,
            'server_port': self.server_port,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'enable_compression': self.enable_compression,
            'compression_level': self.compression_level,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
        config_dict.update(self.extra_config)
        return config_dict