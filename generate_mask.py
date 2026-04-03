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


data_dict = {
    "elev" : 1,
    "ppt" : 12,
    "tmp" : 12,
    "vpr" : 12,
    "wnd" : 12,
    "rad" : 12,
    "soils_fao" : 10
}


def squeeze_grid(varname):

    src_file_name = f"{varname}.tif"
    src_path = os.path.join(work_dir, src_file_name)
    
    ds = rioxarray.open_rasterio(src_path)

    arr = ds.values.squeeze()

    nodata_value = ds.rio.nodata

    arr = np.where(arr == nodata_value, np.nan, arr)

    if len(arr.shape) > 2:
        total = np.sum(arr, axis = 0) * 0 + 1
        print(total.shape)
        return total

    print(arr.shape)
    return arr





grids = []

for var in data_dict.keys():
    print(f"Processing {var}")

    grids.append(squeeze_grid(var))

total = np.sum(np.stack(grids), axis = 0) * 0 + 1

# Let's take the coordinates from the elevation file
path_elev_file = os.path.join(work_dir, "elev.tif")
ds = rioxarray.open_rasterio(path_elev_file)

out_da = xr.DataArray(total,
                      dims = ["y", "x"],
                      coords = {
                          "y" : ds.y.values,
                          "x" : ds.x.values
                      })

out_da = out_da.rio.write_crs("epsg:4326")
out_da = out_da.rio.write_nodata(-9999.)

dst_path = os.path.join(work_dir, "mask.tif")

out_da.rio.to_raster(dst_path, driver = "GTiff", compress = "LZW")
