import argparse
import numpy as np
import os
import pandas as pd
import xarray as xr
import rioxarray


parser = argparse.ArgumentParser(prog = "generate_mapss_elev.py",
                                 description = "Generate elevation file for MAPSS")

parser.add_argument("--work_dir",
                    help = "Where input files are stored and where output files will be stored",
                    required = False,
                    default = "")

parser.add_argument("--paramfile",
                    help = "Parameters file",
                    required = True)

args = parser.parse_args()


numerical_types = {
    "short" : np.int16,
    "int"   : np.int32,
    "float" : np.float32
}

mapss_variable = "elev"

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

buffer = np.zeros((num_values, 1), dtype = output_type)

var_source_filename = f"{mapss_variable}.tif"
var_source_path = os.path.join(var_source_dir, var_source_filename)

# rioxarray will always open TIFF files as an xarray.DataArray
# because the TIFF format cannot contain variables as NetCDF does
with rioxarray.open_rasterio(var_source_path) as da:
    var_arr = da.values.squeeze()

buffer[:,0] = np.round(var_arr[gridpnt_arr > 0] * float(scale) * float(conversion_factor),
                                 decimals = 0)


output_da = xr.DataArray(buffer,
                         dims = ["grid", "band"],
                        attrs = {
                            "long_name" : "elevation",
                            "units" : f"{units}",
                            "scaled" : f"{scale}",
                            "source" : "WorldClim 2.1",
                            "record_length" : "1yr"
                        })

output_ds = xr.Dataset({f"{output_var_name}" : output_da})

output_dir = args.work_dir
output_filename = f"{output_var_name}.nc"
output_path = os.path.join(output_dir, output_filename)
output_ds.to_netcdf(output_path, format = "NETCDF3_CLASSIC")