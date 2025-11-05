
from token import OP
import numpy as np
import xarray as xr
import pandas as pd
from typing import Optional

def vpd_allen_2000(temp_max: np.ndarray | xr.DataArray | pd.Series,
                   temp_min: np.ndarray | xr.DataArray | pd.Series,
                   temp: np.ndarray | xr.DataArray | pd.Series,
                   rh: Optional[np.ndarray | xr.DataArray | pd.Series] = None,
                   q: Optional[np.ndarray | xr.DataArray | pd.Series] = None,
                   p: Optional[np.ndarray | xr.DataArray | pd.Series] = None,
                   tref: float = 237.15
                   ) -> np.ndarray | xr.DataArray | pd.Series:
    
    # Temperature in ° Celsius    
    # RH in percentage (0-100)
    # VPD in kPa
    # P in kPa

    if rh is None:
        if (q is None or p is None):
            raise ValueError('Either rh or q must be provided.')
        else:
            # Convert specific humidity to relative humidity
            # https://earthscience.stackexchange.com/questions/2360/how-do-i-convert-specific-humidity-to-relative-humidity
            rh = 0.263 * (q * p) * np.exp((17.67 * temp) / ((temp + tref) - 29.65))**-1

    print(rh); exit()
    assert (temp_max.shape == \
            temp_min.shape == \
            temp.shape == \
            rh.shape)
    
    print(f'\nCalculating VPD [kPa] from Temperature and RH...\n')

    # doi: 10.1175/BAMS-86-2-225
    temp_dew = temp - ((100 - rh) / 5) 

    # ISBN: 978-92-5-104219-9 
    es_tmin = 0.6108 * np.exp((17.27 * temp_min) / (temp_min + tref))
    es_tmax = 0.6108 * np.exp((17.27 * temp_max) / (temp_max + tref))

    es = (es_tmax + es_tmin) / 2

    ea = 0.6108 * np.exp((17.27 * temp_dew) / (temp_dew + tref))

    # kPa
    vpd = es - ea

    if isinstance(vpd, xr.DataArray): vpd.rename('VPD')

    return vpd