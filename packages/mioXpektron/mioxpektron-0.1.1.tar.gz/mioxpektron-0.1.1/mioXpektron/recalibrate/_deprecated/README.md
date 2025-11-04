# Deprecated Calibration Files

**Date Deprecated:** October 14, 2025
**Reason:** Consolidated to reduce code duplication

## What Happened

These files have been replaced by their enhanced versions for better maintainability:

### Files Deprecated

1. **`universal_calibrator.py.old`** (486 lines, 18K)
   - **Replaced by:** `universal_calibrator.py` (formerly `enhanced_universal_calibrator2.py`)
   - **Reason:** Enhanced version is strict superset with all features + utilities

2. **`enhanced_universal_calibrator.py.old`** (1,425 lines, 47K)
   - **Replaced by:** `universal_calibrator.py` (formerly `enhanced_universal_calibrator2.py`)
   - **Reason:** v2 includes all v1 features + 5 utility functions + CLI

3. **`flexible_calibrator.py.old`** (804 lines, 27K)
   - **Replaced by:** `flexible_calibrator.py` (formerly `enhanced_flexible_calibrator.py`)
   - **Reason:** Enhanced version is strict superset with more models

## Migration

### Old Import (still works!)
```python
from mioXpektron.recalibrate import UniversalCalibrator
from mioXpektron.recalibrate import FlexibleCalibrator
```

These now import the enhanced versions automatically!

### What Changed
- **Functionality:** NONE (all features preserved)
- **API:** NONE (same class names and methods)
- **File names:** Simplified (dropped "enhanced" prefix)

### If You Need Old Versions

These files are kept for reference only. To use them:

```python
# Don't do this unless you have a specific reason
import sys
sys.path.insert(0, 'path/to/_deprecated')
from universal_calibrator import UniversalCalibrator  # Old version
```

**But you shouldn't need to!** The new versions have all the same functionality plus more.

## What You Get Now

### New `universal_calibrator.py` includes:
✅ All features from old basic version
✅ All features from enhanced v1
✅ Plus: `quick_calibrate()`, `diagnose_calibration()`, `validate_calibration()`
✅ Plus: HTML reports, CLI, batch processing

### New `flexible_calibrator.py` includes:
✅ All features from old flexible version
✅ Plus: 4 additional models (reflectron, multisegment, spline, physical)
✅ Plus: Robust outlier rejection
✅ Plus: Advanced peak detection methods

## Code Reduction

- **Before:** 5 files, 5,476 total lines
- **After:** 2 files, 2,761 total lines
- **Reduction:** 50% less code, same functionality!

## See Also

- `FILE_CONSOLIDATION_ANALYSIS.md` - Full analysis
- `MIGRATION_GUIDE_TOF_TO_QUAD_SQRT.md` - Migration guide
- `CHANGES_SUMMARY.md` - Summary of all changes
