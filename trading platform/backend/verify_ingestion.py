"""
Verification script for IngestionService implementation.

This script manually tests the IngestionService to verify:
- Provider fallback logic
- Validation integration
- Upsert logic
- Exponential backoff
- Error handling
"""

import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock

# Add backend to path
sys.path.insert(0, '.')

from app.services.ingestion import IngestionService, IngestionResult
from app.services.data_providers import DataProvider, Candle, FetchResult, Timeframe


def create_sample_candles():
    """Create sample valid candles"""
    base_date = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
    candles = []
    
    for i in range(5):
        candles.append(Candle(
            timestamp=base_date + timedelta(days=i),
            open=Decimal('150.00') + Decimal(i),
            high=Decimal('155.00') + Decimal(i),
            low=Decimal('149.00') + Decimal(i),
            close=Decimal('154.00') + Decimal(i),
            volume=1000000 + (i * 100000)
        ))
    
    return candles


def create_mock_provider(name, success=True, candles=None):
    """Create a mock data provider"""
    provider = Mock(spec=DataProvider)
    provider.name = name
    
    if success and candles:
        provider.fetch_eod_data = Mock(
            return_value=FetchResult.success_result(candles, name)
        )
        provider.fetch_intraday_data = Mock(
            return_value=FetchResult.success_result(candles, name)
        )
    else:
        provider.fetch_eod_data = Mock(
            return_value=FetchResult.failure_result(f"{name} unavailable", name)
        )
        provider.fetch_intraday_data = Mock(
            return_value=FetchResult.failure_result(f"{name} unavailable", name)
        )
    
    return provider


def test_exponential_backoff():
    """Test exponential backoff calculation"""
    print("\n=== Testing Exponential Backoff ===")
    
    mock_db = Mock()
    provider = create_mock_provider("TestProvider", success=True, candles=[])
    
    service = IngestionService(
        providers=[provider],
        db=mock_db,
        base_delay=1.0,
        max_delay=60.0
    )
    
    # Test exponential growth
    delays = [
        (0, 1.0),   # 1 * 2^0 = 1
        (1, 2.0),   # 1 * 2^1 = 2
        (2, 4.0),   # 1 * 2^2 = 4
        (3, 8.0),   # 1 * 2^3 = 8
        (4, 16.0),  # 1 * 2^4 = 16
        (5, 32.0),  # 1 * 2^5 = 32
        (6, 60.0),  # 1 * 2^6 = 64, capped at 60
        (7, 60.0),  # Capped at 60
    ]
    
    all_passed = True
    for attempt, expected_delay in delays:
        actual_delay = service._exponential_backoff_delay(attempt)
        if actual_delay == expected_delay:
            print(f"  ✓ Attempt {attempt}: {actual_delay}s (expected {expected_delay}s)")
        else:
            print(f"  ✗ Attempt {attempt}: {actual_delay}s (expected {expected_delay}s)")
            all_passed = False
    
    return all_passed


def test_provider_fallback():
    """Test provider fallback logic"""
    print("\n=== Testing Provider Fallback ===")
    
    mock_db = Mock()
    candles = create_sample_candles()
    
    # Test 1: Primary provider succeeds
    print("\nTest 1: Primary provider succeeds")
    primary = create_mock_provider("Primary", success=True, candles=candles)
    secondary = create_mock_provider("Secondary", success=True, candles=candles)
    
    service = IngestionService(providers=[primary, secondary], db=mock_db)
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data('AAPL', datetime(2024, 1, 1), datetime(2024, 1, 31))
    )
    
    if result.success and result.provider_name == "Primary":
        print("  ✓ Primary provider was used")
        if not secondary.fetch_eod_data.called:
            print("  ✓ Secondary provider was not called")
        else:
            print("  ✗ Secondary provider should not have been called")
            return False
    else:
        print(f"  ✗ Expected Primary provider, got {result.provider_name}")
        return False
    
    # Test 2: Primary fails, secondary succeeds
    print("\nTest 2: Primary fails, secondary succeeds")
    primary_fail = create_mock_provider("PrimaryFail", success=False)
    secondary_ok = create_mock_provider("SecondaryOK", success=True, candles=candles)
    
    service = IngestionService(providers=[primary_fail, secondary_ok], db=mock_db)
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data('AAPL', datetime(2024, 1, 1), datetime(2024, 1, 31))
    )
    
    if result.success and result.provider_name == "SecondaryOK":
        print("  ✓ Secondary provider was used after primary failed")
    else:
        print(f"  ✗ Expected SecondaryOK provider, got {result.provider_name}")
        return False
    
    # Test 3: All providers fail
    print("\nTest 3: All providers fail")
    fail1 = create_mock_provider("Fail1", success=False)
    fail2 = create_mock_provider("Fail2", success=False)
    
    service = IngestionService(providers=[fail1, fail2], db=mock_db)
    
    result = service._fetch_with_fallback(
        lambda p: p.fetch_eod_data('AAPL', datetime(2024, 1, 1), datetime(2024, 1, 31))
    )
    
    if not result.success and "All providers failed" in result.error_message:
        print("  ✓ All providers failed as expected")
    else:
        print(f"  ✗ Expected failure, got success={result.success}")
        return False
    
    return True


def test_validation_integration():
    """Test validation integration"""
    print("\n=== Testing Validation Integration ===")
    
    mock_db = Mock()
    provider = create_mock_provider("TestProvider", success=True, candles=[])
    service = IngestionService(providers=[provider], db=mock_db)
    
    # Test 1: All valid candles
    print("\nTest 1: All valid candles")
    valid_candles = create_sample_candles()
    validated, errors = service._validate_candles(valid_candles, '1D')
    
    if len(validated) == 5 and errors == 0:
        print(f"  ✓ All {len(validated)} candles validated successfully")
    else:
        print(f"  ✗ Expected 5 valid candles, got {len(validated)} with {errors} errors")
        return False
    
    # Test 2: Some invalid candles
    print("\nTest 2: Mix of valid and invalid candles")
    mixed_candles = valid_candles + [
        # Invalid: High < Low
        Candle(
            timestamp=datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('149.00'),  # Invalid
            low=Decimal('151.00'),
            close=Decimal('150.00'),
            volume=1000000
        ),
        # Invalid: Negative volume
        Candle(
            timestamp=datetime(2024, 1, 21, 0, 0, 0, tzinfo=timezone.utc),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=-1000  # Invalid
        )
    ]
    
    validated, errors = service._validate_candles(mixed_candles, '1D')
    
    if len(validated) == 5 and errors == 2:
        print(f"  ✓ Correctly filtered: {len(validated)} valid, {errors} invalid")
    else:
        print(f"  ✗ Expected 5 valid and 2 invalid, got {len(validated)} valid and {errors} invalid")
        return False
    
    return True


def test_ingestion_result():
    """Test IngestionResult data structure"""
    print("\n=== Testing IngestionResult ===")
    
    # Test success result
    print("\nTest 1: Success result")
    result = IngestionResult.success_result(
        candles_fetched=10,
        candles_validated=9,
        candles_stored=9,
        candles_updated=2,
        candles_inserted=7,
        validation_errors=1,
        provider_used="TestProvider"
    )
    
    if (result.success and 
        result.candles_fetched == 10 and
        result.candles_validated == 9 and
        result.candles_stored == 9 and
        result.validation_errors == 1 and
        result.provider_used == "TestProvider" and
        result.error_message is None):
        print("  ✓ Success result created correctly")
    else:
        print("  ✗ Success result has incorrect values")
        return False
    
    # Test failure result
    print("\nTest 2: Failure result")
    result = IngestionResult.failure_result("Test error")
    
    if (not result.success and
        result.error_message == "Test error" and
        result.candles_fetched == 0):
        print("  ✓ Failure result created correctly")
    else:
        print("  ✗ Failure result has incorrect values")
        return False
    
    return True


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("IngestionService Verification")
    print("=" * 60)
    
    tests = [
        ("Exponential Backoff", test_exponential_backoff),
        ("Provider Fallback", test_provider_fallback),
        ("Validation Integration", test_validation_integration),
        ("IngestionResult", test_ingestion_result),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n  ✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
