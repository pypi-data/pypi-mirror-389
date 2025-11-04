"""
GM SDK - Pure Python SDK for quantitative trading.

This SDK provides a pure Python implementation of the GM quantitative trading platform
API, using gRPC for communication with a proxy server.
"""
__version__ = "1.0.0"
__author__ = "nirvana0614"
__email__ = "nirvana0614@users.noreply.gitee.com"

import traceback

import pandas as pd
from typing import Optional, List, Union, Dict, Any
import logging
import json
import pickle
import datetime

from .client import GMClient
from .config import Config
from .models.types import Frequency, AdjustType, SecurityType, Exchange, DataField
from .models.exceptions import GMError, ConnectionError, QueryError
from .utils.logging import setup_logger, get_logger
from .proto import gm_service_pb2

# Setup default logger
setup_logger('gmsdk', level=logging.INFO)
logger = get_logger(__name__)

# Global client instance
_client: Optional[GMClient] = None
_config: Optional[Config] = None


def initialize(
    server_host: str = 'localhost',
    server_port: int = 50051,
    token: Optional[str] = None,
    **kwargs
) -> None:
    """
    Initialize the GM SDK.
    
    Args:
        server_host: Server host address
        server_port: Server port
        token: Authentication token
        **kwargs: Additional configuration options
    """
    global _client, _config
    
    try:
        # Create configuration
        _config = Config(
            server_host=server_host,
            server_port=server_port,
            **kwargs
        )
        
        # Create client
        _client = GMClient(_config.server_address, _config.to_query_config())
        _client.connect()
        
        logger.info(f"GM SDK initialized successfully, connected to {_config.server_address}")
        
    except Exception as e:
        logger.error(f"Failed to initialize GM SDK: {e}")
        raise GMError(f"Failed to initialize GM SDK: {e}")


def is_initialized() -> bool:
    """
    Check if the SDK is initialized.
    
    Returns:
        True if initialized
    """
    return _client is not None and _client.is_connected()


def _ensure_initialized() -> None:
    """Ensure the SDK is initialized."""
    if not is_initialized():
        raise GMError("GM SDK not initialized. Call initialize() first.")


def _parse_datetime_columns_by_fields(df: pd.DataFrame, dt_fields: list) -> pd.DataFrame:
    """
    根据dt_fields列表解析DataFrame中的datetime列，将ISO格式字符串转换为datetime类型

    Args:
        df: 输入的DataFrame
        dt_fields: datetime字段名列表

    Returns:
        解析后的DataFrame
    """
    if df.empty or not dt_fields:
        return df

    for column in dt_fields:
        if column in df.columns and df[column].dtype == 'object':
            try:
                # 使用pandas的自动推断功能，这能处理ISO格式和其他常见格式
                df[column] = pd.to_datetime(df[column], errors='coerce')
                # 将datetime64[ns, UTC] 转成 datetime64[ns, Asia/Shanghai]
                df[column] = df[column].dt.tz_convert('Asia/Shanghai')
            except Exception:
                # 如果解析失败，保持原样
                traceback.print_exc()
                pass

    return df




def _deserialize_response_data(response, df: bool = True) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any], List[str], str]:
    """
    根据Response的data_type和serialize_type进行data字段的反序列化处理

    Args:
        response: gRPC响应对象
        df: 是否返回DataFrame格式（与请求中的df参数一致）

    Returns:
        反序列化后的数据
    """
    if response.error:
        raise QueryError(f"Query failed: {response.error}")

    # 如果data字段为空，返回相应的空值
    if not response.data:
        if df:
            return pd.DataFrame()
        elif response.data_type == gm_service_pb2.JSON_TYPE:
            return []
        else:
            return {}

    # 根据data_type和serialize_type进行反序列化
    if response.data_type == gm_service_pb2.JSON_TYPE:
        # JSON类型数据
        json_str = response.data.decode('utf-8')
        parsed_data = json.loads(json_str)

        if df:
            # 请求df=True但返回的是JSON类型，转换为DataFrame
            if isinstance(parsed_data, list):
                df_result = pd.DataFrame(parsed_data)
                # 根据dt_fields解析datetime字段
                if hasattr(response, 'dt_fields'):
                    df_result = _parse_datetime_columns_by_fields(df_result, list(response.dt_fields))
                return df_result
            elif isinstance(parsed_data, dict):
                df_result = pd.DataFrame([parsed_data])
                # 根据dt_fields解析datetime字段
                if hasattr(response, 'dt_fields'):
                    df_result = _parse_datetime_columns_by_fields(df_result, list(response.dt_fields))
                return df_result
            else:
                return pd.DataFrame()
        else:
            # 请求df=False，直接返回解析后的JSON数据
            return parsed_data

    elif response.data_type == gm_service_pb2.DF_TYPE:
        # DataFrame类型数据
        if response.serialize_type == gm_service_pb2.PICKLE_SERIALIZE:
            # 使用pickle反序列化
            df_result = pickle.loads(response.data)

            if not df_result.empty:
                return df_result
            else:
                return pd.DataFrame()

        elif response.serialize_type == gm_service_pb2.JSON_SERIALIZE:
            # 使用JSON反序列化
            json_str = response.data.decode('utf-8')
            parsed_data = json.loads(json_str)

            if df:
                # 请求df=True，根据dt_fields处理datetime字段的解析
                if isinstance(parsed_data, list):
                    df_result = pd.DataFrame(parsed_data)
                    # 根据dt_fields解析datetime字段
                    if hasattr(response, 'dt_fields'):
                        df_result = _parse_datetime_columns_by_fields(df_result, list(response.dt_fields))
                    return df_result
                elif isinstance(parsed_data, dict):
                    df_result = pd.DataFrame([parsed_data])
                    # 根据dt_fields解析datetime字段
                    if hasattr(response, 'dt_fields'):
                        df_result = _parse_datetime_columns_by_fields(df_result, list(response.dt_fields))
                    return df_result
                else:
                    return pd.DataFrame()
            else:
                # 请求df=False但返回的是DataFrame类型，返回解析后的JSON数据
                return parsed_data
        else:
            raise QueryError(f"Unsupported serialize_type: {response.serialize_type}")
    else:
        raise QueryError(f"Unsupported data_type: {response.data_type}")


def get_fundamentals(
    table: str,
    symbols: Union[str, List[str]],
    start_date: Union[str, datetime.datetime, datetime.date],
    end_date: Union[str, datetime.datetime, datetime.date],
    fields: Optional[Union[str, List[str]]] = None,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 1000,
    df: bool = False
) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Get fundamental data.

    Args:
        table: Table name
        symbols: List of symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        fields: List of fields to retrieve
        df: Return as DataFrame

    Returns:
        Fundamental data
    """
    _ensure_initialized()

    try:
        # 参数类型转换，与原始SDK保持一致
        # symbols: 支持str或list，转换为列表
        if isinstance(symbols, str):
            symbols_list = [symbols]
        else:
            symbols_list = list(symbols) if symbols else []

        # start_time, end_time: 支持str、datetime、date，转换为字符串
        start_date_str = ''
        if start_date is not None:
            if isinstance(start_date, (datetime.datetime, datetime.date)):
                start_date_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime.date) else start_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_date_str = str(start_date)

        end_date_str = ''
        if end_date is not None:
            if isinstance(end_date, (datetime.datetime, datetime.date)):
                end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime.date) else end_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                end_date_str = str(end_date)

        # fields: 转换为列表格式
        fields_list = []
        if fields is not None:
            if isinstance(fields, str):
                fields_list = [f.strip() for f in fields.split(',') if f.strip()]
            else:
                fields_list = fields if fields else []

        request = gm_service_pb2.GetFundamentalsRequest(
            table=table,
            symbols=symbols_list,
            start_date=start_date_str,
            end_date=end_date_str,
            fields=fields_list,
            filter=filter or '',
            order_by=order_by or '',
            limit=limit,
            df=df
        )

        response = _client.get_fundamentals(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)

    except Exception as e:
        logger.error(f"Error getting fundamentals: {e}")
        raise


def history(
    symbol: Union[str, List[str]],
    frequency: str,
    start_time: Union[str, datetime.datetime, datetime.date],
    end_time: Union[str, datetime.datetime, datetime.date],
    fields: Optional[str] = None,
    skip_suspended: bool = True,
    fill_missing: Optional[str] = None,
    adjust: Optional[int] = None,
    adjust_end_time: str = '',
    df: bool = False
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """
    Get historical data.

    Args:
        symbol: Symbol or list of symbols
        frequency: Data frequency (e.g., '1d', '60s')
        start_time: Start time (YYYY-MM-DD HH:MM:SS)
        end_time: End time (YYYY-MM-DD HH:MM:SS)
        fields: Fields to retrieve (string format)
        skip_suspended: Skip suspended trading days
        fill_missing: Fill missing data method
        adjust: Price adjustment (None=original, 0=none, 1=forward, 2=backward)
        adjust_end_time: Adjustment end time
        df: Return as DataFrame

    Returns:
        Historical data as List[Dict] or DataFrame
    """
    _ensure_initialized()

    try:
        # 参数类型转换，与原始SDK保持一致
        # symbol: 支持str或list，转换为逗号分隔的字符串
        if isinstance(symbol, list):
            symbol_str = ','.join(symbol)
        else:
            symbol_str = str(symbol)

        # start_time, end_time: 支持str、datetime、date，转换为字符串
        start_time_str = ''
        if start_time is not None:
            if isinstance(start_time, (datetime.datetime, datetime.date)):
                start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(start_time, datetime.datetime) else start_time.strftime('%Y-%m-%d')
            else:
                start_time_str = str(start_time)

        end_time_str = ''
        if end_time is not None:
            if isinstance(end_time, (datetime.datetime, datetime.date)):
                end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(end_time, datetime.datetime) else end_time.strftime('%Y-%m-%d')
            else:
                end_time_str = str(end_time)

        # fields: 转换为列表格式
        fields_list = []
        if fields is not None:
            if isinstance(fields, str):
                fields_list = [f.strip() for f in fields.split(',') if f.strip()]
            else:
                fields_list = fields if fields else []

        # adjust: None转换为0
        adjust_value = adjust if adjust is not None else 0

        # fill_missing: None转换为空字符串
        fill_missing_str = fill_missing if fill_missing is not None else ''

        request = gm_service_pb2.HistoryRequest(
            symbol=symbol_str,
            frequency=frequency,
            start_time=start_time_str,
            end_time=end_time_str,
            fields=fields_list,
            df=df,
            adjust=adjust_value,
            skip_suspended=skip_suspended,
            fill_missing=fill_missing_str,
            adjust_end_time=adjust_end_time
        )
        
        response = _client.history(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise


def get_instruments(
    symbols: Optional[List[str]] = None,
    exchanges: Optional[List[str]] = None,
    sec_types: Optional[List[str]] = None,
    names: Optional[List[str]] = None,
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get instruments data.
    
    Args:
        symbols: List of symbols
        exchanges: List of exchanges
        sec_types: List of security types
        names: List of names
        fields: List of fields to retrieve
        df: Return as DataFrame
        
    Returns:
        Instruments data
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.GetInstrumentsRequest(
            symbols=symbols or [],
            exchanges=exchanges or [],
            sec_types=sec_types or [],
            names=names or [],
            fields=fields or [],
            df=df
        )
        
        response = _client.get_instruments(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        raise


def get_trading_dates(
    exchange: str,
    start_date: str,
    end_date: str
) -> List[str]:
    """
    Get trading dates.

    Args:
        exchange: Exchange code
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of trading dates
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetTradingDatesRequest(
            exchange=exchange,
            start_date=start_date,
            end_date=end_date
        )

        response = _client.get_trading_dates(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # GetTradingDatesResponse返回日期列表，不需要反序列化
        return list(response.dates)

    except Exception as e:
        logger.error(f"Error getting trading dates: {e}")
        raise


def get_history_l2ticks(
    symbol: str,
    start_time: str,
    end_time: str,
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 tick data.
    
    Args:
        symbol: Symbol
        start_time: Start time
        end_time: End time
        fields: List of fields to retrieve
        df: Return as DataFrame
        
    Returns:
        Level 2 tick data
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.GetHistoryL2TicksRequest(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            fields=fields or [],
            df=df
        )
        
        response = _client.get_history_l2ticks(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting Level 2 ticks: {e}")
        raise


def get_history_l2bars(
    symbol: str,
    frequency: str,
    start_time: str,
    end_time: str,
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 bar data.
    
    Args:
        symbol: Symbol
        frequency: Data frequency
        start_time: Start time
        end_time: End time
        fields: List of fields to retrieve
        df: Return as DataFrame
        
    Returns:
        Level 2 bar data
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.GetHistoryL2BarsRequest(
            symbol=symbol,
            frequency=frequency,
            start_time=start_time,
            end_time=end_time,
            fields=fields or [],
            df=df
        )
        
        response = _client.get_history_l2bars(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting Level 2 bars: {e}")
        raise


def get_dividend(
    symbol: str,
    start_date: str,
    end_date: str,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get dividend data.

    Args:
        symbol: Symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        df: Return as DataFrame

    Returns:
        Dividend data
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetDividendRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            df=df
        )
        
        response = _client.get_dividend(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting dividend: {e}")
        raise


def get_continuous_contracts(
    symbol: str,
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get continuous contracts.
    
    Args:
        symbol: Symbol
        fields: List of fields to retrieve
        df: Return as DataFrame
        
    Returns:
        Continuous contracts
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.GetContinuousContractsRequest(
            symbol=symbol,
            fields=fields or [],
            df=df
        )
        
        response = _client.get_continuous_contracts(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting continuous contracts: {e}")
        raise


def get_constituents(
    index: str,
    date: str,
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get index constituents.
    
    Args:
        index: Index symbol
        date: Date (YYYY-MM-DD)
        fields: List of fields to retrieve
        df: Return as DataFrame
        
    Returns:
        Index constituents
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.GetConstituentsRequest(
            index=index,
            date=date,
            fields=fields or [],
            df=df
        )
        
        response = _client.get_constituents(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)
        
    except Exception as e:
        logger.error(f"Error getting constituents: {e}")
        raise


def get_sector(
    code: str
) -> List[str]:
    """
    Get sector symbols by code.

    Args:
        code: Sector code

    Returns:
        List of symbols in the sector
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetSectorRequest(
            code=code
        )

        response = _client.get_sector(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # GetSectorResponse返回股票列表，不需要反序列化
        return list(response.symbols)

    except Exception as e:
        logger.error(f"Error getting sector: {e}")
        raise


def get_industry(
    code: str
) -> List[str]:
    """
    Get industry symbols by code.

    Args:
        code: Industry code

    Returns:
        List of symbols in the industry
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetIndustryRequest(
            code=code
        )

        response = _client.get_industry(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # GetIndustryResponse返回股票列表，不需要反序列化
        return list(response.symbols)

    except Exception as e:
        logger.error(f"Error getting industry: {e}")
        raise


def get_concept(
    code: str
) -> List[str]:
    """
    Get concept symbols by code.

    Args:
        code: Concept code

    Returns:
        List of symbols in the concept
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetConceptRequest(
            code=code
        )

        response = _client.get_concept(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # GetConceptResponse返回股票列表，不需要反序列化
        return list(response.symbols)

    except Exception as e:
        logger.error(f"Error getting concept: {e}")
        raise


def get_variety_infos(
    variety_names: List[str],
    fields: Optional[List[str]] = None,
    df: bool = True
) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get variety information.

    Args:
        variety_names: List of variety names
        fields: List of fields to retrieve
        df: Return as DataFrame

    Returns:
        Variety information
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetVarietyInfosRequest(
            variety_names=variety_names,
            fields=fields or [],
            df=df
        )

        response = _client.get_variety_infos(request)

        # 使用新的反序列化函数
        return _deserialize_response_data(response, df)

    except Exception as e:
        logger.error(f"Error getting variety infos: {e}")
        raise


def get_trading_times(
    variety_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Get trading times.

    Args:
        variety_names: List of variety names

    Returns:
        Trading times
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetTradingTimesRequest(
            variety_names=variety_names
        )

        response = _client.get_trading_times(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 使用新的反序列化函数（df=False，返回JSON格式）
        return _deserialize_response_data(response, df=False)

    except Exception as e:
        logger.error(f"Error getting trading times: {e}")
        raise


def current(
    symbols: Union[str, List[str]],
    fields: Optional[Union[str, List[str]]] = None,
    include_call_auction: bool = False
) -> List[Dict[str, Any]]:
    """
    查询当前行情快照，返回tick数据。

    Args:
        symbols: 股票代码，支持单个代码或代码列表
        fields: 需要返回的字段列表，为空则返回所有字段
        include_call_auction: 是否包含集合竞价信息

    Returns:
        List[Dict[str, Any]]: tick数据列表
    """
    _ensure_initialized()

    try:
        # 参数类型转换
        # symbols: 支持str或list，转换为列表
        if isinstance(symbols, str):
            symbols_list = [symbols]
        else:
            symbols_list = list(symbols) if symbols else []

        # fields: 转换为列表格式
        fields_list = []
        if fields is not None:
            if isinstance(fields, str):
                fields_list = [f.strip() for f in fields.split(',') if f.strip()]
            else:
                fields_list = fields if fields else []

        request = gm_service_pb2.CurrentRequest(
            symbols=symbols_list,
            fields=fields_list,
            include_call_auction=include_call_auction
        )

        response = _client.current(request)

        # 使用新的反序列化函数（df=False，返回JSON格式）
        result = _deserialize_response_data(response, df=False)

        # 确保返回列表格式
        if isinstance(result, list):
            return result
        elif result:
            return [result]
        else:
            return []  # 返回空列表

    except Exception as e:
        logger.error(f"Error getting current data: {e}")
        raise


def current_price(
    symbols: Union[str, List[str]]
) -> List[Dict[str, Any]]:
    """
    查询当前价格数据。

    Args:
        symbols: 股票代码，支持单个代码或代码列表

    Returns:
        List[Dict[str, Any]]: 价格数据列表
    """
    _ensure_initialized()

    try:
        # 参数类型转换
        # symbols: 支持str或list，转换为列表
        if isinstance(symbols, str):
            symbols_list = [symbols]
        else:
            symbols_list = list(symbols) if symbols else []

        request = gm_service_pb2.CurrentPriceRequest(
            symbols=symbols_list
        )

        response = _client.current_price(request)

        # 使用新的反序列化函数（df=False，返回JSON格式）
        result = _deserialize_response_data(response, df=False)

        # 确保返回列表格式
        if isinstance(result, list):
            return result
        elif result:
            return [result]
        else:
            return []  # 返回空列表

    except Exception as e:
        logger.error(f"Error getting current price data: {e}")
        raise


def get_cash(account_id: str) -> Dict[str, Any]:
    """
    Get cash information.

    Args:
        account_id: Account ID

    Returns:
        Cash information
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetCashRequest(account_id=account_id)

        response = _client.get_cash(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 使用新的反序列化函数（df=False，返回JSON格式）
        data = _deserialize_response_data(response, df=False)

        # 如果是列表，返回第一个元素，否则返回整个数据
        if isinstance(data, list) and data:
            return data[0]
        elif data:
            return data
        else:
            return {}  # 返回空字典

    except Exception as e:
        logger.error(f"Error getting cash: {e}")
        raise


def get_position(account_id: str) -> List[Dict[str, Any]]:
    """
    Get position information.

    Args:
        account_id: Account ID

    Returns:
        Position information
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.GetPositionRequest(account_id=account_id)

        response = _client.get_position(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 使用新的反序列化函数（df=False，返回JSON格式）
        data = _deserialize_response_data(response, df=False)

        # 确保返回列表
        if isinstance(data, list):
            return data
        elif data:
            return [data]
        else:
            return []  # 返回空列表

    except Exception as e:
        logger.error(f"Error getting position: {e}")
        raise


def universe_set(universe_name: str, symbols: List[str]) -> None:
    """
    Set universe.

    Args:
        universe_name: Universe name
        symbols: List of symbols
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.UniverseSetRequest(
            universe_name=universe_name,
            symbols=symbols
        )
        
        response = _client.universe_set(request)
        
        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 原始SDK返回None，不返回success状态

    except Exception as e:
        logger.error(f"Error setting universe: {e}")
        raise


def universe_get_symbols(universe_name: str) -> List[str]:
    """
    Get universe symbols.
    
    Args:
        universe_name: Universe name
        
    Returns:
        List of symbols
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.UniverseGetSymbolsRequest(universe_name=universe_name)
        
        response = _client.universe_get_symbols(request)
        
        if response.error:
            raise QueryError(f"Query failed: {response.error}")
        
        return list(response.symbols)
        
    except Exception as e:
        logger.error(f"Error getting universe symbols: {e}")
        raise


def universe_get_names() -> List[str]:
    """
    Get universe names.

    Returns:
        List of universe names
    """
    _ensure_initialized()

    try:
        request = gm_service_pb2.UniverseGetNamesRequest()

        response = _client.universe_get_names(request)

        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 直接返回字符串列表，与原始SDK保持一致
        if response.symbols:
            return list(response.symbols)
        else:
            return []  # 返回空列表

    except Exception as e:
        logger.error(f"Error getting universe names: {e}")
        raise


def universe_delete(universe_name: str) -> None:
    """
    Delete universe.

    Args:
        universe_name: Universe name
    """
    _ensure_initialized()
    
    try:
        request = gm_service_pb2.UniverseDeleteRequest(universe_name=universe_name)
        
        response = _client.universe_delete(request)
        
        if response.error:
            raise QueryError(f"Query failed: {response.error}")

        # 原始SDK返回None，不返回success状态

    except Exception as e:
        logger.error(f"Error deleting universe: {e}")
        raise


def close() -> None:
    """Close the SDK connection."""
    global _client
    
    try:
        if _client:
            _client.disconnect()
            _client = None
            logger.info("GM SDK connection closed")
        
    except Exception as e:
        logger.error(f"Error closing SDK connection: {e}")


# Convenience functions for backward compatibility
def history_n(symbol: str, count: int, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get historical data by count.
    
    Args:
        symbol: Symbol
        count: Number of records
        **kwargs: Additional arguments
        
    Returns:
        Historical data
    """
    # This is a convenience wrapper - actual implementation needs date calculation
    raise NotImplementedError("history_n not yet implemented")


def get_fundamentals_n(table: str, symbols: List[str], count: int, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get fundamentals data by count.
    
    Args:
        table: Table name
        symbols: List of symbols
        count: Number of records
        **kwargs: Additional arguments
        
    Returns:
        Fundamental data
    """
    # This is a convenience wrapper - actual implementation needs date calculation
    raise NotImplementedError("get_fundamentals_n not yet implemented")


def get_history_instruments(symbols: List[str], **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get historical instruments data.
    
    Args:
        symbols: List of symbols
        **kwargs: Additional arguments
        
    Returns:
        Historical instruments data
    """
    # This is a convenience wrapper - delegates to get_instruments
    return get_instruments(symbols=symbols, **kwargs)


def get_instrumentinfos(symbols: List[str], **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get detailed instrument information.
    
    Args:
        symbols: List of symbols
        **kwargs: Additional arguments
        
    Returns:
        Instrument information
    """
    # This is a convenience wrapper - delegates to get_instruments
    return get_instruments(symbols=symbols, **kwargs)


def get_previous_trading_date(date: str) -> str:
    """
    Get previous trading date.
    
    Args:
        date: Date (YYYY-MM-DD)
        
    Returns:
        Previous trading date
    """
    # This is a convenience wrapper - actual implementation needs date calculation
    raise NotImplementedError("get_previous_trading_date not yet implemented")


def get_next_trading_date(date: str) -> str:
    """
    Get next trading date.
    
    Args:
        date: Date (YYYY-MM-DD)
        
    Returns:
        Next trading date
    """
    # This is a convenience wrapper - actual implementation needs date calculation
    raise NotImplementedError("get_next_trading_date not yet implemented")


def get_history_ticks_l2(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 tick data (alternative name).
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Level 2 tick data
    """
    # This is a convenience wrapper - delegates to get_history_l2ticks
    return get_history_l2ticks(symbol=symbol, **kwargs)


def get_history_bars_l2(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 bar data (alternative name).
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Level 2 bar data
    """
    # This is a convenience wrapper - delegates to get_history_l2bars
    return get_history_l2bars(symbol=symbol, **kwargs)


def get_history_l2transactions(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 transaction data.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Level 2 transaction data
    """
    # This function is not yet implemented
    raise NotImplementedError("get_history_l2transactions not yet implemented")


def get_history_l2orders(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 order data.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Level 2 order data
    """
    # This function is not yet implemented
    raise NotImplementedError("get_history_l2orders not yet implemented")


def get_history_l2orders_queue(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get Level 2 order queue data.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Level 2 order queue data
    """
    # This function is not yet implemented
    raise NotImplementedError("get_history_l2orders_queue not yet implemented")


def option_get_symbols_by_exchange(exchange: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get option symbols by exchange.
    
    Args:
        exchange: Exchange
        **kwargs: Additional arguments
        
    Returns:
        Option symbols
    """
    # This function is not yet implemented
    raise NotImplementedError("option_get_symbols_by_exchange not yet implemented")


def option_get_symbols_by_in_at_out(in_at_out: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get option symbols by in/out of the money.
    
    Args:
        in_at_out: In/at/out of the money
        **kwargs: Additional arguments
        
    Returns:
        Option symbols
    """
    # This function is not yet implemented
    raise NotImplementedError("option_get_symbols_by_in_at_out not yet implemented")


def option_get_delisted_dates(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get option delisted dates.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Delisted dates
    """
    # This function is not yet implemented
    raise NotImplementedError("option_get_delisted_dates not yet implemented")


def option_get_exercise_prices(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get option exercise prices.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Exercise prices
    """
    # This function is not yet implemented
    raise NotImplementedError("option_get_exercise_prices not yet implemented")


def get_expire_rest_days(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get days until expiration.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Days until expiration
    """
    # This function is not yet implemented
    raise NotImplementedError("get_expire_rest_days not yet implemented")


def bond_convertible_get_call_info(symbol: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get convertible bond call information.
    
    Args:
        symbol: Symbol
        **kwargs: Additional arguments
        
    Returns:
        Call information
    """
    # This function is not yet implemented
    raise NotImplementedError("bond_convertible_get_call_info not yet implemented")


def get_history_constituents(index: str, **kwargs) -> Union[pd.DataFrame, Dict[str, Any]]:
    """
    Get historical index constituents.
    
    Args:
        index: Index symbol
        **kwargs: Additional arguments
        
    Returns:
        Historical constituents
    """
    # This function is not yet implemented
    raise NotImplementedError("get_history_constituents not yet implemented")


def raw_func(func_name: str, *args, **kwargs) -> Any:
    """
    Execute raw function.
    
    Args:
        func_name: Function name
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    # This function is not yet implemented
    raise NotImplementedError("raw_func not yet implemented")


# Export all public functions and classes
__all__ = [
    # Initialization
    'initialize',
    'is_initialized',
    'close',
    
    # Core query functions
    'get_fundamentals',
    'history',
    'get_instruments',
    'get_trading_dates',
    'get_history_l2ticks',
    'get_history_l2bars',
    'get_dividend',
    'get_continuous_contracts',
    'get_constituents',
    'get_sector',
    'get_industry',
    'get_concept',
    'get_variety_infos',
    'get_trading_times',
    'current',
    'current_price',
    'get_cash',
    'get_position',
    'universe_set',
    'universe_get_symbols',
    'universe_get_names',
    'universe_delete',
    
    # Convenience functions
    'history_n',
    'get_fundamentals_n',
    'get_history_instruments',
    'get_instrumentinfos',
    'get_previous_trading_date',
    'get_next_trading_date',
    'get_history_ticks_l2',
    'get_history_bars_l2',
    'get_history_l2transactions',
    'get_history_l2orders',
    'get_history_l2orders_queue',
    'option_get_symbols_by_exchange',
    'option_get_symbols_by_in_at_out',
    'option_get_delisted_dates',
    'option_get_exercise_prices',
    'get_expire_rest_days',
    'bond_convertible_get_call_info',
    'get_history_constituents',
    'raw_func',
    
    # Types and enums
    'Frequency',
    'AdjustType',
    'SecurityType',
    'Exchange',
    'DataField',
    
    # Exceptions
    'GMError',
    'ConnectionError',
    'QueryError',
]