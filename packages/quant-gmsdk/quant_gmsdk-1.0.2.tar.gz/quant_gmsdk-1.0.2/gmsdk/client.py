"""
gRPC client implementation for the GM SDK.
"""

import threading
import time
from typing import Optional

import grpc

from .models.exceptions import ConnectionError, ServerError
from .models.types import QueryConfig
from .proto import gm_service_pb2, gm_service_pb2_grpc
from .utils.logging import get_logger

logger = get_logger(__name__)


class GMClient:
    """
    gRPC client for GM service communication.
    """
    
    def __init__(self, server_address: str, config: QueryConfig):
        """
        Initialize GM client.
        
        Args:
            server_address: Server address (host:port)
            config: Query configuration
        """
        self.server_address = server_address
        self.config = config
        self._channel: Optional[grpc.Channel] = None
        self._stub: Optional[gm_service_pb2_grpc.GMServiceStub] = None
        self._lock = threading.Lock()
        self._connected = False
        
    def connect(self) -> None:
        """
        Connect to the GM server.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            with self._lock:
                if self._connected:
                    return
                
                logger.info(f"Connecting to GM server at {self.server_address}")
                
                # Configure channel options
                options = [
                    ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                    ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
                    ('grpc.keepalive_time_ms', 30000),  # 30 seconds
                    ('grpc.keepalive_timeout_ms', 5000),  # 5 seconds
                    ('grpc.keepalive_permit_without_calls', True),
                    ('grpc.http2.min_time_between_pings_ms', 10000),  # 10 seconds
                    ('grpc.http2.max_pings_without_data', 0),
                ]
                
                self._channel = grpc.insecure_channel(
                    self.server_address,
                    options=options
                )
                
                # Create stub
                self._stub = gm_service_pb2_grpc.GMServiceStub(self._channel)
                
                # Test connection
                try:
                    # Try a simple health check
                    grpc.channel_ready_future(self._channel).result(timeout=self.config.timeout)
                    self._connected = True
                    logger.info(f"Successfully connected to GM server at {self.server_address}")
                    
                except grpc.FutureTimeoutError:
                    raise ConnectionError(f"Connection timeout to {self.server_address}")
                    
        except Exception as e:
            logger.error(f"Failed to connect to GM server: {e}")
            raise ConnectionError(f"Failed to connect to GM server: {e}")
    
    def disconnect(self) -> None:
        """Disconnect from the GM server."""
        try:
            with self._lock:
                if self._channel:
                    self._channel.close()
                    self._channel = None
                    self._stub = None
                    self._connected = False
                    logger.info("Disconnected from GM server")
                    
        except Exception as e:
            logger.error(f"Error disconnecting from GM server: {e}")
    
    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected and self._channel is not None
    
    def _execute_with_retry(self, operation, *args, **kwargs):
        """
        Execute operation with retry logic.
        
        Args:
            operation: Function to execute
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            ConnectionError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if not self.is_connected():
                    self.connect()
                
                return operation(*args, **kwargs)
                
            except grpc.RpcError as e:
                last_exception = e
                
                if e.code() == grpc.StatusCode.UNAVAILABLE:
                    logger.warning(f"Server unavailable, attempt {attempt + 1}/{self.config.max_retries + 1}")
                    self._connected = False
                    
                elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    logger.warning(f"Request timeout, attempt {attempt + 1}/{self.config.max_retries + 1}")
                    
                elif e.code() == grpc.StatusCode.INTERNAL:
                    logger.error(f"Server internal error: {e.details()}")
                    raise ServerError(f"Server internal error: {e.details()}")
                    
                else:
                    logger.error(f"gRPC error: {e.code()} - {e.details()}")
                    raise ServerError(f"gRPC error: {e.code()} - {e.details()}")
                
                # Wait before retry
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    
        raise ConnectionError(f"Operation failed after {self.config.max_retries + 1} attempts: {last_exception}")
    
    def get_fundamentals(self, request: gm_service_pb2.GetFundamentalsRequest) -> gm_service_pb2.GetFundamentalsResponse:
        """
        Get fundamentals data.
        
        Args:
            request: GetFundamentalsRequest
            
        Returns:
            GetFundamentalsResponse
        """
        def _operation():
            return self._stub.GetFundamentals(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def history(self, request: gm_service_pb2.HistoryRequest) -> gm_service_pb2.HistoryResponse:
        """
        Get historical data.
        
        Args:
            request: HistoryRequest
            
        Returns:
            HistoryResponse
        """
        def _operation():
            return self._stub.History(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_instruments(self, request: gm_service_pb2.GetInstrumentsRequest) -> gm_service_pb2.GetInstrumentsResponse:
        """
        Get instruments data.
        
        Args:
            request: GetInstrumentsRequest
            
        Returns:
            GetInstrumentsResponse
        """
        def _operation():
            return self._stub.GetInstruments(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_trading_dates(self, request: gm_service_pb2.GetTradingDatesRequest) -> gm_service_pb2.GetTradingDatesResponse:
        """
        Get trading dates.
        
        Args:
            request: GetTradingDatesRequest
            
        Returns:
            GetTradingDatesResponse
        """
        def _operation():
            return self._stub.GetTradingDates(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_history_l2ticks(self, request: gm_service_pb2.GetHistoryL2TicksRequest) -> gm_service_pb2.GetHistoryL2TicksResponse:
        """
        Get Level 2 tick data.
        
        Args:
            request: GetHistoryL2TicksRequest
            
        Returns:
            GetHistoryL2TicksResponse
        """
        def _operation():
            return self._stub.GetHistoryL2Ticks(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_history_l2bars(self, request: gm_service_pb2.GetHistoryL2BarsRequest) -> gm_service_pb2.GetHistoryL2BarsResponse:
        """
        Get Level 2 bar data.
        
        Args:
            request: GetHistoryL2BarsRequest
            
        Returns:
            GetHistoryL2BarsResponse
        """
        def _operation():
            return self._stub.GetHistoryL2Bars(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_dividend(self, request: gm_service_pb2.GetDividendRequest) -> gm_service_pb2.GetDividendResponse:
        """
        Get dividend data.
        
        Args:
            request: GetDividendRequest
            
        Returns:
            GetDividendResponse
        """
        def _operation():
            return self._stub.GetDividend(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_continuous_contracts(self, request: gm_service_pb2.GetContinuousContractsRequest) -> gm_service_pb2.GetContinuousContractsResponse:
        """
        Get continuous contracts.
        
        Args:
            request: GetContinuousContractsRequest
            
        Returns:
            GetContinuousContractsResponse
        """
        def _operation():
            return self._stub.GetContinuousContracts(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_constituents(self, request: gm_service_pb2.GetConstituentsRequest) -> gm_service_pb2.GetConstituentsResponse:
        """
        Get index constituents.
        
        Args:
            request: GetConstituentsRequest
            
        Returns:
            GetConstituentsResponse
        """
        def _operation():
            return self._stub.GetConstituents(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_sector(self, request: gm_service_pb2.GetSectorRequest) -> gm_service_pb2.GetSectorResponse:
        """
        Get sector data.
        
        Args:
            request: GetSectorRequest
            
        Returns:
            GetSectorResponse
        """
        def _operation():
            return self._stub.GetSector(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_industry(self, request: gm_service_pb2.GetIndustryRequest) -> gm_service_pb2.GetIndustryResponse:
        """
        Get industry data.
        
        Args:
            request: GetIndustryRequest
            
        Returns:
            GetIndustryResponse
        """
        def _operation():
            return self._stub.GetIndustry(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_concept(self, request: gm_service_pb2.GetConceptRequest) -> gm_service_pb2.GetConceptResponse:
        """
        Get concept data.
        
        Args:
            request: GetConceptRequest
            
        Returns:
            GetConceptResponse
        """
        def _operation():
            return self._stub.GetConcept(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_variety_infos(self, request: gm_service_pb2.GetVarietyInfosRequest) -> gm_service_pb2.GetVarietyInfosResponse:
        """
        Get variety information.
        
        Args:
            request: GetVarietyInfosRequest
            
        Returns:
            GetVarietyInfosResponse
        """
        def _operation():
            return self._stub.GetVarietyInfos(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_trading_times(self, request: gm_service_pb2.GetTradingTimesRequest) -> gm_service_pb2.GetTradingTimesResponse:
        """
        Get trading times.
        
        Args:
            request: GetTradingTimesRequest
            
        Returns:
            GetTradingTimesResponse
        """
        def _operation():
            return self._stub.GetTradingTimes(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_cash(self, request: gm_service_pb2.GetCashRequest) -> gm_service_pb2.GetCashResponse:
        """
        Get cash information.
        
        Args:
            request: GetCashRequest
            
        Returns:
            GetCashResponse
        """
        def _operation():
            return self._stub.GetCash(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def get_position(self, request: gm_service_pb2.GetPositionRequest) -> gm_service_pb2.GetPositionResponse:
        """
        Get position information.
        
        Args:
            request: GetPositionRequest
            
        Returns:
            GetPositionResponse
        """
        def _operation():
            return self._stub.GetPosition(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def universe_set(self, request: gm_service_pb2.UniverseSetRequest) -> gm_service_pb2.UniverseSetResponse:
        """
        Set universe.
        
        Args:
            request: UniverseSetRequest
            
        Returns:
            UniverseSetResponse
        """
        def _operation():
            return self._stub.UniverseSet(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def universe_get_symbols(self, request: gm_service_pb2.UniverseGetSymbolsRequest) -> gm_service_pb2.UniverseGetSymbolsResponse:
        """
        Get universe symbols.
        
        Args:
            request: UniverseGetSymbolsRequest
            
        Returns:
            UniverseGetSymbolsResponse
        """
        def _operation():
            return self._stub.UniverseGetSymbols(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def universe_get_names(self, request: gm_service_pb2.UniverseGetNamesRequest) -> gm_service_pb2.UniverseGetNamesResponse:
        """
        Get universe names.
        
        Args:
            request: UniverseGetNamesRequest
            
        Returns:
            UniverseGetNamesResponse
        """
        def _operation():
            return self._stub.UniverseGetNames(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)
    
    def universe_delete(self, request: gm_service_pb2.UniverseDeleteRequest) -> gm_service_pb2.UniverseDeleteResponse:
        """
        Delete universe.
        
        Args:
            request: UniverseDeleteRequest
            
        Returns:
            UniverseDeleteResponse
        """
        def _operation():
            return self._stub.UniverseDelete(request, timeout=self.config.timeout)
        
        return self._execute_with_retry(_operation)

    def current(self, request: gm_service_pb2.CurrentRequest) -> gm_service_pb2.CurrentResponse:
        """
        获取当前行情快照数据。

        Args:
            request: CurrentRequest

        Returns:
            CurrentResponse
        """
        def _operation():
            return self._stub.Current(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def current_price(self, request: gm_service_pb2.CurrentPriceRequest) -> gm_service_pb2.CurrentPriceResponse:
        """
        获取当前价格数据。

        Args:
            request: CurrentPriceRequest

        Returns:
            CurrentPriceResponse
        """
        def _operation():
            return self._stub.CurrentPrice(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def history_n(self, request: gm_service_pb2.HistoryNRequest) -> gm_service_pb2.HistoryNResponse:
        """
        Get historical data by count.

        Args:
            request: HistoryNRequest

        Returns:
            HistoryNResponse
        """
        def _operation():
            return self._stub.HistoryN(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_fundamentals_n(self, request: gm_service_pb2.GetFundamentalsNRequest) -> gm_service_pb2.GetFundamentalsNResponse:
        """
        Get fundamental data by count.

        Args:
            request: GetFundamentalsNRequest

        Returns:
            GetFundamentalsNResponse
        """
        def _operation():
            return self._stub.GetFundamentalsN(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_previous_trading_date(self, request: gm_service_pb2.GetPreviousTradingDateRequest) -> gm_service_pb2.GetPreviousTradingDateResponse:
        """
        Get previous trading date.

        Args:
            request: GetPreviousTradingDateRequest

        Returns:
            GetPreviousTradingDateResponse
        """
        def _operation():
            return self._stub.GetPreviousTradingDate(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_next_trading_date(self, request: gm_service_pb2.GetNextTradingDateRequest) -> gm_service_pb2.GetNextTradingDateResponse:
        """
        Get next trading date.

        Args:
            request: GetNextTradingDateRequest

        Returns:
            GetNextTradingDateResponse
        """
        def _operation():
            return self._stub.GetNextTradingDate(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_history_l2transactions(self, request: gm_service_pb2.GetHistoryL2TransactionsRequest) -> gm_service_pb2.GetHistoryL2TransactionsResponse:
        """
        Get Level 2 transaction data.

        Args:
            request: GetHistoryL2TransactionsRequest

        Returns:
            GetHistoryL2TransactionsResponse
        """
        def _operation():
            return self._stub.GetHistoryL2Transactions(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_history_l2orders(self, request: gm_service_pb2.GetHistoryL2OrdersRequest) -> gm_service_pb2.GetHistoryL2OrdersResponse:
        """
        Get Level 2 order data.

        Args:
            request: GetHistoryL2OrdersRequest

        Returns:
            GetHistoryL2OrdersResponse
        """
        def _operation():
            return self._stub.GetHistoryL2Orders(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_history_l2orders_queue(self, request: gm_service_pb2.GetHistoryL2OrdersQueueRequest) -> gm_service_pb2.GetHistoryL2OrdersQueueResponse:
        """
        Get Level 2 order queue data.

        Args:
            request: GetHistoryL2OrdersQueueRequest

        Returns:
            GetHistoryL2OrdersQueueResponse
        """
        def _operation():
            return self._stub.GetHistoryL2OrdersQueue(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def option_get_symbols_by_exchange(self, request: gm_service_pb2.OptionGetSymbolsByExchangeRequest) -> gm_service_pb2.OptionGetSymbolsByExchangeResponse:
        """
        Get option symbols by exchange.

        Args:
            request: OptionGetSymbolsByExchangeRequest

        Returns:
            OptionGetSymbolsByExchangeResponse
        """
        def _operation():
            return self._stub.OptionGetSymbolsByExchange(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def option_get_symbols_by_in_at_out(self, request: gm_service_pb2.OptionGetSymbolsByInAtOutRequest) -> gm_service_pb2.OptionGetSymbolsByInAtOutResponse:
        """
        Get option symbols by in/at/out of money.

        Args:
            request: OptionGetSymbolsByInAtOutRequest

        Returns:
            OptionGetSymbolsByInAtOutResponse
        """
        def _operation():
            return self._stub.OptionGetSymbolsByInAtOut(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def option_get_delisted_dates(self, request: gm_service_pb2.OptionGetDelistedDatesRequest) -> gm_service_pb2.OptionGetDelistedDatesResponse:
        """
        Get option delisted dates.

        Args:
            request: OptionGetDelistedDatesRequest

        Returns:
            OptionGetDelistedDatesResponse
        """
        def _operation():
            return self._stub.OptionGetDelistedDates(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def option_get_exercise_prices(self, request: gm_service_pb2.OptionGetExercisePricesRequest) -> gm_service_pb2.OptionGetExercisePricesResponse:
        """
        Get option exercise prices.

        Args:
            request: OptionGetExercisePricesRequest

        Returns:
            OptionGetExercisePricesResponse
        """
        def _operation():
            return self._stub.OptionGetExercisePrices(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_expire_rest_days(self, request: gm_service_pb2.GetExpireRestDaysRequest) -> gm_service_pb2.GetExpireRestDaysResponse:
        """
        Get days until expiration.

        Args:
            request: GetExpireRestDaysRequest

        Returns:
            GetExpireRestDaysResponse
        """
        def _operation():
            return self._stub.GetExpireRestDays(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def bond_convertible_get_call_info(self, request: gm_service_pb2.BondConvertibleGetCallInfoRequest) -> gm_service_pb2.BondConvertibleGetCallInfoResponse:
        """
        Get convertible bond call information.

        Args:
            request: BondConvertibleGetCallInfoRequest

        Returns:
            BondConvertibleGetCallInfoResponse
        """
        def _operation():
            return self._stub.BondConvertibleGetCallInfo(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def get_history_constituents(self, request: gm_service_pb2.GetHistoryConstituentsRequest) -> gm_service_pb2.GetHistoryConstituentsResponse:
        """
        Get historical index constituents.

        Args:
            request: GetHistoryConstituentsRequest

        Returns:
            GetHistoryConstituentsResponse
        """
        def _operation():
            return self._stub.GetHistoryConstituents(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)

    def raw_func(self, request: gm_service_pb2.RawFuncRequest) -> gm_service_pb2.RawFuncResponse:
        """
        Execute raw function call.

        Args:
            request: RawFuncRequest

        Returns:
            RawFuncResponse
        """
        def _operation():
            return self._stub.RawFunc(request, timeout=self.config.timeout)

        return self._execute_with_retry(_operation)