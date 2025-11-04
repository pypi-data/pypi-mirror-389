import numpy as np

# Total Ion Current (TIC) normalization

def tic_normalization(intensities, target_tic=1e6):
    """Scale intensities to the requested total-ion current."""

    intensities = np.asarray(intensities, dtype=float)

    if target_tic is None:
        scaled = intensities
    else:
        current_tic = np.nansum(intensities)
        if not np.isfinite(current_tic) or current_tic <= 0:
            return np.zeros_like(intensities)
        scaled = intensities * (float(target_tic) / current_tic)

    scaled = np.nan_to_num(scaled)
    scaled[scaled < 0] = 0.0
    return scaled
