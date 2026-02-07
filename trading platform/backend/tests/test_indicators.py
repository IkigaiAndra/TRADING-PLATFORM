"""
Unit tests for indicator protocol and base classes.

Tests the core abstractions for indicator computation including:
- Candle data structure and validation
- IndicatorValue data structure
- Indicator protocol interface
- BaseIndicator template class
- IndicatorRegistry

Validates Requirements: 4.1-4.7
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List

from app.services.indicators import (
    Candle,
    IndicatorValue,
    Indicator,
    BaseIndicator,
    IndicatorRegistry,
    Timeframe,
    SMAIndicator,
    EMAIndicator,
    RSIIndicator,
    MACDIndicator
)


class TestCandle:
    """Test Candle data structure"""
    
    def test_candle_creation_valid(self):
        """Test creating a valid candle"""
        candle = Candle(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000,
            timeframe='1D'
        )
        
        assert candle.open == Decimal('150.00')
        assert candle.high == Decimal('155.00')
        assert candle.low == Decimal('149.00')
        assert candle.close == Decimal('154.00')
        assert candle.volume == 1000000
        assert candle.timeframe == '1D'
        assert candle.is_valid()
    
    def test_candle_invalid_high_less_than_low(self):
        """Test candle with high < low raises ValueError"""
        with pytest.raises(ValueError, match="Invalid candle data"):
            Candle(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('149.00'),  # High < Low
                low=Decimal('151.00'),
                close=Decimal('150.00'),
                volume=1000000
            )
    
    def test_candle_invalid_open_outside_range(self):
        """Test candle with open outside [low, high] raises ValueError"""
        with pytest.raises(ValueError, match="Invalid candle data"):
            Candle(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('160.00'),  # Open > High
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            )
    
    def test_candle_invalid_close_outside_range(self):
        """Test candle with close outside [low, high] raises ValueError"""
        with pytest.raises(ValueError, match="Invalid candle data"):
            Candle(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('148.00'),  # Close < Low
                volume=1000000
            )
    
    def test_candle_invalid_negative_volume(self):
        """Test candle with negative volume raises ValueError"""
        with pytest.raises(ValueError, match="Invalid candle data"):
            Candle(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=-1000  # Negative volume
            )
    
    def test_candle_typical_price(self):
        """Test typical price calculation"""
        candle = Candle(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('156.00'),
            low=Decimal('147.00'),
            close=Decimal('153.00'),
            volume=1000000
        )
        
        # Typical price = (High + Low + Close) / 3
        # = (156 + 147 + 153) / 3 = 456 / 3 = 152
        expected = Decimal('152.00')
        assert candle.typical_price() == expected
    
    def test_candle_true_range_without_prev_close(self):
        """Test true range calculation without previous close"""
        candle = Candle(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        # True range without prev_close = high - low
        # = 155 - 149 = 6
        expected = Decimal('6.00')
        assert candle.true_range() == expected
    
    def test_candle_true_range_with_prev_close(self):
        """Test true range calculation with previous close"""
        candle = Candle(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        prev_close = Decimal('148.00')
        
        # True range = max(
        #   high - low = 155 - 149 = 6,
        #   |high - prev_close| = |155 - 148| = 7,
        #   |low - prev_close| = |149 - 148| = 1
        # ) = 7
        expected = Decimal('7.00')
        assert candle.true_range(prev_close) == expected
    
    def test_candle_immutability(self):
        """Test that Candle is immutable (frozen dataclass)"""
        candle = Candle(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        with pytest.raises(AttributeError):
            candle.close = Decimal('160.00')


class TestIndicatorValue:
    """Test IndicatorValue data structure"""
    
    def test_indicator_value_creation(self):
        """Test creating an indicator value"""
        value = IndicatorValue(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            indicator_name='SMA_20',
            value=Decimal('152.50')
        )
        
        assert value.indicator_name == 'SMA_20'
        assert value.value == Decimal('152.50')
        assert value.metadata is None
    
    def test_indicator_value_with_metadata(self):
        """Test creating an indicator value with metadata"""
        metadata = {
            'upper_band': Decimal('155.00'),
            'lower_band': Decimal('145.00')
        }
        
        value = IndicatorValue(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            indicator_name='BB_20',
            value=Decimal('150.00'),
            metadata=metadata
        )
        
        assert value.metadata == metadata
        assert value.metadata['upper_band'] == Decimal('155.00')
        assert value.metadata['lower_band'] == Decimal('145.00')
    
    def test_indicator_value_immutability(self):
        """Test that IndicatorValue is immutable"""
        value = IndicatorValue(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            indicator_name='SMA_20',
            value=Decimal('152.50')
        )
        
        with pytest.raises(AttributeError):
            value.value = Decimal('160.00')
    
    def test_indicator_value_repr(self):
        """Test string representation of IndicatorValue"""
        value = IndicatorValue(
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            indicator_name='SMA_20',
            value=Decimal('152.50')
        )
        
        repr_str = repr(value)
        assert 'SMA_20' in repr_str
        assert '152.50' in repr_str


class TestBaseIndicator:
    """Test BaseIndicator abstract class"""
    
    def test_base_indicator_requires_implementation(self):
        """Test that BaseIndicator cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseIndicator()
    
    def test_concrete_indicator_implementation(self):
        """Test a concrete indicator implementation"""
        
        class SimpleMovingAverage(BaseIndicator):
            """Simple test implementation of SMA"""
            
            @property
            def name(self) -> str:
                return "SMA_TEST"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return params.get('period', 20)
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                period = params['period']
                values = []
                
                for i in range(period - 1, len(candles)):
                    window = candles[i - period + 1:i + 1]
                    avg = sum(c.close for c in window) / period
                    
                    values.append(IndicatorValue(
                        timestamp=candles[i].timestamp,
                        indicator_name=self.name,
                        value=avg
                    ))
                
                return values
        
        # Create test candles
        candles = []
        for i in range(25):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal(str(150 + i)),
                volume=1000000
            ))
        
        # Test indicator
        sma = SimpleMovingAverage()
        assert sma.name == "SMA_TEST"
        assert sma.required_periods({'period': 20}) == 20
        
        # Compute values
        values = sma.compute(candles, {'period': 5})
        
        # Should have 21 values (25 candles - 4 warmup)
        assert len(values) == 21
        
        # First value should be average of first 5 closes
        # (150 + 151 + 152 + 153 + 154) / 5 = 760 / 5 = 152
        assert values[0].value == Decimal('152')
    
    def test_base_indicator_insufficient_data(self):
        """Test that compute raises error with insufficient data"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 20
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        indicator = TestIndicator()
        
        # Create only 10 candles (need 20)
        candles = []
        for i in range(10):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            ))
        
        with pytest.raises(ValueError, match="requires at least 20 candles"):
            indicator.compute(candles, {})
    
    def test_base_indicator_sorts_candles(self):
        """Test that compute sorts candles by timestamp"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 2
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                # Verify candles are sorted
                for i in range(1, len(candles)):
                    assert candles[i].timestamp > candles[i-1].timestamp
                return []
        
        indicator = TestIndicator()
        
        # Create candles in wrong order
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('150.00'),
                high=Decimal('155.00'),
                low=Decimal('149.00'),
                close=Decimal('154.00'),
                volume=1000000
            ),
        ]
        
        # Should not raise error (candles will be sorted)
        indicator.compute(candles, {})
    
    def test_validate_period_helper(self):
        """Test _validate_period helper method"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
            
            def _validate_params(self, params: Dict[str, Any]) -> None:
                self._validate_period(params, 'period')
        
        indicator = TestIndicator()
        
        candle = Candle(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        
        # Valid period
        indicator.compute([candle], {'period': 20})
        
        # Missing period
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            indicator.compute([candle], {})
        
        # Non-integer period
        with pytest.raises(ValueError, match="period must be an integer"):
            indicator.compute([candle], {'period': '20'})
        
        # Negative period
        with pytest.raises(ValueError, match="period must be positive"):
            indicator.compute([candle], {'period': -5})


class TestIndicatorRegistry:
    """Test IndicatorRegistry"""
    
    def test_registry_creation(self):
        """Test creating an empty registry"""
        registry = IndicatorRegistry()
        assert registry.list_all() == []
    
    def test_registry_register_and_get(self):
        """Test registering and retrieving indicators"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST_IND"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        registry = IndicatorRegistry()
        indicator = TestIndicator()
        
        registry.register(indicator)
        
        # Should be able to retrieve it
        retrieved = registry.get("TEST_IND")
        assert retrieved is indicator
        assert retrieved.name == "TEST_IND"
    
    def test_registry_duplicate_registration(self):
        """Test that duplicate registration raises error"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST_IND"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        registry = IndicatorRegistry()
        indicator1 = TestIndicator()
        indicator2 = TestIndicator()
        
        registry.register(indicator1)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register(indicator2)
    
    def test_registry_list_all(self):
        """Test listing all registered indicators"""
        
        class TestIndicator1(BaseIndicator):
            @property
            def name(self) -> str:
                return "IND_1"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        class TestIndicator2(BaseIndicator):
            @property
            def name(self) -> str:
                return "IND_2"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        registry = IndicatorRegistry()
        registry.register(TestIndicator1())
        registry.register(TestIndicator2())
        
        names = registry.list_all()
        assert len(names) == 2
        assert "IND_1" in names
        assert "IND_2" in names
    
    def test_registry_get_nonexistent(self):
        """Test getting non-existent indicator returns None"""
        registry = IndicatorRegistry()
        assert registry.get("NONEXISTENT") is None
    
    def test_registry_clear(self):
        """Test clearing registry"""
        
        class TestIndicator(BaseIndicator):
            @property
            def name(self) -> str:
                return "TEST_IND"
            
            def required_periods(self, params: Dict[str, Any]) -> int:
                return 1
            
            def _compute_values(
                self,
                candles: List[Candle],
                params: Dict[str, Any]
            ) -> List[IndicatorValue]:
                return []
        
        registry = IndicatorRegistry()
        registry.register(TestIndicator())
        
        assert len(registry.list_all()) == 1
        
        registry.clear()
        
        assert len(registry.list_all()) == 0
        assert registry.get("TEST_IND") is None


class TestTimeframe:
    """Test Timeframe enum"""
    
    def test_timeframe_values(self):
        """Test that all expected timeframes are defined"""
        assert Timeframe.ONE_MINUTE.value == "1m"
        assert Timeframe.FIVE_MINUTE.value == "5m"
        assert Timeframe.FIFTEEN_MINUTE.value == "15m"
        assert Timeframe.THIRTY_MINUTE.value == "30m"
        assert Timeframe.ONE_HOUR.value == "1h"
        assert Timeframe.FOUR_HOUR.value == "4h"
        assert Timeframe.ONE_DAY.value == "1D"
        assert Timeframe.ONE_WEEK.value == "1W"
        assert Timeframe.ONE_MONTH.value == "1M"



class TestSMAIndicator:
    """Test SMA (Simple Moving Average) indicator implementation"""
    
    def test_sma_name(self):
        """Test SMA indicator name includes period"""
        sma = SMAIndicator(period=20)
        assert sma.name == "SMA_20"
        
        sma_50 = SMAIndicator(period=50)
        assert sma_50.name == "SMA_50"
    
    def test_sma_required_periods(self):
        """Test SMA required periods equals period parameter"""
        sma = SMAIndicator(period=20)
        assert sma.required_periods({'period': 20}) == 20
        
        sma_10 = SMAIndicator(period=10)
        assert sma_10.required_periods({'period': 10}) == 10
    
    def test_sma_computation_simple(self):
        """Test SMA computation with simple known values"""
        # Create 5 candles with closes: 10, 20, 30, 40, 50
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(10 * (i + 1))),
                volume=1000000
            ))
        
        # Compute 3-period SMA
        sma = SMAIndicator(period=3)
        values = sma.compute(candles, {'period': 3})
        
        # Should have 3 values (positions 2, 3, 4)
        assert len(values) == 3
        
        # SMA at position 2: (10 + 20 + 30) / 3 = 20
        assert values[0].value == Decimal('20')
        assert values[0].indicator_name == "SMA_3"
        assert values[0].timestamp == candles[2].timestamp
        
        # SMA at position 3: (20 + 30 + 40) / 3 = 30
        assert values[1].value == Decimal('30')
        assert values[1].timestamp == candles[3].timestamp
        
        # SMA at position 4: (30 + 40 + 50) / 3 = 40
        assert values[2].value == Decimal('40')
        assert values[2].timestamp == candles[4].timestamp
    
    def test_sma_computation_realistic(self):
        """Test SMA computation with realistic price data"""
        # Create 25 candles with varying closes
        closes = [
            150.00, 151.50, 149.75, 152.25, 153.00,
            154.50, 153.75, 155.00, 156.25, 155.50,
            157.00, 158.25, 157.50, 159.00, 160.25,
            159.50, 161.00, 162.25, 161.50, 163.00,
            164.25, 163.50, 165.00, 166.25, 165.50
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 20-period SMA
        sma = SMAIndicator(period=20)
        values = sma.compute(candles, {'period': 20})
        
        # Should have 6 values (25 - 19)
        assert len(values) == 6
        
        # Verify first SMA value (average of first 20 closes)
        expected_first = sum(Decimal(str(c)) for c in closes[:20]) / Decimal('20')
        assert values[0].value == expected_first
        
        # Verify last SMA value (average of last 20 closes)
        expected_last = sum(Decimal(str(c)) for c in closes[5:25]) / Decimal('20')
        assert values[5].value == expected_last
    
    def test_sma_single_period(self):
        """Test SMA with period=1 (should equal close price)"""
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i * 10)),
                volume=1000000
            ))
        
        # SMA with period=1 should equal close price
        sma = SMAIndicator(period=1)
        values = sma.compute(candles, {'period': 1})
        
        assert len(values) == 5
        for i, value in enumerate(values):
            assert value.value == candles[i].close
    
    def test_sma_insufficient_data(self):
        """Test SMA raises error with insufficient candles"""
        # Create only 10 candles
        candles = []
        for i in range(10):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            ))
        
        # Try to compute 20-period SMA (need 20 candles)
        sma = SMAIndicator(period=20)
        
        with pytest.raises(ValueError, match="requires at least 20 candles"):
            sma.compute(candles, {'period': 20})
    
    def test_sma_exact_minimum_data(self):
        """Test SMA with exactly the minimum required candles"""
        # Create exactly 20 candles
        candles = []
        for i in range(20):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Compute 20-period SMA
        sma = SMAIndicator(period=20)
        values = sma.compute(candles, {'period': 20})
        
        # Should have exactly 1 value
        assert len(values) == 1
        
        # Verify it's the average of all 20 closes
        expected = sum(Decimal(str(100 + i)) for i in range(20)) / Decimal('20')
        assert values[0].value == expected
    
    def test_sma_invalid_period_missing(self):
        """Test SMA raises error when period parameter is missing"""
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        sma = SMAIndicator(period=20)
        
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            sma.compute(candles, {})
    
    def test_sma_invalid_period_not_integer(self):
        """Test SMA raises error when period is not an integer"""
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        sma = SMAIndicator(period=20)
        
        with pytest.raises(ValueError, match="period must be an integer"):
            sma.compute(candles, {'period': '20'})
    
    def test_sma_invalid_period_negative(self):
        """Test SMA raises error when period is negative"""
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        sma = SMAIndicator(period=20)
        
        with pytest.raises(ValueError, match="period must be positive"):
            sma.compute(candles, {'period': -5})
    
    def test_sma_invalid_period_zero(self):
        """Test SMA raises error when period is zero"""
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        sma = SMAIndicator(period=20)
        
        with pytest.raises(ValueError, match="period must be positive"):
            sma.compute(candles, {'period': 0})
    
    def test_sma_unsorted_candles(self):
        """Test SMA handles unsorted candles correctly"""
        # Create candles in wrong order
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('30'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('10'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('20'),
                volume=1000000
            ),
        ]
        
        # Compute 3-period SMA
        sma = SMAIndicator(period=3)
        values = sma.compute(candles, {'period': 3})
        
        # Should have 1 value
        assert len(values) == 1
        
        # Should be average of sorted closes: (10 + 20 + 30) / 3 = 20
        assert values[0].value == Decimal('20')
        
        # Timestamp should be from the last candle (chronologically)
        assert values[0].timestamp == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
    
    def test_sma_decimal_precision(self):
        """Test SMA maintains decimal precision"""
        # Create candles with values that don't divide evenly
        candles = []
        for i in range(3):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('100.33'),
                volume=1000000
            ))
        
        # Compute 3-period SMA
        sma = SMAIndicator(period=3)
        values = sma.compute(candles, {'period': 3})
        
        # Should have 1 value
        assert len(values) == 1
        
        # (100.33 + 100.33 + 100.33) / 3 = 100.33
        assert values[0].value == Decimal('100.33')
    
    def test_sma_large_period(self):
        """Test SMA with large period (50)"""
        # Create 100 candles
        candles = []
        for i in range(100):
            candles.append(Candle(
                timestamp=datetime(2024, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Compute 50-period SMA
        sma = SMAIndicator(period=50)
        values = sma.compute(candles, {'period': 50})
        
        # Should have 51 values (100 - 49)
        assert len(values) == 51
        
        # Verify first value (average of first 50 closes)
        expected_first = sum(Decimal(str(100 + i)) for i in range(50)) / Decimal('50')
        assert values[0].value == expected_first
        
        # Verify last value (average of last 50 closes)
        expected_last = sum(Decimal(str(100 + i)) for i in range(50, 100)) / Decimal('50')
        assert values[50].value == expected_last
    
    def test_sma_metadata_is_none(self):
        """Test SMA indicator values have no metadata"""
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            ))
        
        sma = SMAIndicator(period=3)
        values = sma.compute(candles, {'period': 3})
        
        # All values should have metadata=None
        for value in values:
            assert value.metadata is None
    
    def test_sma_with_default_period(self):
        """Test SMA uses default period when not specified in params"""
        candles = []
        for i in range(25):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Create SMA with default period=20
        sma = SMAIndicator(period=20)
        
        # Compute with period in params
        values = sma.compute(candles, {'period': 20})
        
        # Should have 6 values
        assert len(values) == 6



class TestEMAIndicator:
    """Test EMA (Exponential Moving Average) indicator implementation"""
    
    def test_ema_name(self):
        """Test EMA indicator name includes period"""
        
        ema = EMAIndicator(period=12)
        assert ema.name == "EMA_12"
        
        ema_26 = EMAIndicator(period=26)
        assert ema_26.name == "EMA_26"
    
    def test_ema_required_periods(self):
        """Test EMA required periods equals period parameter"""
        from app.services.indicators import EMAIndicator
        
        ema = EMAIndicator(period=12)
        assert ema.required_periods({'period': 12}) == 12
        
        ema_20 = EMAIndicator(period=20)
        assert ema_20.required_periods({'period': 20}) == 20
    
    def test_ema_computation_simple(self):
        """Test EMA computation with simple known values"""
        from app.services.indicators import EMAIndicator
        
        # Create 5 candles with closes: 10, 20, 30, 40, 50
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(10 * (i + 1))),
                volume=1000000
            ))
        
        # Compute 3-period EMA
        # α = 2 / (3 + 1) = 0.5
        ema = EMAIndicator(period=3)
        values = ema.compute(candles, {'period': 3})
        
        # Should have 3 values (positions 2, 3, 4)
        assert len(values) == 3
        
        # EMA at position 2: SMA(10, 20, 30) = 20
        assert values[0].value == Decimal('20')
        assert values[0].indicator_name == "EMA_3"
        assert values[0].timestamp == candles[2].timestamp
        
        # EMA at position 3: 0.5 * 40 + 0.5 * 20 = 30
        assert values[1].value == Decimal('30')
        assert values[1].timestamp == candles[3].timestamp
        
        # EMA at position 4: 0.5 * 50 + 0.5 * 30 = 40
        assert values[2].value == Decimal('40')
        assert values[2].timestamp == candles[4].timestamp
    
    def test_ema_first_value_is_sma(self):
        """Test that first EMA value equals SMA of first N prices"""
        from app.services.indicators import EMAIndicator
        
        # Create candles with known closes
        closes = [100, 102, 104, 106, 108, 110, 112, 114, 116, 118]
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 5-period EMA
        ema = EMAIndicator(period=5)
        ema_values = ema.compute(candles, {'period': 5})
        
        # First EMA value should equal SMA of first 5 closes
        expected_sma = sum(Decimal(str(c)) for c in closes[:5]) / Decimal('5')
        assert ema_values[0].value == expected_sma
    
    def test_ema_smoothing_factor(self):
        """Test EMA uses correct smoothing factor α = 2/(period+1)"""
        from app.services.indicators import EMAIndicator
        
        # Create candles with constant close price, then a jump
        candles = []
        for i in range(10):
            close = Decimal('100.00') if i < 5 else Decimal('110.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('115.00'),
                low=Decimal('95.00'),
                close=close,
                volume=1000000
            ))
        
        # Compute 5-period EMA
        # α = 2 / (5 + 1) = 1/3 ≈ 0.333...
        ema = EMAIndicator(period=5)
        values = ema.compute(candles, {'period': 5})
        
        # First value (position 4): SMA of first 5 = 100
        assert values[0].value == Decimal('100.00')
        
        # Second value (position 5): α * 110 + (1-α) * 100
        # = (1/3) * 110 + (2/3) * 100
        # = 36.666... + 66.666... = 103.333...
        alpha = Decimal('2') / Decimal('6')
        expected = alpha * Decimal('110.00') + (Decimal('1') - alpha) * Decimal('100.00')
        assert abs(values[1].value - expected) < Decimal('0.01')
    
    def test_ema_more_responsive_than_sma(self):
        """Test that EMA responds faster to price changes than SMA"""
        from app.services.indicators import EMAIndicator
        
        # Create candles with a price trend
        candles = []
        for i in range(25):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i * 2)),  # Increasing trend
                volume=1000000
            ))
        
        # Compute both EMA and SMA with same period
        ema = EMAIndicator(period=10)
        ema_values = ema.compute(candles, {'period': 10})
        
        sma = SMAIndicator(period=10)
        sma_values = sma.compute(candles, {'period': 10})
        
        # Both should have same number of values
        assert len(ema_values) == len(sma_values)
        
        # First values should be equal (EMA starts with SMA)
        assert ema_values[0].value == sma_values[0].value
        
        # In an uptrend, EMA should be higher than SMA (more responsive)
        # Check the last few values
        for i in range(-5, 0):
            assert ema_values[i].value > sma_values[i].value
    
    def test_ema_computation_realistic(self):
        """Test EMA computation with realistic price data"""
        from app.services.indicators import EMAIndicator
        
        # Create 25 candles with varying closes
        closes = [
            150.00, 151.50, 149.75, 152.25, 153.00,
            154.50, 153.75, 155.00, 156.25, 155.50,
            157.00, 158.25, 157.50, 159.00, 160.25,
            159.50, 161.00, 162.25, 161.50, 163.00,
            164.25, 163.50, 165.00, 166.25, 165.50
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 12-period EMA
        ema = EMAIndicator(period=12)
        values = ema.compute(candles, {'period': 12})
        
        # Should have 14 values (25 - 11)
        assert len(values) == 14
        
        # Verify first EMA value equals SMA of first 12 closes
        expected_first = sum(Decimal(str(c)) for c in closes[:12]) / Decimal('12')
        assert values[0].value == expected_first
        
        # Verify EMA values are monotonically increasing (since prices trend up)
        for i in range(1, len(values)):
            assert values[i].value > values[i-1].value
    
    def test_ema_single_period(self):
        """Test EMA with period=1 (should equal close price after first)"""
        from app.services.indicators import EMAIndicator
        
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i * 10)),
                volume=1000000
            ))
        
        # EMA with period=1: α = 2/(1+1) = 1.0
        # So EMA(i) = 1.0 * close(i) + 0.0 * EMA(i-1) = close(i)
        ema = EMAIndicator(period=1)
        values = ema.compute(candles, {'period': 1})
        
        assert len(values) == 5
        
        # First value is SMA of first candle = close price
        assert values[0].value == candles[0].close
        
        # All subsequent values should equal close price (α = 1.0)
        for i in range(1, len(values)):
            assert values[i].value == candles[i].close
    
    def test_ema_insufficient_data(self):
        """Test EMA raises error with insufficient candles"""
        from app.services.indicators import EMAIndicator
        
        # Create only 10 candles
        candles = []
        for i in range(10):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            ))
        
        # Try to compute 12-period EMA (need 12 candles)
        ema = EMAIndicator(period=12)
        
        with pytest.raises(ValueError, match="requires at least 12 candles"):
            ema.compute(candles, {'period': 12})
    
    def test_ema_exact_minimum_data(self):
        """Test EMA with exactly the minimum required candles"""
        from app.services.indicators import EMAIndicator
        
        # Create exactly 12 candles
        candles = []
        for i in range(12):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Compute 12-period EMA
        ema = EMAIndicator(period=12)
        values = ema.compute(candles, {'period': 12})
        
        # Should have exactly 1 value (the initial SMA)
        assert len(values) == 1
        
        # Verify it's the SMA of all 12 closes
        expected = sum(Decimal(str(100 + i)) for i in range(12)) / Decimal('12')
        assert values[0].value == expected
    
    def test_ema_invalid_period_missing(self):
        """Test EMA raises error when period parameter is missing"""
        from app.services.indicators import EMAIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        ema = EMAIndicator(period=12)
        
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            ema.compute(candles, {})
    
    def test_ema_invalid_period_not_integer(self):
        """Test EMA raises error when period is not an integer"""
        from app.services.indicators import EMAIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        ema = EMAIndicator(period=12)
        
        with pytest.raises(ValueError, match="period must be an integer"):
            ema.compute(candles, {'period': '12'})
    
    def test_ema_invalid_period_negative(self):
        """Test EMA raises error when period is negative"""
        from app.services.indicators import EMAIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        ema = EMAIndicator(period=12)
        
        with pytest.raises(ValueError, match="period must be positive"):
            ema.compute(candles, {'period': -5})
    
    def test_ema_invalid_period_zero(self):
        """Test EMA raises error when period is zero"""
        from app.services.indicators import EMAIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        ema = EMAIndicator(period=12)
        
        with pytest.raises(ValueError, match="period must be positive"):
            ema.compute(candles, {'period': 0})
    
    def test_ema_unsorted_candles(self):
        """Test EMA handles unsorted candles correctly"""
        from app.services.indicators import EMAIndicator
        
        # Create candles in wrong order
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('30'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('10'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('20'),
                volume=1000000
            ),
        ]
        
        # Compute 3-period EMA
        ema = EMAIndicator(period=3)
        values = ema.compute(candles, {'period': 3})
        
        # Should have 1 value
        assert len(values) == 1
        
        # Should be SMA of sorted closes: (10 + 20 + 30) / 3 = 20
        assert values[0].value == Decimal('20')
        
        # Timestamp should be from the last candle (chronologically)
        assert values[0].timestamp == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
    
    def test_ema_decimal_precision(self):
        """Test EMA maintains decimal precision"""
        from app.services.indicators import EMAIndicator
        
        # Create candles with values that require precision
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('100.33'),
                volume=1000000
            ))
        
        # Compute 3-period EMA
        ema = EMAIndicator(period=3)
        values = ema.compute(candles, {'period': 3})
        
        # Should have 3 values
        assert len(values) == 3
        
        # All values should be 100.33 (constant price)
        for value in values:
            assert value.value == Decimal('100.33')
    
    def test_ema_large_period(self):
        """Test EMA with large period (50)"""
        from app.services.indicators import EMAIndicator
        
        # Create 100 candles
        candles = []
        for i in range(100):
            candles.append(Candle(
                timestamp=datetime(2024, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Compute 50-period EMA
        ema = EMAIndicator(period=50)
        values = ema.compute(candles, {'period': 50})
        
        # Should have 51 values (100 - 49)
        assert len(values) == 51
        
        # Verify first value equals SMA of first 50 closes
        expected_first = sum(Decimal(str(100 + i)) for i in range(50)) / Decimal('50')
        assert values[0].value == expected_first
        
        # Verify EMA values increase (uptrend)
        for i in range(1, len(values)):
            assert values[i].value > values[i-1].value
    
    def test_ema_metadata_is_none(self):
        """Test EMA indicator values have no metadata"""
        from app.services.indicators import EMAIndicator
        
        candles = []
        for i in range(5):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            ))
        
        ema = EMAIndicator(period=3)
        values = ema.compute(candles, {'period': 3})
        
        # All values should have metadata=None
        for value in values:
            assert value.metadata is None
    
    def test_ema_recursive_formula_verification(self):
        """Test EMA recursive formula: EMA(i) = α * close(i) + (1 - α) * EMA(i-1)"""
        from app.services.indicators import EMAIndicator
        
        # Create candles with known values
        closes = [100, 105, 110, 115, 120, 125]
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('130.00'),
                low=Decimal('95.00'),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 3-period EMA
        # α = 2 / (3 + 1) = 0.5
        ema = EMAIndicator(period=3)
        values = ema.compute(candles, {'period': 3})
        
        # Manually verify the recursive formula
        alpha = Decimal('2') / Decimal('4')  # 0.5
        
        # First value: SMA(100, 105, 110) = 105
        expected_0 = (Decimal('100') + Decimal('105') + Decimal('110')) / Decimal('3')
        assert values[0].value == expected_0
        
        # Second value: 0.5 * 115 + 0.5 * 105 = 110
        expected_1 = alpha * Decimal('115') + (Decimal('1') - alpha) * expected_0
        assert values[1].value == expected_1
        
        # Third value: 0.5 * 120 + 0.5 * 110 = 115
        expected_2 = alpha * Decimal('120') + (Decimal('1') - alpha) * expected_1
        assert values[2].value == expected_2
        
        # Fourth value: 0.5 * 125 + 0.5 * 115 = 120
        expected_3 = alpha * Decimal('125') + (Decimal('1') - alpha) * expected_2
        assert values[3].value == expected_3



class TestRSIIndicator:
    """Test RSI (Relative Strength Index) indicator implementation"""
    
    def test_rsi_name(self):
        """Test RSI indicator name includes period"""
        from app.services.indicators import RSIIndicator
        
        rsi = RSIIndicator(period=14)
        assert rsi.name == "RSI_14"
        
        rsi_20 = RSIIndicator(period=20)
        assert rsi_20.name == "RSI_20"
    
    def test_rsi_required_periods(self):
        """Test RSI required periods equals period + 1"""
        from app.services.indicators import RSIIndicator
        
        rsi = RSIIndicator(period=14)
        assert rsi.required_periods({'period': 14}) == 15
        
        rsi_10 = RSIIndicator(period=10)
        assert rsi_10.required_periods({'period': 10}) == 11
    
    def test_rsi_computation_all_gains(self):
        """Test RSI with all gains (should equal 100)"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with steadily increasing prices (all gains)
        candles = []
        for i in range(16):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i * 5)),  # 100, 105, 110, 115, ...
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # Should have 2 values (16 - 14)
        assert len(values) == 2
        
        # All gains, no losses → RSI = 100
        assert values[0].value == Decimal('100')
        assert values[1].value == Decimal('100')
    
    def test_rsi_computation_all_losses(self):
        """Test RSI with all losses (should equal 0)"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with steadily decreasing prices (all losses)
        candles = []
        for i in range(16):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('50.00'),
                close=Decimal(str(100 - i * 2)),  # 100, 98, 96, 94, ...
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # Should have 2 values
        assert len(values) == 2
        
        # All losses, no gains → RSI = 0
        assert values[0].value == Decimal('0')
        assert values[1].value == Decimal('0')
    
    def test_rsi_range_invariant(self):
        """Test RSI values are always in range [0, 100]"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with random-like price movements
        closes = [
            100, 102, 101, 103, 102, 104, 103, 105, 104, 106,
            105, 107, 106, 108, 107, 109, 108, 110, 109, 111
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # All RSI values must be in [0, 100]
        for value in values:
            assert Decimal('0') <= value.value <= Decimal('100')
    
    def test_rsi_computation_simple(self):
        """Test RSI computation with simple known values"""
        from app.services.indicators import RSIIndicator
        
        # Create a simple scenario with known gains/losses
        # Closes: 100, 102, 101, 103, 102 (gains: 2, 0, 2, 0; losses: 0, 1, 0, 1)
        closes = [100, 102, 101, 103, 102]
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 3-period RSI
        rsi = RSIIndicator(period=3)
        values = rsi.compute(candles, {'period': 3})
        
        # Should have 1 value (5 candles - 4 for warmup)
        assert len(values) == 1
        
        # Changes: +2, -1, +2, -1
        # First 3 changes: +2, -1, +2
        # Avg gain = (2 + 0 + 2) / 3 = 4/3
        # Avg loss = (0 + 1 + 0) / 3 = 1/3
        # RS = (4/3) / (1/3) = 4
        # RSI = 100 - 100/(1+4) = 100 - 20 = 80
        expected_rsi = Decimal('80')
        assert values[0].value == expected_rsi
    
    def test_rsi_computation_realistic(self):
        """Test RSI computation with realistic price data"""
        from app.services.indicators import RSIIndicator
        
        # Create 20 candles with varying closes
        closes = [
            150.00, 151.50, 149.75, 152.25, 153.00,
            154.50, 153.75, 155.00, 156.25, 155.50,
            157.00, 158.25, 157.50, 159.00, 160.25,
            159.50, 161.00, 162.25, 161.50, 163.00
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # Should have 6 values (20 - 14)
        assert len(values) == 6
        
        # All values should be in valid range
        for value in values:
            assert Decimal('0') <= value.value <= Decimal('100')
        
        # In an uptrend, RSI should generally be above 50
        # (most values should be > 50)
        above_50 = sum(1 for v in values if v.value > Decimal('50'))
        assert above_50 >= 4  # At least 4 out of 6 should be above 50
    
    def test_rsi_period_1(self):
        """Test RSI with period=1"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with alternating gains and losses
        closes = [100, 102, 101, 103, 102]
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 1-period RSI
        rsi = RSIIndicator(period=1)
        values = rsi.compute(candles, {'period': 1})
        
        # Should have 4 values (5 candles - 1 for first change)
        assert len(values) == 4
        
        # With period=1, each RSI is based on single change
        # Change +2 → RSI = 100 (all gain)
        assert values[0].value == Decimal('100')
        
        # Change -1 → RSI = 0 (all loss)
        assert values[1].value == Decimal('0')
        
        # Change +2 → RSI = 100 (all gain)
        assert values[2].value == Decimal('100')
        
        # Change -1 → RSI = 0 (all loss)
        assert values[3].value == Decimal('0')
    
    def test_rsi_insufficient_data(self):
        """Test RSI raises error with insufficient candles"""
        from app.services.indicators import RSIIndicator
        
        # Create only 10 candles
        candles = []
        for i in range(10):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            ))
        
        # Try to compute 14-period RSI (need 15 candles)
        rsi = RSIIndicator(period=14)
        
        with pytest.raises(ValueError, match="requires at least 15 candles"):
            rsi.compute(candles, {'period': 14})
    
    def test_rsi_exact_minimum_data(self):
        """Test RSI with exactly the minimum required candles"""
        from app.services.indicators import RSIIndicator
        
        # Create exactly 15 candles (14 + 1)
        candles = []
        for i in range(15):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # Should have exactly 1 value
        assert len(values) == 1
        
        # All gains → RSI = 100
        assert values[0].value == Decimal('100')
    
    def test_rsi_invalid_period_missing(self):
        """Test RSI raises error when period parameter is missing"""
        from app.services.indicators import RSIIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        rsi = RSIIndicator(period=14)
        
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            rsi.compute(candles, {})
    
    def test_rsi_invalid_period_not_integer(self):
        """Test RSI raises error when period is not an integer"""
        from app.services.indicators import RSIIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        rsi = RSIIndicator(period=14)
        
        with pytest.raises(ValueError, match="period must be an integer"):
            rsi.compute(candles, {'period': '14'})
    
    def test_rsi_invalid_period_negative(self):
        """Test RSI raises error when period is negative"""
        from app.services.indicators import RSIIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        rsi = RSIIndicator(period=14)
        
        with pytest.raises(ValueError, match="period must be positive"):
            rsi.compute(candles, {'period': -5})
    
    def test_rsi_invalid_period_zero(self):
        """Test RSI raises error when period is zero"""
        from app.services.indicators import RSIIndicator
        
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('105.00'),
                volume=1000000
            )
        ]
        
        rsi = RSIIndicator(period=14)
        
        with pytest.raises(ValueError, match="period must be positive"):
            rsi.compute(candles, {'period': 0})
    
    def test_rsi_unsorted_candles(self):
        """Test RSI handles unsorted candles correctly"""
        from app.services.indicators import RSIIndicator
        
        # Create candles in wrong order
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('103'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('100'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('102'),
                volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 4, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('101'),
                volume=1000000
            ),
        ]
        
        # Compute 2-period RSI
        rsi = RSIIndicator(period=2)
        values = rsi.compute(candles, {'period': 2})
        
        # Should have 1 value
        assert len(values) == 1
        
        # After sorting: 100, 102, 103, 101
        # Changes: +2, +1, -2
        # First 2 changes: +2, +1
        # Avg gain = (2 + 1) / 2 = 1.5
        # Avg loss = 0
        # RSI = 100 (no losses)
        assert values[0].value == Decimal('100')
        
        # Timestamp should be from the last candle (chronologically)
        assert values[0].timestamp == datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
    
    def test_rsi_decimal_precision(self):
        """Test RSI maintains decimal precision"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with precise decimal values
        closes = [
            Decimal('100.00'), Decimal('100.50'), Decimal('100.25'),
            Decimal('100.75'), Decimal('100.50')
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('101.00'),
                low=Decimal('99.00'),
                close=close,
                volume=1000000
            ))
        
        # Compute 3-period RSI
        rsi = RSIIndicator(period=3)
        values = rsi.compute(candles, {'period': 3})
        
        # Should have 1 value
        assert len(values) == 1
        
        # Verify RSI is in valid range
        assert Decimal('0') <= values[0].value <= Decimal('100')
    
    def test_rsi_metadata_is_none(self):
        """Test RSI indicator values have no metadata"""
        from app.services.indicators import RSIIndicator
        
        candles = []
        for i in range(16):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # All values should have metadata=None
        for value in values:
            assert value.metadata is None
    
    def test_rsi_smoothed_moving_average(self):
        """Test RSI uses smoothed moving average for subsequent values"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with known price changes
        closes = [100, 102, 104, 103, 105, 104, 106]
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute 3-period RSI
        rsi = RSIIndicator(period=3)
        values = rsi.compute(candles, {'period': 3})
        
        # Should have 3 values
        assert len(values) == 3
        
        # All values should be in valid range
        for value in values:
            assert Decimal('0') <= value.value <= Decimal('100')
    
    def test_rsi_overbought_oversold_levels(self):
        """Test RSI correctly identifies overbought/oversold conditions"""
        from app.services.indicators import RSIIndicator
        
        # Create strong uptrend (overbought)
        candles_up = []
        for i in range(20):
            candles_up.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal(str(100 + i * 3)),
                volume=1000000
            ))
        
        rsi = RSIIndicator(period=14)
        values_up = rsi.compute(candles_up, {'period': 14})
        
        # In strong uptrend, RSI should be high (> 70 is overbought)
        assert values_up[-1].value > Decimal('70')
        
        # Create strong downtrend (oversold)
        candles_down = []
        for i in range(20):
            candles_down.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('110.00'),
                low=Decimal('40.00'),
                close=Decimal(str(100 - i * 2)),
                volume=1000000
            ))
        
        values_down = rsi.compute(candles_down, {'period': 14})
        
        # In strong downtrend, RSI should be low (< 30 is oversold)
        assert values_down[-1].value < Decimal('30')
    
    def test_rsi_constant_price(self):
        """Test RSI with constant price (no changes)"""
        from app.services.indicators import RSIIndicator
        
        # Create candles with constant price
        candles = []
        for i in range(16):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('100.00'),
                low=Decimal('100.00'),
                close=Decimal('100.00'),
                volume=1000000
            ))
        
        # Compute 14-period RSI
        rsi = RSIIndicator(period=14)
        values = rsi.compute(candles, {'period': 14})
        
        # Should have 2 values
        assert len(values) == 2
        
        # With no changes, avg_gain = 0, avg_loss = 0
        # RSI should be 100 (handled as special case)
        assert values[0].value == Decimal('100')
        assert values[1].value == Decimal('100')


class TestMACDIndicator:
    """Test MACD (Moving Average Convergence Divergence) indicator implementation"""
    
    def test_macd_name(self):
        """Test MACD indicator name includes all parameters"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        assert macd.name == "MACD_12_26_9"
        
        macd_custom = MACDIndicator(fast=8, slow=17, signal=5)
        assert macd_custom.name == "MACD_8_17_5"
    
    def test_macd_required_periods(self):
        """Test MACD required periods equals slow + signal - 1"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        # Required: 26 + 9 - 1 = 34
        assert macd.required_periods({'fast': 12, 'slow': 26, 'signal': 9}) == 34
        
        macd_custom = MACDIndicator(fast=8, slow=17, signal=5)
        # Required: 17 + 5 - 1 = 21
        assert macd_custom.required_periods({'fast': 8, 'slow': 17, 'signal': 5}) == 21
    
    def test_macd_parameter_validation_missing_fast(self):
        """Test MACD raises error when fast parameter is missing"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(40)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: fast"):
            macd.compute(candles, {'slow': 26, 'signal': 9})
    
    def test_macd_parameter_validation_missing_slow(self):
        """Test MACD raises error when slow parameter is missing"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(40)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: slow"):
            macd.compute(candles, {'fast': 12, 'signal': 9})
    
    def test_macd_parameter_validation_missing_signal(self):
        """Test MACD raises error when signal parameter is missing"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(40)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: signal"):
            macd.compute(candles, {'fast': 12, 'slow': 26})
    
    def test_macd_parameter_validation_fast_not_positive(self):
        """Test MACD raises error when fast is not positive"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(40)
        ]
        
        with pytest.raises(ValueError, match="fast must be positive"):
            macd.compute(candles, {'fast': 0, 'slow': 26, 'signal': 9})
    
    def test_macd_parameter_validation_fast_greater_than_slow(self):
        """Test MACD raises error when fast >= slow"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(40)
        ]
        
        with pytest.raises(ValueError, match="fast period.*must be less than slow period"):
            macd.compute(candles, {'fast': 26, 'slow': 12, 'signal': 9})
        
        with pytest.raises(ValueError, match="fast period.*must be less than slow period"):
            macd.compute(candles, {'fast': 26, 'slow': 26, 'signal': 9})
    
    def test_macd_insufficient_data(self):
        """Test MACD raises error with insufficient candles"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        
        # Only 30 candles, but need 34 (26 + 9 - 1)
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(30)
        ]
        
        with pytest.raises(ValueError, match="requires at least 34 candles"):
            macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
    
    def test_macd_computation_basic(self):
        """Test MACD computation with simple uptrend"""
        from app.services.indicators import MACDIndicator
        
        # Create 40 candles with steadily increasing prices
        candles = []
        for i in range(40):
            close = Decimal(str(100 + i * 2))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD with standard parameters
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Should have 40 - 34 + 1 = 7 values
        assert len(values) == 7
        
        # In an uptrend, MACD should be positive (fast EMA > slow EMA)
        for value in values:
            assert value.value > Decimal('0'), f"MACD should be positive in uptrend, got {value.value}"
    
    def test_macd_computation_downtrend(self):
        """Test MACD computation with downtrend"""
        from app.services.indicators import MACDIndicator
        
        # Create 40 candles with steadily decreasing prices
        candles = []
        for i in range(40):
            close = Decimal(str(200 - i * 2))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close + Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD with standard parameters
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Should have 7 values
        assert len(values) == 7
        
        # In a downtrend, MACD should be negative (fast EMA < slow EMA)
        for value in values:
            assert value.value < Decimal('0'), f"MACD should be negative in downtrend, got {value.value}"
    
    def test_macd_metadata_contains_signal_and_histogram(self):
        """Test MACD values include signal_line and histogram in metadata"""
        from app.services.indicators import MACDIndicator
        
        # Create 40 candles
        candles = []
        for i in range(40):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Check all values have metadata with signal_line and histogram
        for value in values:
            assert value.metadata is not None
            assert 'signal_line' in value.metadata
            assert 'histogram' in value.metadata
            
            # Histogram should equal MACD - signal_line
            expected_histogram = float(value.value) - value.metadata['signal_line']
            assert abs(value.metadata['histogram'] - expected_histogram) < 0.0001
    
    def test_macd_histogram_calculation(self):
        """Test MACD histogram is correctly calculated as MACD - signal"""
        from app.services.indicators import MACDIndicator
        
        # Create 50 candles with varying prices
        closes = [
            100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
            111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
            119, 121, 123, 122, 124, 126, 125, 127, 129, 128,
            130, 132, 131, 133, 135, 134, 136, 138, 137, 139,
            141, 140, 142, 144, 143, 145, 147, 146, 148, 150
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Verify histogram calculation for all values
        for value in values:
            macd_value = float(value.value)
            signal_value = value.metadata['signal_line']
            histogram_value = value.metadata['histogram']
            
            expected_histogram = macd_value - signal_value
            assert abs(histogram_value - expected_histogram) < 0.0001
    
    def test_macd_custom_parameters(self):
        """Test MACD with custom parameters"""
        from app.services.indicators import MACDIndicator
        
        # Create 30 candles
        candles = []
        for i in range(30):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD with custom parameters (8, 17, 5)
        macd = MACDIndicator(fast=8, slow=17, signal=5)
        values = macd.compute(candles, {'fast': 8, 'slow': 17, 'signal': 5})
        
        # Required: 17 + 5 - 1 = 21, so should have 30 - 21 + 1 = 10 values
        assert len(values) == 10
        
        # All values should have metadata
        for value in values:
            assert value.metadata is not None
            assert 'signal_line' in value.metadata
            assert 'histogram' in value.metadata
    
    def test_macd_timestamps_match_candles(self):
        """Test MACD timestamps match input candle timestamps"""
        from app.services.indicators import MACDIndicator
        
        # Create 40 candles with specific timestamps
        candles = []
        for i in range(40):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 12, 30, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Verify timestamps match candles (starting from position 33)
        for i, value in enumerate(values):
            expected_timestamp = candles[33 + i].timestamp
            assert value.timestamp == expected_timestamp
    
    def test_macd_decimal_precision(self):
        """Test MACD maintains decimal precision"""
        from app.services.indicators import MACDIndicator
        
        # Create candles with precise decimal values
        candles = []
        for i in range(40):
            close = Decimal('100.123456') + Decimal(str(i)) * Decimal('0.5')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('0.5'),
                high=close + Decimal('1.0'),
                low=close - Decimal('1.0'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # All values should be Decimal type
        for value in values:
            assert isinstance(value.value, Decimal)
            # Metadata values are floats for JSON serialization
            assert isinstance(value.metadata['signal_line'], float)
            assert isinstance(value.metadata['histogram'], float)
    
    def test_macd_flat_prices(self):
        """Test MACD with flat prices (no movement)"""
        from app.services.indicators import MACDIndicator
        
        # Create 40 candles with constant price
        candles = []
        for i in range(40):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('100.00'),
                low=Decimal('100.00'),
                close=Decimal('100.00'),
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # With flat prices, MACD should be 0 (fast EMA = slow EMA)
        for value in values:
            assert value.value == Decimal('0')
            assert value.metadata['signal_line'] == 0.0
            assert value.metadata['histogram'] == 0.0
    
    def test_macd_realistic_data(self):
        """Test MACD with realistic price movements"""
        from app.services.indicators import MACDIndicator
        
        # Create realistic price data with trend changes
        closes = [
            150.00, 151.50, 149.75, 152.25, 153.00, 154.50, 153.75, 155.00,
            156.25, 155.50, 157.00, 158.25, 157.50, 159.00, 160.25, 159.50,
            161.00, 162.25, 161.50, 163.00, 164.50, 163.75, 165.00, 166.25,
            165.50, 167.00, 168.25, 167.50, 169.00, 170.25, 169.50, 171.00,
            172.25, 171.50, 173.00, 174.50, 173.75, 175.00, 176.25, 175.50
        ]
        
        candles = []
        for i, close in enumerate(closes):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal(str(close - 1)),
                high=Decimal(str(close + 2)),
                low=Decimal(str(close - 2)),
                close=Decimal(str(close)),
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Should have 7 values
        assert len(values) == 7
        
        # In an uptrend, MACD should generally be positive
        positive_count = sum(1 for v in values if v.value > Decimal('0'))
        assert positive_count >= 5  # Most should be positive
        
        # All values should have valid metadata
        for value in values:
            assert value.metadata is not None
            assert 'signal_line' in value.metadata
            assert 'histogram' in value.metadata
    
    def test_macd_indicator_name_property(self):
        """Test MACD indicator name property"""
        from app.services.indicators import MACDIndicator
        
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        assert macd.name == "MACD_12_26_9"
        
        # Test that name is consistent across multiple calls
        assert macd.name == macd.name
    
    def test_macd_with_minimum_required_candles(self):
        """Test MACD with exactly the minimum required candles"""
        from app.services.indicators import MACDIndicator
        
        # Create exactly 34 candles (26 + 9 - 1)
        candles = []
        for i in range(34):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute MACD
        macd = MACDIndicator(fast=12, slow=26, signal=9)
        values = macd.compute(candles, {'fast': 12, 'slow': 26, 'signal': 9})
        
        # Should have exactly 1 value
        assert len(values) == 1
        
        # Value should have all required components
        assert values[0].value is not None
        assert values[0].metadata is not None
        assert 'signal_line' in values[0].metadata
        assert 'histogram' in values[0].metadata



class TestBollingerBandsIndicator:
    """Test Bollinger Bands indicator implementation"""
    
    def test_bollinger_bands_name(self):
        """Test Bollinger Bands indicator name includes all parameters"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        assert bb.name == "BB_20_2.0"
        
        bb_custom = BollingerBandsIndicator(period=10, std_dev=1.5)
        assert bb_custom.name == "BB_10_1.5"
    
    def test_bollinger_bands_required_periods(self):
        """Test Bollinger Bands required periods equals period"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        assert bb.required_periods({'period': 20, 'std_dev': 2.0}) == 20
        
        bb_custom = BollingerBandsIndicator(period=10, std_dev=1.5)
        assert bb_custom.required_periods({'period': 10, 'std_dev': 1.5}) == 10
    
    def test_bollinger_bands_parameter_validation_missing_period(self):
        """Test Bollinger Bands raises error when period parameter is missing"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(25)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            bb.compute(candles, {'std_dev': 2.0})
    
    def test_bollinger_bands_parameter_validation_missing_std_dev(self):
        """Test Bollinger Bands raises error when std_dev parameter is missing"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(25)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: std_dev"):
            bb.compute(candles, {'period': 20})
    
    def test_bollinger_bands_parameter_validation_period_not_positive(self):
        """Test Bollinger Bands raises error when period is not positive"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(25)
        ]
        
        with pytest.raises(ValueError, match="period must be positive"):
            bb.compute(candles, {'period': 0, 'std_dev': 2.0})
    
    def test_bollinger_bands_parameter_validation_std_dev_not_positive(self):
        """Test Bollinger Bands raises error when std_dev is not positive"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(25)
        ]
        
        with pytest.raises(ValueError, match="std_dev must be positive"):
            bb.compute(candles, {'period': 20, 'std_dev': 0})
        
        with pytest.raises(ValueError, match="std_dev must be positive"):
            bb.compute(candles, {'period': 20, 'std_dev': -1.0})
    
    def test_bollinger_bands_insufficient_data(self):
        """Test Bollinger Bands raises error with insufficient candles"""
        from app.services.indicators import BollingerBandsIndicator
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        
        # Only 15 candles, but need 20
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(15)
        ]
        
        with pytest.raises(ValueError, match="requires at least 20 candles"):
            bb.compute(candles, {'period': 20, 'std_dev': 2.0})
    
    def test_bollinger_bands_computation_basic(self):
        """Test Bollinger Bands computation with simple data"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 25 candles with constant price (no volatility)
        candles = []
        for i in range(25):
            close = Decimal('100.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close,
                high=close + Decimal('1'),
                low=close - Decimal('1'),
                close=close,
                volume=1000000
            ))
        
        # Compute Bollinger Bands with standard parameters
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Should have 25 - 20 + 1 = 6 values
        assert len(values) == 6
        
        # With constant prices, all bands should converge to the same value
        for value in values:
            assert value.value == Decimal('100.00'), "Middle band should be 100"
            assert 'upper_band' in value.metadata
            assert 'lower_band' in value.metadata
            # With zero volatility, all bands should be equal
            assert abs(value.metadata['upper_band'] - 100.0) < 0.01
            assert abs(value.metadata['lower_band'] - 100.0) < 0.01
    
    def test_bollinger_bands_ordering_invariant(self):
        """Test that lower_band < middle_band < upper_band always holds"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 25 candles with varying prices
        candles = []
        for i in range(25):
            close = Decimal(str(100 + (i % 10) * 5))  # Oscillating prices
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Verify ordering invariant for all values
        for value in values:
            middle = float(value.value)
            upper = value.metadata['upper_band']
            lower = value.metadata['lower_band']
            
            assert lower < middle, f"Lower band ({lower}) should be < middle band ({middle})"
            assert middle < upper, f"Middle band ({middle}) should be < upper band ({upper})"
            assert lower < upper, f"Lower band ({lower}) should be < upper band ({upper})"
    
    def test_bollinger_bands_middle_band_equals_sma(self):
        """Test that middle band equals SMA with same period"""
        from app.services.indicators import BollingerBandsIndicator, SMAIndicator
        
        # Create 25 candles
        candles = []
        for i in range(25):
            close = Decimal(str(100 + i * 2))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute Bollinger Bands
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        bb_values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Compute SMA with same period
        sma = SMAIndicator(period=20)
        sma_values = sma.compute(candles, {'period': 20})
        
        # Middle band should equal SMA
        assert len(bb_values) == len(sma_values)
        for bb_val, sma_val in zip(bb_values, sma_values):
            assert bb_val.timestamp == sma_val.timestamp
            assert bb_val.value == sma_val.value, \
                f"Middle band ({bb_val.value}) should equal SMA ({sma_val.value})"
    
    def test_bollinger_bands_with_uptrend(self):
        """Test Bollinger Bands with uptrending prices"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 30 candles with uptrend
        candles = []
        for i in range(30):
            close = Decimal(str(100 + i * 3))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Should have 11 values
        assert len(values) == 11
        
        # All values should have proper structure
        for value in values:
            assert value.indicator_name == "BB_20_2.0"
            assert 'upper_band' in value.metadata
            assert 'lower_band' in value.metadata
            assert 'bandwidth' in value.metadata
            
            # Verify ordering
            middle = float(value.value)
            upper = value.metadata['upper_band']
            lower = value.metadata['lower_band']
            assert lower < middle < upper
    
    def test_bollinger_bands_with_high_volatility(self):
        """Test Bollinger Bands with high volatility (wide bands)"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 25 candles with high volatility
        candles = []
        for i in range(25):
            # Alternating high and low prices
            close = Decimal(str(100 + (20 if i % 2 == 0 else -20)))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # With high volatility, bands should be wide
        for value in values:
            bandwidth = value.metadata['bandwidth']
            # Bandwidth should be significant (> 10)
            assert bandwidth > 10, f"Expected wide bands with high volatility, got bandwidth {bandwidth}"
    
    def test_bollinger_bands_with_low_volatility(self):
        """Test Bollinger Bands with low volatility (narrow bands)"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 25 candles with low volatility
        candles = []
        for i in range(25):
            # Prices vary slightly around 100
            close = Decimal(str(100 + (i % 3) * 0.5))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('0.1'),
                high=close + Decimal('0.2'),
                low=close - Decimal('0.2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # With low volatility, bands should be narrow
        for value in values:
            bandwidth = value.metadata['bandwidth']
            # Bandwidth should be small (< 5)
            assert bandwidth < 5, f"Expected narrow bands with low volatility, got bandwidth {bandwidth}"
    
    def test_bollinger_bands_different_std_dev_multipliers(self):
        """Test Bollinger Bands with different standard deviation multipliers"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 25 candles
        candles = []
        for i in range(25):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        # Compute with std_dev=1.0
        bb1 = BollingerBandsIndicator(period=20, std_dev=1.0)
        values1 = bb1.compute(candles, {'period': 20, 'std_dev': 1.0})
        
        # Compute with std_dev=2.0
        bb2 = BollingerBandsIndicator(period=20, std_dev=2.0)
        values2 = bb2.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Compute with std_dev=3.0
        bb3 = BollingerBandsIndicator(period=20, std_dev=3.0)
        values3 = bb3.compute(candles, {'period': 20, 'std_dev': 3.0})
        
        # All should have same number of values
        assert len(values1) == len(values2) == len(values3)
        
        # For each timestamp, bandwidth should increase with std_dev multiplier
        for v1, v2, v3 in zip(values1, values2, values3):
            bw1 = v1.metadata['bandwidth']
            bw2 = v2.metadata['bandwidth']
            bw3 = v3.metadata['bandwidth']
            
            assert bw1 < bw2 < bw3, \
                f"Bandwidth should increase with std_dev: {bw1} < {bw2} < {bw3}"
            
            # Bandwidth should be proportional to std_dev multiplier
            # bw2 should be approximately 2 * bw1
            assert abs(bw2 - 2 * bw1) < 0.01, \
                f"Bandwidth should be proportional to std_dev multiplier"
    
    def test_bollinger_bands_metadata_structure(self):
        """Test that Bollinger Bands metadata has correct structure"""
        from app.services.indicators import BollingerBandsIndicator
        
        candles = []
        for i in range(25):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        for value in values:
            # Check metadata exists and has required keys
            assert value.metadata is not None
            assert 'upper_band' in value.metadata
            assert 'lower_band' in value.metadata
            assert 'bandwidth' in value.metadata
            
            # Check types
            assert isinstance(value.metadata['upper_band'], float)
            assert isinstance(value.metadata['lower_band'], float)
            assert isinstance(value.metadata['bandwidth'], float)
            
            # Check bandwidth equals upper - middle
            middle = float(value.value)
            upper = value.metadata['upper_band']
            lower = value.metadata['lower_band']
            bandwidth = value.metadata['bandwidth']
            
            expected_bandwidth = upper - middle
            assert abs(bandwidth - expected_bandwidth) < 0.01, \
                f"Bandwidth should equal upper - middle: {bandwidth} vs {expected_bandwidth}"
    
    def test_bollinger_bands_exact_computation(self):
        """Test Bollinger Bands computation with known values"""
        from app.services.indicators import BollingerBandsIndicator
        
        # Create 5 candles with known values
        # Closes: [100, 102, 104, 103, 105]
        candles = [
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('99'), high=Decimal('101'), low=Decimal('98'),
                close=Decimal('100'), volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('101'), high=Decimal('103'), low=Decimal('100'),
                close=Decimal('102'), volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('103'), high=Decimal('105'), low=Decimal('102'),
                close=Decimal('104'), volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 4, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('104'), high=Decimal('105'), low=Decimal('102'),
                close=Decimal('103'), volume=1000000
            ),
            Candle(
                timestamp=datetime(2024, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('104'), high=Decimal('106'), low=Decimal('103'),
                close=Decimal('105'), volume=1000000
            ),
        ]
        
        # Compute with period=5, std_dev=2.0
        bb = BollingerBandsIndicator(period=5, std_dev=2.0)
        values = bb.compute(candles, {'period': 5, 'std_dev': 2.0})
        
        # Should have 1 value (at position 4)
        assert len(values) == 1
        
        # Calculate expected values manually
        # Mean = (100 + 102 + 104 + 103 + 105) / 5 = 514 / 5 = 102.8
        expected_middle = Decimal('102.8')
        
        # Variance = [(100-102.8)^2 + (102-102.8)^2 + (104-102.8)^2 + (103-102.8)^2 + (105-102.8)^2] / 5
        #          = [7.84 + 0.64 + 1.44 + 0.04 + 4.84] / 5
        #          = 14.8 / 5 = 2.96
        # Std Dev = sqrt(2.96) ≈ 1.72047
        # Upper = 102.8 + 2.0 * 1.72047 ≈ 106.24
        # Lower = 102.8 - 2.0 * 1.72047 ≈ 99.36
        
        value = values[0]
        assert abs(value.value - expected_middle) < Decimal('0.01'), \
            f"Middle band should be {expected_middle}, got {value.value}"
        
        # Check that bands are reasonable (within expected range)
        assert 105 < value.metadata['upper_band'] < 107
        assert 98 < value.metadata['lower_band'] < 100
    
    def test_bollinger_bands_timestamps_match_candles(self):
        """Test that Bollinger Bands timestamps match input candle timestamps"""
        from app.services.indicators import BollingerBandsIndicator
        
        candles = []
        for i in range(25):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        bb = BollingerBandsIndicator(period=20, std_dev=2.0)
        values = bb.compute(candles, {'period': 20, 'std_dev': 2.0})
        
        # Timestamps should match candles starting from position 19
        for i, value in enumerate(values):
            expected_timestamp = candles[19 + i].timestamp
            assert value.timestamp == expected_timestamp, \
                f"Timestamp mismatch at index {i}: {value.timestamp} vs {expected_timestamp}"



class TestATRIndicator:
    """Test ATR (Average True Range) indicator implementation"""
    
    def test_atr_name(self):
        """Test ATR indicator name includes period parameter"""
        from app.services.indicators import ATRIndicator
        
        atr = ATRIndicator(period=14)
        assert atr.name == "ATR_14"
        
        atr_custom = ATRIndicator(period=20)
        assert atr_custom.name == "ATR_20"
    
    def test_atr_required_periods(self):
        """Test ATR required periods equals period + 1"""
        from app.services.indicators import ATRIndicator
        
        atr = ATRIndicator(period=14)
        assert atr.required_periods({'period': 14}) == 15
        
        atr_custom = ATRIndicator(period=20)
        assert atr_custom.required_periods({'period': 20}) == 21
    
    def test_atr_parameter_validation_missing_period(self):
        """Test ATR raises error when period parameter is missing"""
        from app.services.indicators import ATRIndicator
        
        atr = ATRIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(20)
        ]
        
        with pytest.raises(ValueError, match="Missing required parameter: period"):
            atr.compute(candles, {})
    
    def test_atr_parameter_validation_period_not_positive(self):
        """Test ATR raises error when period is not positive"""
        from app.services.indicators import ATRIndicator
        
        atr = ATRIndicator()
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(20)
        ]
        
        with pytest.raises(ValueError, match="period must be positive"):
            atr.compute(candles, {'period': 0})
        
        with pytest.raises(ValueError, match="period must be positive"):
            atr.compute(candles, {'period': -5})
    
    def test_atr_insufficient_data(self):
        """Test ATR raises error with insufficient candles"""
        from app.services.indicators import ATRIndicator
        
        atr = ATRIndicator(period=14)
        
        # Only 10 candles, but need 15 (period + 1)
        candles = [
            Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            )
            for i in range(10)
        ]
        
        with pytest.raises(ValueError, match="requires at least 15 candles"):
            atr.compute(candles, {'period': 14})
    
    def test_atr_computation_basic(self):
        """Test ATR computation with simple data"""
        from app.services.indicators import ATRIndicator
        
        # Create 20 candles with constant range
        candles = []
        for i in range(20):
            close = Decimal('100.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close,
                high=close + Decimal('5'),  # Range of 5
                low=close - Decimal('5'),
                close=close,
                volume=1000000
            ))
        
        # Compute ATR with standard parameters
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Should have 20 - 14 = 6 values (starts from candle 14)
        assert len(values) == 6
        
        # With constant range and no gaps, ATR should be close to 10 (high - low)
        for value in values:
            assert value.value >= Decimal('0'), "ATR must be non-negative"
            assert abs(value.value - Decimal('10')) < Decimal('0.5'), "ATR should be close to 10"
            assert 'true_range' in value.metadata
    
    def test_atr_non_negativity_invariant(self):
        """Test that ATR is always non-negative (ATR >= 0)"""
        from app.services.indicators import ATRIndicator
        
        # Create 25 candles with varying prices
        candles = []
        for i in range(25):
            close = Decimal(str(100 + (i % 10) * 5))  # Oscillating prices
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('3'),
                low=close - Decimal('3'),
                close=close,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Verify non-negativity invariant for all values
        for value in values:
            assert value.value >= Decimal('0'), f"ATR ({value.value}) must be non-negative"
    
    def test_atr_true_range_calculation(self):
        """Test that true range is calculated correctly"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with known true ranges
        candles = [
            # Candle 0: close = 100
            Candle(
                timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal('100.00'),
                volume=1000000
            ),
            # Candle 1: Gap up, TR = max(110-90=20, |110-100|=10, |90-100|=10) = 20
            Candle(
                timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('105.00'),
                high=Decimal('110.00'),
                low=Decimal('90.00'),
                close=Decimal('108.00'),
                volume=1000000
            ),
            # Candle 2: Normal range, TR = max(112-106=6, |112-108|=4, |106-108|=2) = 6
            Candle(
                timestamp=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('108.00'),
                high=Decimal('112.00'),
                low=Decimal('106.00'),
                close=Decimal('110.00'),
                volume=1000000
            ),
        ]
        
        # Add more candles to meet minimum requirement
        for i in range(3, 20):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('110.00'),
                high=Decimal('115.00'),
                low=Decimal('105.00'),
                close=Decimal('110.00'),
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Check that true_range is in metadata
        for value in values:
            assert 'true_range' in value.metadata
            assert value.metadata['true_range'] >= 0
    
    def test_atr_with_gap_up(self):
        """Test ATR calculation with gap up scenario"""
        from app.services.indicators import ATRIndicator
        
        candles = []
        # First candle
        candles.append(Candle(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('102.00'),
            low=Decimal('98.00'),
            close=Decimal('100.00'),
            volume=1000000
        ))
        
        # Gap up: previous close = 100, current high = 115, low = 110
        # TR = max(115-110=5, |115-100|=15, |110-100|=10) = 15
        candles.append(Candle(
            timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('112.00'),
            high=Decimal('115.00'),
            low=Decimal('110.00'),
            close=Decimal('113.00'),
            volume=1000000
        ))
        
        # Add more candles with normal ranges
        for i in range(2, 20):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('113.00'),
                high=Decimal('115.00'),
                low=Decimal('111.00'),
                close=Decimal('113.00'),
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # ATR should reflect the gap up volatility
        assert len(values) > 0
        assert all(v.value >= Decimal('0') for v in values)
    
    def test_atr_with_gap_down(self):
        """Test ATR calculation with gap down scenario"""
        from app.services.indicators import ATRIndicator
        
        candles = []
        # First candle
        candles.append(Candle(
            timestamp=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('100.00'),
            high=Decimal('102.00'),
            low=Decimal('98.00'),
            close=Decimal('100.00'),
            volume=1000000
        ))
        
        # Gap down: previous close = 100, current high = 90, low = 85
        # TR = max(90-85=5, |90-100|=10, |85-100|=15) = 15
        candles.append(Candle(
            timestamp=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
            open=Decimal('88.00'),
            high=Decimal('90.00'),
            low=Decimal('85.00'),
            close=Decimal('87.00'),
            volume=1000000
        ))
        
        # Add more candles with normal ranges
        for i in range(2, 20):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=Decimal('87.00'),
                high=Decimal('89.00'),
                low=Decimal('85.00'),
                close=Decimal('87.00'),
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # ATR should reflect the gap down volatility
        assert len(values) > 0
        assert all(v.value >= Decimal('0') for v in values)
    
    def test_atr_zero_volatility(self):
        """Test ATR with zero volatility (all candles have same OHLC)"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with zero range (all OHLC equal)
        candles = []
        for i in range(20):
            price = Decimal('100.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # With zero volatility, ATR should be 0
        for value in values:
            assert value.value == Decimal('0'), "ATR should be 0 with zero volatility"
            assert value.metadata['true_range'] == 0.0
    
    def test_atr_increasing_volatility(self):
        """Test ATR increases with increasing volatility"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with increasing range
        candles = []
        for i in range(25):
            range_size = Decimal(str(5 + i * 0.5))  # Increasing range
            close = Decimal('100.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close,
                high=close + range_size,
                low=close - range_size,
                close=close,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # ATR should generally increase as volatility increases
        # (may not be strictly monotonic due to EMA smoothing)
        assert len(values) > 2
        assert values[-1].value > values[0].value, "ATR should increase with increasing volatility"
    
    def test_atr_decreasing_volatility(self):
        """Test ATR decreases with decreasing volatility"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with decreasing range
        candles = []
        for i in range(25):
            range_size = Decimal(str(15 - i * 0.3))  # Decreasing range
            if range_size < Decimal('1'):
                range_size = Decimal('1')
            close = Decimal('100.00')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close,
                high=close + range_size,
                low=close - range_size,
                close=close,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # ATR should generally decrease as volatility decreases
        assert len(values) > 2
        assert values[-1].value < values[0].value, "ATR should decrease with decreasing volatility"
    
    def test_atr_decimal_precision(self):
        """Test ATR maintains decimal precision"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with precise decimal values
        candles = []
        for i in range(20):
            close = Decimal('100.123456')
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('0.5'),
                high=close + Decimal('1.234567'),
                low=close - Decimal('1.234567'),
                close=close,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Verify all values are Decimal type
        for value in values:
            assert isinstance(value.value, Decimal), "ATR value should be Decimal type"
            assert value.value >= Decimal('0')
    
    def test_atr_with_different_periods(self):
        """Test ATR with different period parameters"""
        from app.services.indicators import ATRIndicator
        
        # Create 30 candles
        candles = []
        for i in range(30):
            close = Decimal(str(100 + (i % 10) * 2))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('3'),
                low=close - Decimal('3'),
                close=close,
                volume=1000000
            ))
        
        # Test with period=10
        atr_10 = ATRIndicator(period=10)
        values_10 = atr_10.compute(candles, {'period': 10})
        assert len(values_10) == 19  # 30 - 10 - 1 + 1 = 19
        
        # Test with period=20
        atr_20 = ATRIndicator(period=20)
        values_20 = atr_20.compute(candles, {'period': 20})
        assert len(values_20) == 9  # 30 - 20 - 1 + 1 = 9
        
        # Shorter period should be more responsive (may have higher variance)
        assert len(values_10) > len(values_20)
    
    def test_atr_timestamps_match_candles(self):
        """Test that ATR timestamps match input candle timestamps"""
        from app.services.indicators import ATRIndicator
        
        # Create candles with specific timestamps
        candles = []
        for i in range(20):
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 30, 0, tzinfo=timezone.utc),
                open=Decimal('100.00'),
                high=Decimal('105.00'),
                low=Decimal('95.00'),
                close=Decimal(str(100 + i)),
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Verify timestamps match candles (starting from candle 14)
        for i, value in enumerate(values):
            expected_timestamp = candles[14 + i].timestamp
            assert value.timestamp == expected_timestamp, \
                f"Timestamp mismatch at index {i}: {value.timestamp} != {expected_timestamp}"
    
    def test_atr_metadata_contains_true_range(self):
        """Test that ATR metadata contains true_range for each value"""
        from app.services.indicators import ATRIndicator
        
        candles = []
        for i in range(20):
            close = Decimal(str(100 + i))
            candles.append(Candle(
                timestamp=datetime(2024, 1, i + 1, 10, 0, 0, tzinfo=timezone.utc),
                open=close - Decimal('1'),
                high=close + Decimal('2'),
                low=close - Decimal('2'),
                close=close,
                volume=1000000
            ))
        
        atr = ATRIndicator(period=14)
        values = atr.compute(candles, {'period': 14})
        
        # Verify metadata structure
        for value in values:
            assert value.metadata is not None, "Metadata should not be None"
            assert 'true_range' in value.metadata, "Metadata should contain true_range"
            assert isinstance(value.metadata['true_range'], float), "true_range should be float"
            assert value.metadata['true_range'] >= 0, "true_range should be non-negative"
