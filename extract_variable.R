library(ncdf4)
library(terra)

# ── helper function ────────────────────────────────────────────────────────────
get_var <- function(varname, mapss_file, gridpnt_file) {
  
  # Open and extract the grid-point mask
  nc_gridpnt <- nc_open(gridpnt_file)
  arr_gridpnt <- ncvar_get(nc_gridpnt, "gridpnt")
  lats        <- ncvar_get(nc_gridpnt, "lat")
  lons        <- ncvar_get(nc_gridpnt, "lon")
  nc_close(nc_gridpnt)
  
  # Convert mask: 0 → NA, everything else → 1
  arr_gridpnt <- ifelse(arr_gridpnt == 0, NA, 1)
  
  # Open and extract the target variable
  nc_data <- nc_open(mapss_file)
  arr_data <- ncvar_get(nc_data, varname)
  long_name <- ncatt_get(nc_data, varname, "long_name")$value
  units     <- ncatt_get(nc_data, varname, "units")$value
  nc_close(nc_data)
  
  # Apply the land mask
  arr_data <- ifelse(is.na(arr_gridpnt), NA, arr_data)
  
  # Build a SpatRaster with proper coordinates and metadata
  r <- rast(
    nrows  = length(lats),
    ncols  = length(lons),
    xmin   = min(lons) - (lons[2] - lons[1]) / 2,
    xmax   = max(lons) + (lons[2] - lons[1]) / 2,
    ymin   = min(lats) - (lats[2] - lats[1]) / 2,
    ymax   = max(lats) + (lats[2] - lats[1]) / 2,
    crs    = "EPSG:4326"
  )
  values(r) <- t(arr_data)
  names(r)  <- varname
  
  # Store metadata as layer description (terra's closest equivalent to xarray attrs)
  longnames(r) <- long_name
  units(r)     <- units
  
  return(r)
}

# ── main script ────────────────────────────────────────────────────────────────
period <- "2061-2080"
ssp    <- "ssp245"
model  <- "ACCESS-CM2"

rootdir <- file.path("E:/MAPSS/PREP_RUN_MAPSS", period, ssp)
srcdir  <- file.path("E:/MAPSS/resultados_2026-03-16", period, ssp, model)

src_file_name    <- paste0("out_", model,"_", ssp, "_", period, ".nc")
src_gridpnt_name <- "gridpnt.nc"

src_path         <- file.path(srcdir, src_file_name)
src_path_gridpnt <- file.path(rootdir, model, src_gridpnt_name)

da_var_corr <- get_var("roff", src_path, src_path_gridpnt)

