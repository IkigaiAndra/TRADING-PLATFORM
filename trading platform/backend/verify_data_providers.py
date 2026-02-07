"""
Verification script for data provider implementation.

This script verifies that the data provider interface and Yahoo Finance
implementation are correctly structured and can be imported.
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

def verify_imports():
    """Verify all imports work correctly"""
    print("✓ Verifying imports...")
    
    try:
        from app.services.data_providers import (
            DataProvider,
            YahooFinanceProvider,
            Candle,
            FetchResult,
            Timeframe
        )
        print("  ✓ All imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def verify_protocol():
    """Verify DataProvider protocol structure"""
    print("\n✓ Verifying DataProvider protocol...")
    
    from app.services.data_providers import DataProvider
    
    # Check protocol has required methods
    required_methods = ['name', 'fetch_eod_data', 'fetch_intraday_data']
    
    for method in required_methods:
        if not hasattr(DataProvider, method):
            print(f"  ✗ Missing method: {method}")
            return False
    
    print("  ✓ Protocol structure correct")
    return True


def verify_yahoo_provider():
    """Verify YahooFinanceProvider implementation"""
    print("\n✓ Verifying YahooFinanceProvider...")
    
    from app.services.data_providers import YahooFinanceProvider
    
    # Create instance
    try:
        provider = YahooFinanceProvider()
        print("  ✓ Provider instantiation successful")
    except Exception as e:
        print(f"  ✗ Instantiation error: {e}")
        return False
    
    # Check name property
    if not hasattr(provider, 'name'):
        print("  ✗ Missing 'name' property")
        return False
    
    if provider.name != "YahooFinance":
        print(f"  ✗ Incorrect name: {provider.name}")
        return False
    
    print(f"  ✓ Provider name: {provider.name}")
    
    # Check methods exist
    if not hasattr(provider, 'fetch_eod_data'):
        print("  ✗ Missing 'fetch_eod_data' method")
        return False
    
    if not hasattr(provider, 'fetch_intraday_data'):
        print("  ✗ Missing 'fetch_intraday_data' method")
        return False
    
    print("  ✓ All required methods present")
    return True


def verify_data_classes():
    """Verify Candle and FetchResult data classes"""
    print("\n✓ Verifying data classes...")
    
    from datetime import datetime
    from decimal import Decimal
    from app.services.data_providers import Candle, FetchResult
    
    # Test Candle creation
    try:
        candle = Candle(
            timestamp=datetime(2024, 1, 15),
            open=Decimal('150.00'),
            high=Decimal('155.00'),
            low=Decimal('149.00'),
            close=Decimal('154.00'),
            volume=1000000
        )
        print("  ✓ Candle creation successful")
        
        # Test to_dict method
        candle_dict = candle.to_dict()
        if 'timestamp' not in candle_dict or 'open' not in candle_dict:
            print("  ✗ Candle.to_dict() missing fields")
            return False
        print("  ✓ Candle.to_dict() works correctly")
        
    except Exception as e:
        print(f"  ✗ Candle creation error: {e}")
        return False
    
    # Test FetchResult
    try:
        # Test success result
        success_result = FetchResult.success_result([candle], "TestProvider")
        if not success_result.success:
            print("  ✗ FetchResult.success_result() not marked as success")
            return False
        print("  ✓ FetchResult.success_result() works correctly")
        
        # Test failure result
        failure_result = FetchResult.failure_result("Test error", "TestProvider")
        if failure_result.success:
            print("  ✗ FetchResult.failure_result() marked as success")
            return False
        print("  ✓ FetchResult.failure_result() works correctly")
        
    except Exception as e:
        print(f"  ✗ FetchResult error: {e}")
        return False
    
    return True


def verify_timeframe_enum():
    """Verify Timeframe enum"""
    print("\n✓ Verifying Timeframe enum...")
    
    from app.services.data_providers import Timeframe
    
    # Check required timeframes
    required_timeframes = [
        'ONE_MINUTE', 'FIVE_MINUTE', 'FIFTEEN_MINUTE',
        'THIRTY_MINUTE', 'ONE_HOUR', 'FOUR_HOUR',
        'ONE_DAY', 'ONE_WEEK', 'ONE_MONTH'
    ]
    
    for tf in required_timeframes:
        if not hasattr(Timeframe, tf):
            print(f"  ✗ Missing timeframe: {tf}")
            return False
    
    print("  ✓ All timeframes present")
    
    # Check values
    if Timeframe.FIVE_MINUTE.value != '5m':
        print(f"  ✗ Incorrect FIVE_MINUTE value: {Timeframe.FIVE_MINUTE.value}")
        return False
    
    if Timeframe.ONE_DAY.value != '1D':
        print(f"  ✗ Incorrect ONE_DAY value: {Timeframe.ONE_DAY.value}")
        return False
    
    print("  ✓ Timeframe values correct")
    return True


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Data Provider Implementation Verification")
    print("=" * 60)
    
    checks = [
        ("Imports", verify_imports),
        ("DataProvider Protocol", verify_protocol),
        ("YahooFinanceProvider", verify_yahoo_provider),
        ("Data Classes", verify_data_classes),
        ("Timeframe Enum", verify_timeframe_enum),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All verification checks passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some verification checks failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
