"""
Simple syntax check for EMA implementation.
This script just tries to import the module to verify syntax is correct.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Checking EMA implementation syntax...")
    from app.services.indicators import EMAIndicator, Candle
    print("✅ EMA module imports successfully")
    
    # Check that EMAIndicator has required methods
    ema = EMAIndicator(period=12)
    print(f"✅ EMAIndicator instantiated: {ema.name}")
    
    # Check required methods exist
    assert hasattr(ema, 'name'), "Missing 'name' property"
    assert hasattr(ema, 'compute'), "Missing 'compute' method"
    assert hasattr(ema, 'required_periods'), "Missing 'required_periods' method"
    assert hasattr(ema, '_compute_values'), "Missing '_compute_values' method"
    assert hasattr(ema, '_validate_params'), "Missing '_validate_params' method"
    print("✅ All required methods present")
    
    # Check name format
    assert ema.name == "EMA_12", f"Expected 'EMA_12', got '{ema.name}'"
    print(f"✅ Name format correct: {ema.name}")
    
    # Check required_periods
    periods = ema.required_periods({'period': 12})
    assert periods == 12, f"Expected 12, got {periods}"
    print(f"✅ Required periods correct: {periods}")
    
    print("\n" + "=" * 50)
    print("✅ All syntax checks passed!")
    print("=" * 50)
    
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")
    sys.exit(1)
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
