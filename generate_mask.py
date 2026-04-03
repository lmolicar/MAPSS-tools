import numpy as np
import rioxarray
import xarray as xr

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
    
    ds = rioxarray.open_rasterio(src_file_name)

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
ds = rioxarray.open_rasterio("elev.tif")

out_da = xr.DataArray(total,
                      dims = ["y", "x"],
                      coords = {
                          "y" : ds.y.values,
                          "x" : ds.x.values
                      })

out_da = out_da.rio.write_crs("epsg:4326")
out_da = out_da.rio.write_nodata(-9999.)

out_da.rio.to_raster("mask.tif", driver = "GTiff", compress = "LZW")
