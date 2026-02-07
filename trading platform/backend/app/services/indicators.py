"""
Indicator computation module for technical analysis.

This module provides the core abstractions for computing technical indicators
from price data. It defines the Indicator protocol that all indicator
implementations must follow, along with base classes and data structures.

The design is extensible to support all indicator types including:
- Moving Averages (SMA, EMA, ALMA)
- Momentum Indicators (RSI, MACD)
- Volatility Indicators (Bollinger Bands, ATR)
- Volume Indicators (VWAP)

Validates Requirements: 4.1-4.7, 5.1-5.5
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol
from enum import Enum


class Timeframe(Enum):
    """Supported timeframes for candle data"""
    ONE_MINUTE = "1m"
    FIVE_MINUTE = "5m"
    FIFTEEN_MINUTE = "15m"
    THIRTY_MINUTE = "30m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"
    ONE_DAY = "1D"
    ONE_WEEK = "1W"
    ONE_MONTH = "1M"


@dataclass(frozen=True)
class Candle:
    """
    Represents a single OHLCV (Open, High, Low, Close, Volume) candle.
    
    This is an immutable data structure used for passing price data
    to indicator computation functions.
    
    Attributes:
        timestamp: Candle timestamp
        open: Opening price
        high: Highest price during period
        low: Lowest price during period
        close: Closing price
        volume: Trading volume
        timeframe: Candle frequency (e.g., '1D', '5m', '1m')
        
    Invariants:
        - Low <= Open <= High
        - Low <= Close <= High
        - Low <= High
        - Volume >= 0
    """
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timeframe: str = "1D"
    
    def __post_init__(self):
        """Validate candle data on construction"""
        if not self.is_valid():
            raise ValueError(f"Invalid candle data: {self}")
    
    def is_valid(self) -> bool:
        """
        Check if candle satisfies OHLC invariants.
        
        Returns:
            True if valid, False otherwise
        """
        return (
            self.low <= self.open <= self.high and
            self.low <= self.close <= self.high and
            self.low <= self.high and
            self.volume >= 0
        )
    
    def typical_price(self) -> Decimal:
        """
        Calculate typical price: (High + Low + Close) / 3
        
        Returns:
            Typical price
        """
        return (self.high + self.low + self.close) / Decimal('3')
    
    def true_range(self, prev_close: Optional[Decimal] = None) -> Decimal:
        """
        Calculate true range for ATR computation.
        
        True Range = max(
            high - low,
            |high - prev_close|,
            |low - prev_close|
        )
        
        If prev_close is not provided, returns high - low.
        
        Args:
            prev_close: Previous candle's close price
            
        Returns:
            True range value
        """
        if prev_close is None:
            return self.high - self.low
        
        return max(
            self.high - self.low,
            abs(self.high - prev_close),
            abs(self.low - prev_close)
        )


@dataclass(frozen=True)
class IndicatorValue:
    """
    Represents a computed indicator value at a specific timestamp.
    
    This is an immutable data structure used for returning indicator
    computation results.
    
    Attributes:
        timestamp: Timestamp for this indicator value
        indicator_name: Name of the indicator (e.g., 'SMA_20', 'RSI_14')
        value: Primary computed value
        metadata: Optional dictionary for additional indicator-specific data
                  Examples:
                  - Bollinger Bands: {"upper_band": 155.0, "lower_band": 145.0}
                  - MACD: {"signal_line": 1.5, "histogram": 0.3}
                  - ATR: {"true_range": 2.5}
    """
    timestamp: datetime
    indicator_name: str
    value: Decimal
    metadata: Optional[Dict[str, Any]] = None
    
    def __repr__(self) -> str:
        meta_str = f", metadata={self.metadata}" if self.metadata else ""
        return (
            f"IndicatorValue(timestamp={self.timestamp}, "
            f"indicator='{self.indicator_name}', "
            f"value={self.value}{meta_str})"
        )


class Indicator(Protocol):
    """
    Abstract protocol for technical indicators.
    
    All indicator implementations must follow this protocol, providing:
    1. A name property that uniquely identifies the indicator
    2. A compute() method that calculates indicator values from candles
    3. A required_periods() method that specifies minimum data requirements
    
    This protocol enables polymorphic indicator computation in the
    AnalyticsEngine without requiring inheritance.
    
    Example implementations:
    - SMA (Simple Moving Average)
    - EMA (Exponential Moving Average)
    - RSI (Relative Strength Index)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - ATR (Average True Range)
    - ALMA (Arnaud Legoux Moving Average)
    - VWAP (Volume Weighted Average Price)
    """
    
    @property
    def name(self) -> str:
        """
        Indicator name (e.g., 'SMA_20', 'RSI_14', 'MACD_12_26_9').
        
        The name should include parameter values to uniquely identify
        the indicator configuration.
        
        Returns:
            Indicator name string
        """
        ...
    
    def compute(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Compute indicator values from candle data.
        
        This method should:
        1. Validate that sufficient candles are provided
        2. Compute indicator values for each applicable candle
        3. Return IndicatorValue objects with timestamps matching input candles
        4. Handle missing data gracefully (skip gaps, don't fail)
        
        Args:
            candles: List of candles in chronological order (oldest first)
            params: Dictionary of indicator-specific parameters
                    Examples:
                    - SMA: {"period": 20}
                    - EMA: {"period": 12}
                    - RSI: {"period": 14}
                    - MACD: {"fast": 12, "slow": 26, "signal": 9}
                    - Bollinger Bands: {"period": 20, "std_dev": 2.0}
                    
        Returns:
            List of IndicatorValue objects, one per candle where computation
            is possible. May be shorter than input if insufficient data for
            initial periods.
            
        Raises:
            ValueError: If params are invalid or insufficient candles provided
            
        Example:
            >>> candles = [Candle(...), Candle(...), ...]
            >>> sma = SMAIndicator()
            >>> values = sma.compute(candles, {"period": 20})
            >>> len(values) == len(candles) - 19  # First 19 candles need warmup
            True
        """
        ...
    
    def required_periods(self, params: Dict[str, Any]) -> int:
        """
        Return minimum number of candles needed for computation.
        
        This is used to:
        1. Validate sufficient data before calling compute()
        2. Determine warmup period for indicator calculation
        3. Optimize data fetching (only fetch what's needed)
        
        Args:
            params: Dictionary of indicator-specific parameters
            
        Returns:
            Minimum number of candles required
            
        Example:
            >>> sma = SMAIndicator()
            >>> sma.required_periods({"period": 20})
            20
            >>> rsi = RSIIndicator()
            >>> rsi.required_periods({"period": 14})
            15  # 14 + 1 for initial calculation
        """
        ...


class BaseIndicator(ABC):
    """
    Abstract base class for indicator implementations.
    
    Provides common functionality for all indicators including:
    - Parameter validation
    - Data sufficiency checks
    - Error handling
    - Logging
    
    Subclasses must implement:
    - name property
    - compute() method
    - required_periods() method
    - _compute_values() method (internal computation logic)
    
    This class provides a template method pattern where compute()
    handles validation and error handling, delegating actual computation
    to _compute_values().
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Indicator name (e.g., 'SMA_20', 'RSI_14').
        
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def required_periods(self, params: Dict[str, Any]) -> int:
        """
        Return minimum number of candles needed for computation.
        
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def _compute_values(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Internal method to compute indicator values.
        
        This is where subclasses implement their specific computation logic.
        This method is called by compute() after validation.
        
        Args:
            candles: List of validated candles (sufficient quantity)
            params: Validated parameters
            
        Returns:
            List of IndicatorValue objects
        """
        pass
    
    def compute(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Compute indicator values with validation and error handling.
        
        This template method:
        1. Validates parameters
        2. Checks data sufficiency
        3. Delegates to _compute_values()
        4. Handles errors gracefully
        
        Args:
            candles: List of candles in chronological order
            params: Indicator-specific parameters
            
        Returns:
            List of IndicatorValue objects
            
        Raises:
            ValueError: If validation fails
        """
        # Validate parameters
        self._validate_params(params)
        
        # Check if we have enough data
        required = self.required_periods(params)
        if len(candles) < required:
            raise ValueError(
                f"{self.name} requires at least {required} candles, "
                f"but only {len(candles)} provided"
            )
        
        # Ensure candles are sorted by timestamp
        sorted_candles = sorted(candles, key=lambda c: c.timestamp)
        
        # Delegate to subclass implementation
        return self._compute_values(sorted_candles, params)
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate indicator parameters.
        
        Subclasses can override this to add specific validation logic.
        Default implementation does nothing.
        
        Args:
            params: Parameters to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        pass
    
    def _validate_period(self, params: Dict[str, Any], param_name: str = "period") -> int:
        """
        Validate and extract a period parameter.
        
        Helper method for common period validation.
        
        Args:
            params: Parameter dictionary
            param_name: Name of the period parameter (default: "period")
            
        Returns:
            Validated period value
            
        Raises:
            ValueError: If period is missing or invalid
        """
        if param_name not in params:
            raise ValueError(f"Missing required parameter: {param_name}")
        
        period = params[param_name]
        
        if not isinstance(period, int):
            raise ValueError(f"{param_name} must be an integer, got {type(period)}")
        
        if period < 1:
            raise ValueError(f"{param_name} must be positive, got {period}")
        
        return period


class IndicatorRegistry:
    """
    Registry for managing available indicators.
    
    Provides a centralized place to register and retrieve indicator
    implementations. Used by the AnalyticsEngine to discover and
    instantiate indicators.
    
    Example:
        >>> registry = IndicatorRegistry()
        >>> registry.register(SMAIndicator())
        >>> registry.register(RSIIndicator())
        >>> sma = registry.get("SMA_20")
        >>> indicators = registry.list_all()
    """
    
    def __init__(self):
        """Initialize empty registry"""
        self._indicators: Dict[str, Indicator] = {}
    
    def register(self, indicator: Indicator) -> None:
        """
        Register an indicator.
        
        Args:
            indicator: Indicator instance to register
            
        Raises:
            ValueError: If indicator with same name already registered
        """
        if indicator.name in self._indicators:
            raise ValueError(
                f"Indicator '{indicator.name}' is already registered"
            )
        self._indicators[indicator.name] = indicator
    
    def get(self, name: str) -> Optional[Indicator]:
        """
        Get indicator by name.
        
        Args:
            name: Indicator name
            
        Returns:
            Indicator instance or None if not found
        """
        return self._indicators.get(name)
    
    def list_all(self) -> List[str]:
        """
        List all registered indicator names.
        
        Returns:
            List of indicator names
        """
        return list(self._indicators.keys())
    
    def clear(self) -> None:
        """Clear all registered indicators"""
        self._indicators.clear()



class SMAIndicator(BaseIndicator):
    """
    Simple Moving Average (SMA) indicator.
    
    The SMA is calculated as the arithmetic mean of the closing prices
    over a specified period:
    
        SMA(i) = sum(close[i-N+1:i+1]) / N
    
    Where:
        - N is the period (number of candles)
        - i is the current position
        - close[i-N+1:i+1] is the window of N closing prices ending at position i
    
    Example:
        For a 20-period SMA, the value at position i is the average of the
        20 most recent closing prices (including position i).
    
    Edge Cases:
        - Insufficient data: Requires at least N candles to compute first value
        - Missing data: Skips gaps in the data (handled by BaseIndicator)
    
    Validates Requirements: 4.1
    """
    
    def __init__(self, period: int = 20):
        """
        Initialize SMA indicator.
        
        Args:
            period: Number of candles to average (default: 20)
        """
        self._period = period
    
    @property
    def name(self) -> str:
        """
        Indicator name including period parameter.
        
        Returns:
            Name in format 'SMA_{period}'
        """
        return f"SMA_{self._period}"
    
    def required_periods(self, params: Dict[str, Any]) -> int:
        """
        Return minimum number of candles needed for SMA computation.
        
        SMA requires exactly N candles to compute the first value.
        
        Args:
            params: Dictionary containing 'period' key
            
        Returns:
            Period value (N candles required)
        """
        period = params.get('period', self._period)
        return period
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate SMA parameters.
        
        Args:
            params: Dictionary containing 'period' key
            
        Raises:
            ValueError: If period is missing, not an integer, or not positive
        """
        self._validate_period(params, 'period')
    
    def _compute_values(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Compute SMA values for the given candles.
        
        Implementation:
        1. Extract period from params
        2. For each position i from (period-1) to end:
           a. Extract window of N closing prices
           b. Calculate arithmetic mean
           c. Create IndicatorValue with timestamp from candle[i]
        
        Args:
            candles: List of candles in chronological order (validated and sorted)
            params: Dictionary containing 'period' key
            
        Returns:
            List of IndicatorValue objects, one per candle starting from position (period-1)
            
        Example:
            For 25 candles with period=20:
            - Returns 6 values (positions 19-24)
            - First value is average of candles[0:20]
            - Last value is average of candles[5:25]
        """
        period = params.get('period', self._period)
        values = []
        
        # Compute SMA for each position starting from (period-1)
        for i in range(period - 1, len(candles)):
            # Extract window of N closing prices
            window = candles[i - period + 1:i + 1]
            
            # Calculate arithmetic mean: sum(close) / N
            close_sum = sum(c.close for c in window)
            sma_value = close_sum / Decimal(str(period))
            
            # Create indicator value with timestamp from current candle
            values.append(IndicatorValue(
                timestamp=candles[i].timestamp,
                indicator_name=self.name,
                value=sma_value,
                metadata=None
            ))
        
        return values


class RSIIndicator(BaseIndicator):
    """
    Relative Strength Index (RSI) indicator.
    
    The RSI is a momentum oscillator that measures the speed and magnitude of
    price changes. It oscillates between 0 and 100, with readings above 70
    typically indicating overbought conditions and readings below 30 indicating
    oversold conditions.
    
    The RSI is calculated using the following formula:
    
        RSI = 100 - 100 / (1 + RS)
        
    Where:
        - RS (Relative Strength) = Average Gain / Average Loss
        - Average Gain = Average of all gains over the period
        - Average Loss = Average of all losses over the period
    
    Calculation Steps:
        1. Calculate price changes: change(i) = close(i) - close(i-1)
        2. Separate gains and losses:
           - gain(i) = change(i) if change(i) > 0, else 0
           - loss(i) = |change(i)| if change(i) < 0, else 0
        3. Calculate initial averages using SMA of first N gains/losses
        4. Calculate subsequent averages using smoothed moving average:
           - avg_gain(i) = (avg_gain(i-1) * (N-1) + gain(i)) / N
           - avg_loss(i) = (avg_loss(i-1) * (N-1) + loss(i)) / N
        5. Calculate RS and RSI for each position
    
    Edge Cases:
        - All gains (no losses): RSI = 100
        - All losses (no gains): RSI = 0
        - Average loss = 0: RSI = 100 (avoid division by zero)
        - Insufficient data: Requires N+1 candles (N for period, +1 for first change)
    
    Properties:
        - RSI is always in the range [0, 100]
        - More responsive to recent price changes than simple moving averages
        - Commonly used with period=14
    
    Validates Requirements: 4.3
    """
    
    def __init__(self, period: int = 14):
        """
        Initialize RSI indicator.
        
        Args:
            period: Number of periods for RSI calculation (default: 14)
        """
        self._period = period
    
    @property
    def name(self) -> str:
        """
        Indicator name including period parameter.
        
        Returns:
            Name in format 'RSI_{period}'
        """
        return f"RSI_{self._period}"
    
    def required_periods(self, params: Dict[str, Any]) -> int:
        """
        Return minimum number of candles needed for RSI computation.
        
        RSI requires N+1 candles:
        - N candles to calculate the initial average gain/loss
        - +1 candle to compute the first price change
        
        Args:
            params: Dictionary containing 'period' key
            
        Returns:
            Period + 1 (N+1 candles required)
        """
        period = params.get('period', self._period)
        return period + 1
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate RSI parameters.
        
        Args:
            params: Dictionary containing 'period' key
            
        Raises:
            ValueError: If period is missing, not an integer, or not positive
        """
        self._validate_period(params, 'period')
    
    def _compute_values(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Compute RSI values for the given candles.
        
        Implementation:
        1. Extract period from params
        2. Calculate price changes for all candles
        3. Separate gains and losses
        4. Calculate initial average gain/loss using SMA of first N changes
        5. For each subsequent position:
           a. Update average gain/loss using smoothed moving average
           b. Calculate RS = avg_gain / avg_loss
           c. Calculate RSI = 100 - 100 / (1 + RS)
           d. Create IndicatorValue with timestamp from current candle
        
        Args:
            candles: List of candles in chronological order (validated and sorted)
            params: Dictionary containing 'period' key
            
        Returns:
            List of IndicatorValue objects, one per candle starting from position N
            
        Example:
            For 25 candles with period=14:
            - Returns 11 values (positions 14-24)
            - First value uses SMA of first 14 changes
            - Subsequent values use smoothed moving average
        """
        period = params.get('period', self._period)
        values = []
        
        # Calculate price changes
        changes = []
        for i in range(1, len(candles)):
            change = candles[i].close - candles[i - 1].close
            changes.append(change)
        
        # Separate gains and losses
        gains = [max(change, Decimal('0')) for change in changes]
        losses = [abs(min(change, Decimal('0'))) for change in changes]
        
        # Calculate initial average gain/loss using SMA of first N changes
        initial_avg_gain = sum(gains[:period]) / Decimal(str(period))
        initial_avg_loss = sum(losses[:period]) / Decimal(str(period))
        
        # Initialize smoothed averages
        avg_gain = initial_avg_gain
        avg_loss = initial_avg_loss
        
        # Calculate RSI for first position (at index period, which is candle period+1)
        if avg_loss == Decimal('0'):
            # All gains, no losses → RSI = 100
            rsi_value = Decimal('100')
        else:
            rs = avg_gain / avg_loss
            rsi_value = Decimal('100') - Decimal('100') / (Decimal('1') + rs)
        
        values.append(IndicatorValue(
            timestamp=candles[period].timestamp,
            indicator_name=self.name,
            value=rsi_value,
            metadata=None
        ))
        
        # Calculate RSI for remaining positions using smoothed moving average
        period_decimal = Decimal(str(period))
        period_minus_one = Decimal(str(period - 1))
        
        for i in range(period, len(changes)):
            # Update smoothed averages:
            # avg_gain(i) = (avg_gain(i-1) * (N-1) + gain(i)) / N
            # avg_loss(i) = (avg_loss(i-1) * (N-1) + loss(i)) / N
            avg_gain = (avg_gain * period_minus_one + gains[i]) / period_decimal
            avg_loss = (avg_loss * period_minus_one + losses[i]) / period_decimal
            
            # Calculate RS and RSI
            if avg_loss == Decimal('0'):
                # All gains, no losses → RSI = 100
                rsi_value = Decimal('100')
            else:
                rs = avg_gain / avg_loss
                rsi_value = Decimal('100') - Decimal('100') / (Decimal('1') + rs)
            
            # Create indicator value with timestamp from current candle
            # Note: i is the index in changes array, so candle index is i+1
            values.append(IndicatorValue(
                timestamp=candles[i + 1].timestamp,
                indicator_name=self.name,
                value=rsi_value,
                metadata=None
            ))
        
        return values


class EMAIndicator(BaseIndicator):
    """
    Exponential Moving Average (EMA) indicator.
    
    The EMA is a weighted moving average that gives more weight to recent prices,
    making it more responsive to price changes than the SMA. It uses a recursive
    formula with a smoothing factor:
    
        EMA(i) = α * close(i) + (1 - α) * EMA(i-1)
        
    Where:
        - α (alpha) = 2 / (period + 1) is the smoothing factor
        - close(i) is the current closing price
        - EMA(i-1) is the previous EMA value
        - EMA(0) is initialized using SMA of the first N prices
    
    The smoothing factor α determines how much weight is given to the current price:
        - Larger α (smaller period) → more weight on recent prices → more responsive
        - Smaller α (larger period) → more weight on historical prices → smoother
    
    Example:
        For a 12-period EMA with α = 2/(12+1) = 0.1538:
        - Current price contributes 15.38% to the new EMA
        - Previous EMA contributes 84.62% to the new EMA
    
    Initialization:
        The first EMA value is calculated as the SMA of the first N prices.
        This provides a stable starting point for the recursive calculation.
    
    Edge Cases:
        - Insufficient data: Requires at least N candles to compute first value
        - Missing data: Skips gaps in the data (handled by BaseIndicator)
    
    Validates Requirements: 4.2
    """
    
    def __init__(self, period: int = 12):
        """
        Initialize EMA indicator.
        
        Args:
            period: Number of periods for EMA calculation (default: 12)
        """
        self._period = period
    
    @property
    def name(self) -> str:
        """
        Indicator name including period parameter.
        
        Returns:
            Name in format 'EMA_{period}'
        """
        return f"EMA_{self._period}"
    
    def required_periods(self, params: Dict[str, Any]) -> int:
        """
        Return minimum number of candles needed for EMA computation.
        
        EMA requires N candles to compute the initial SMA seed value,
        then continues recursively from there.
        
        Args:
            params: Dictionary containing 'period' key
            
        Returns:
            Period value (N candles required)
        """
        period = params.get('period', self._period)
        return period
    
    def _validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate EMA parameters.
        
        Args:
            params: Dictionary containing 'period' key
            
        Raises:
            ValueError: If period is missing, not an integer, or not positive
        """
        self._validate_period(params, 'period')
    
    def _compute_values(
        self,
        candles: List[Candle],
        params: Dict[str, Any]
    ) -> List[IndicatorValue]:
        """
        Compute EMA values for the given candles.
        
        Implementation:
        1. Extract period from params
        2. Calculate smoothing factor: α = 2 / (period + 1)
        3. Initialize first EMA using SMA of first N prices
        4. For each subsequent position:
           a. Apply recursive formula: EMA(i) = α * close(i) + (1 - α) * EMA(i-1)
           b. Create IndicatorValue with timestamp from current candle
        
        Args:
            candles: List of candles in chronological order (validated and sorted)
            params: Dictionary containing 'period' key
            
        Returns:
            List of IndicatorValue objects, one per candle starting from position (period-1)
            
        Example:
            For 25 candles with period=12:
            - Returns 14 values (positions 11-24)
            - First value is SMA of candles[0:12]
            - Subsequent values use recursive EMA formula
        """
        period = params.get('period', self._period)
        values = []
        
        # Calculate smoothing factor: α = 2 / (period + 1)
        alpha = Decimal('2') / Decimal(str(period + 1))
        one_minus_alpha = Decimal('1') - alpha
        
        # Initialize first EMA using SMA of first N prices
        first_window = candles[:period]
        close_sum = sum(c.close for c in first_window)
        ema_value = close_sum / Decimal(str(period))
        
        # Create first indicator value
        values.append(IndicatorValue(
            timestamp=candles[period - 1].timestamp,
            indicator_name=self.name,
            value=ema_value,
            metadata=None
        ))
        
        # Compute EMA recursively for remaining candles
        for i in range(period, len(candles)):
            # Apply recursive formula: EMA(i) = α * close(i) + (1 - α) * EMA(i-1)
            current_close = candles[i].close
            ema_value = alpha * current_close + one_minus_alpha * ema_value
            
            # Create indicator value with timestamp from current candle
            values.append(IndicatorValue(
                timestamp=candles[i].timestamp,
                indicator_name=self.name,
                value=ema_value,
                metadata=None
            ))
        
        return values
