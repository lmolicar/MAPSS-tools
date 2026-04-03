import argparse
import numpy as np
import os
import pandas as pd
import xarray as xr
import rioxarray


parser = argparse.ArgumentParser(prog = "generate_mapss_historical.py",
                                 description = "Generate historical files for MAPSS")

parser.add_argument("--work_dir",
                    help = "Where input files are stored and where output files will be stored",
                    required = False,
                    default = "")
parser.add_argument("--variable",
                    help = "Name of the variable to process",
                    required = True,
                    choices = ["ppt", "tmp", "vpr", "wnd", "rad"])
parser.add_argument("--paramfile",
                    help = "Parameters file",
                    required = True)

args = parser.parse_args()


numerical_types = {
    "short" : np.int16,
    "int"   : np.int32
}

mapss_variable = args.variable

description_file = os.path.join(args.work_dir, args.paramfile)

descriptions = pd.read_csv(description_file)

descriptions = descriptions.set_index("attribute")

input_var_name = descriptions[mapss_variable]["input_var_name"]
output_var_name = mapss_variable
output_type = numerical_types[descriptions[mapss_variable]["type"]]
units = descriptions[mapss_variable]["units"]
scale = descriptions[mapss_variable]["scale"]
conversion_factor = descriptions[mapss_variable]["factor"]

gridpnt_src = os.path.join(args.work_dir, "gridpnt.nc")
var_source_dir = args.work_dir


with xr.open_dataset(gridpnt_src) as gridpnt_ds:
    gridpnt_arr = gridpnt_ds["gridpnt"].values.squeeze()

num_values = gridpnt_arr.max()

buffer = np.zeros((num_values, 12), dtype = output_type)

var_source_filename = f"{mapss_variable}.tif"
var_source_path = os.path.join(var_source_dir, var_source_filename)

# rioxarray will always open TIFF files as an xarray.DataArray
# because the TIFF format cannot contain variables as NetCDF does
with rioxarray.open_rasterio(var_source_path) as da:
    var_arr = da.values.squeeze()

for month in range(12):
    if month == 0:
        lats = da.y.values
        lons = da.x.values
    
    buffer[:,month] = np.round(var_arr[month, gridpnt_arr > 0] * float(scale) * float(conversion_factor),
                                 decimals = 0)


output_da = xr.DataArray(buffer,
                         dims = ["grid", "month"],
                        attrs = {
                            "long_name" : f"{output_var_name}",
                            "units" : f"{units}",
                            "scaled" : f"{scale}",
                            "source" : "WorldClim 2.1",
                            "record_length" : "1yr"
                        })

lats_scaled = np.int32(np.round(lats*100, decimals=0))
var_lat = xr.Variable("row", lats_scaled,
                      {"long_name" : "latitude",
                       "units" : "degrees_N",
                       "start" : str(lats_scaled.max()),
                       "scaled" : "100"})

lons_scaled = np.int32(np.round(lons*100, decimals=0))
var_lon = xr.Variable("col", lons_scaled,
                      {"long_name" : "longitude",
                       "units" : "degrees",
                       "start" : lons_scaled.min(),
                       "scaled" : "100"})

output_ds = xr.Dataset({f"{output_var_name}" : output_da,
                        "lat" : var_lat,
                        "lon" : var_lon})

output_dir = args.work_dir
output_filename = f"{output_var_name}.nc"
output_path = os.path.join(output_dir, output_filename)
output_ds.to_netcdf(output_path, format = "NETCDF3_CLASSIC")