import argparse
import numpy as np
import os
import rioxarray
import xarray as xr

parser = argparse.ArgumentParser(prog = "generate_mask.py",
                                 description = "Generate a mask based on the input files for a MAPSS simulation")

parser.add_argument("--work_dir", 
                    help = "Where input files are located. The output will be stored in the same location.",
                    required = False,
                    default = "")

args = parser.parse_args()
work_dir = args.work_dir

final_mask_src = os.path.join(work_dir, "mask.tif")

with rioxarray.open_rasterio(final_mask_src) as ds:
    mask_arr = ds.values.squeeze()
    crs = ds.rio.crs
    nodata = ds.rio.nodata
    lats = ds.y.values.squeeze()
    lons = ds.x.values.squeeze()


if np.isnan(nodata):
    mask_arr = np.where(np.isnan(mask_arr), np.nan, 1)
else:
    mask_arr = np.where(mask_arr == nodata, np.nan, mask_arr)


num_valid_points = int(np.nansum(mask_arr))

gridpnt = mask_arr.copy()

gridpnt[np.logical_not(np.isnan(mask_arr))] = np.array(range(1, num_valid_points + 1))

gridpnt = np.where(np.isnan(gridpnt), 0, gridpnt)

gridpnt_int = np.zeros(gridpnt.shape, dtype=int)

gridpnt_int[:] = gridpnt[:]

gridpnt_dst_dir = work_dir
gridpnt_filename = "gridpnt.nc"
gridpnt_out_path = os.path.join(gridpnt_dst_dir, gridpnt_filename)

gridpnt_da = xr.DataArray(gridpnt_int,
                         dims = ["row", "col"],
                         attrs={"scaled" : "1.0"})

var_lat = xr.Variable("row", lats,
                      attrs = {"long_name" : "latitude", "units" : "degrees_north"})
var_lon = xr.Variable("col", lons,
                      attrs = {"long_name" : "longitude", "units" : "degrees_east"})

gridpnt_ds = xr.Dataset({"gridpnt" : gridpnt_da,
                         "lat" : var_lat,
                         "lon" : var_lon}, attrs={"equator_row" :99999})

gridpnt_ds.to_netcdf(gridpnt_out_path, format = "NETCDF3_CLASSIC")