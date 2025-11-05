import pandas as pd
import pint
import numpy as np
import xarray as xr

def convert_units(data: np.ndarray | pd.Series | xr.DataArray,
                  src_unit: str,
                  dst_unit: str) -> np.ndarray | pd.Series | xr.DataArray:
        
        data_out = data.copy()
        
        if isinstance(data, pd.Series): data = data.to_numpy()
        if isinstance(data, xr.DataArray): data = data.values
        
        ureg = pint.UnitRegistry()
        Q_ = ureg.Quantity

        print(f'\nConverting units from {src_unit} to {dst_unit}...\n')

        values_src = Q_(data, src_unit)

        values_dst = values_src.to(dst_unit)  
            
        data_out[:] = values_dst

        return data_out