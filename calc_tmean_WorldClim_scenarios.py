import argparse
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

parser.add_argument("--ssp",
                    help="Emissions scenario (SSP)",
                    required=True,
                    choices=["ssp126", "ssp245", "ssp585"])

parser.add_argument("--period",
                    help = "Period (e.g. 2021-2040)",
                    required = True,
                    choices = ["2021-2040", "2041-2060", "2061-2080", "2081-2100"])

parser.add_argument("--paramfile",
                    help = "Text file that contains the list of models to process; one line per model",
                    required = True)

args = parser.parse_args()


src_dir_root = args.work_dir
param_file_name = args.paramfile
ssp = args.ssp
period =  args.period


df = pd.read_csv(param_file_name, header = None, names = ["model"])
models = df["model"].tolist()

for curr_model in models:

    curr_dir = f"{src_dir_root}/{curr_model}"

    filename_tmin = f"wc2.1_30s_tmin_{curr_model}_{ssp}_{period}_meso.tif"
    print(filename_tmin)

    filename_tmax = f"wc2.1_30s_tmax_{curr_model}_{ssp}_{period}_meso.tif"
    print(filename_tmax)

    tmin_path = os.path.join(curr_dir, filename_tmin)
    tmax_path = os.path.join(curr_dir, filename_tmax)

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
    tavg_path = os.path.join(curr_dir, filename_tavg)

    tavg_da.rio.set_spatial_dims("lon", "lat")
    tavg_da.rio.to_raster(tavg_path, driver="GTiff", compress="LZW")