import argparse
import glob
import os
import rioxarray
import xarray as xr
import pandas as pd


parser = argparse.ArgumentParser(prog = "calc_tmean_WorldClim_scenarios.py",
                                 description = "Compute average temperature from WorldClim 2.1")

parser.add_argument("--work_dir",
                    help = "Where input files are stored and where output files will be stored",
                    required = False,
                    default = "")

args = parser.parse_args()

src_dir_root = args.work_dir

list_files = glob.glob(os.path.join(src_dir_root, "*.tif"))

series1 = pd.Series(list_files)

tmax_path = series1[series1.str.find("tmax") > 0].iloc[0]

tmin_path = series1[series1.str.find("tmax") > 0].iloc[0]


with rioxarray.open_rasterio(tmin_path) as ds:
    tmin_arr = ds.values
    lats = ds.y.values
    lons = ds.x.values
    crs = ds.rio.crs
    nodata = ds.rio.nodata

with rioxarray.open_rasterio(tmax_path) as ds:
    tmax_arr = ds.values

tavg_arr = (tmin_arr + tmax_arr)/2

tavg_da = xr.DataArray(tavg_arr,
                    dims = ["month", "lat", "lon"],
                    coords = {
                        "month" : range(12),
                        "lat" : lats,
                        "lon" : lons
                    })

tavg_da = tavg_da.rio.write_crs(crs)
tavg_da = tavg_da.rio.write_nodata(nodata)

filename_tavg = f"tmp.tif"
tavg_path = os.path.join(src_dir_root, filename_tavg)

tavg_da.rio.set_spatial_dims("lon", "lat")
tavg_da.rio.to_raster(tavg_path, driver="GTiff", compress="LZW")