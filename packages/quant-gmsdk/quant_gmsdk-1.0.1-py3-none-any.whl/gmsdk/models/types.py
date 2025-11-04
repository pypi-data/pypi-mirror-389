"""
Data types and enums for the GM SDK.
"""

from enum import Enum
from typing import Optional, Union, List, Dict, Any


class Frequency(Enum):
    """Data frequency enumeration."""
    TICK = 'tick'
    SECOND = '1s'
    MINUTE = '1m'
    FIVE_MINUTES = '5m'
    FIFTEEN_MINUTES = '15m'
    THIRTY_MINUTES = '30m'
    HOUR = '1h'
    FOUR_HOURS = '4h'
    DAY = '1d'
    WEEK = '1w'
    MONTH = '1M'
    QUARTER = '1Q'
    YEAR = '1Y'


class AdjustType(Enum):
    """Price adjustment type enumeration."""
    NONE = 'none'
    PREV_CLOSE = 'prev_close'
    POST = 'post'
    SPOT = 'spot'
    FORWARD = 'forward'


class SecurityType(Enum):
    """Security type enumeration."""
    STOCK = 'stock'
    FUND = 'fund'
    BOND = 'bond'
    INDEX = 'index'
    FUTURES = 'futures'
    OPTIONS = 'options'
    SPOT = 'spot'
    CONVERTIBLE_BOND = 'convertible_bond'
    ETF = 'etf'
    LOF = 'lof'
    REPO = 'repo'


class Exchange(Enum):
    """Exchange enumeration."""
    SHSE = 'SHSE'  # Shanghai Stock Exchange
    SZSE = 'SZSE'  # Shenzhen Stock Exchange
    CFFEX = 'CFFEX'  # China Financial Futures Exchange
    SHFE = 'SHFE'  # Shanghai Futures Exchange
    DCE = 'DCE'  # Dalian Commodity Exchange
    CZCE = 'CZCE'  # Zhengzhou Commodity Exchange
    INE = 'INE'  # Shanghai International Energy Exchange


class UniverseType(Enum):
    """Universe type enumeration."""
    CUSTOM = 'custom'
    INDEX = 'index'
    SECTOR = 'sector'
    INDUSTRY = 'industry'
    CONCEPT = 'concept'


class DataField:
    """Common data field constants."""
    
    # Price fields
    OPEN = 'open'
    HIGH = 'high'
    LOW = 'low'
    CLOSE = 'close'
    VOLUME = 'volume'
    AMOUNT = 'amount'
    TURNOVER = 'turnover'
    
    # Fundamental fields
    MARKET_CAP = 'market_cap'
    PE_RATIO = 'pe_ratio'
    PB_RATIO = 'pb_ratio'
    PS_RATIO = 'ps_ratio'
    DIVIDEND_YIELD = 'dividend_yield'
    ROE = 'roe'
    ROA = 'roa'
    DEBT_RATIO = 'debt_ratio'
    CURRENT_RATIO = 'current_ratio'
    QUICK_RATIO = 'quick_ratio'
    
    # Symbol information
    SYMBOL = 'symbol'
    SEC_NAME = 'sec_name'
    SEC_TYPE = 'sec_type'
    EXCHANGE = 'exchange'
    LIST_DATE = 'list_date'
    DELIST_DATE = 'delist_date'
    
    # Trading information
    TRADE_DATE = 'trade_date'
    TRADE_TIME = 'trade_time'
    PRE_CLOSE = 'pre_close'
    CHANGE = 'change'
    CHANGE_PCT = 'change_pct'
    TURNOVER_RATE = 'turnover_rate'
    AMPLITUDE = 'amplitude'
    VOLATILITY = 'volatility'


class QueryConfig:
    """Configuration for query operations."""
    
    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_compression: bool = True,
        compression_level: int = 3
    ):
        """
        Initialize query configuration.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            enable_compression: Whether to enable compression
            compression_level: Compression level (1-22)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.enable_compression = enable_compression
        self.compression_level = compression_level