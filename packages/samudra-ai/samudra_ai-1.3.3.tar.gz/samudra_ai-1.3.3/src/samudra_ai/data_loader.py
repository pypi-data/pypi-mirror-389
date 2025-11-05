# # File: src/samudra_ai/data_loader.py
# import os
# import xarray as xr
# import pandas as pd
# import numpy as np
# import cftime
# from .utils import standardize_dims

# def load_and_mask_dataset(file_path: str, var_name: str, lat_range: tuple, lon_range: tuple, time_range: tuple) -> xr.DataArray:
#     print(f"-> Memuat dan memproses file: {os.path.basename(file_path)}...")

#     # === Validasi time_range ===
#     if not (isinstance(time_range, (list, tuple)) and len(time_range) == 2):
#         raise ValueError("time_range harus tuple (start, end) dengan format YYYY-MM-DD")

#     try:
#         start_dt = pd.to_datetime(time_range[0])
#         end_dt = pd.to_datetime(time_range[1])
#     except Exception:
#         raise ValueError("Format waktu harus bisa dibaca oleh pandas, misal '1993-01-01'")

#     if start_dt >= end_dt:
#         raise ValueError("time_range: tanggal awal harus lebih kecil dari tanggal akhir")

#     # === Buka dataset dengan fallback engine ===
#     try:
#         data = xr.open_dataset(file_path, engine="h5netcdf", decode_times=True)
#     except Exception:
#         print(f"⚠️  Engine 'h5netcdf' gagal membaca {os.path.basename(file_path)}, mencoba 'netcdf4'...")
#         data = xr.open_dataset(file_path, engine="netcdf4", decode_times=True)

#     # === Validasi variabel ===
#     if var_name not in data.variables:
#         raise ValueError(f"Variabel '{var_name}' tidak ditemukan dalam {file_path}")

#     # === Deteksi nama dimensi waktu ===
#     time_candidates = ["time", "valid_time", "date", "Time", "t"]
#     detected_time = next((t for t in time_candidates if t in data.dims or t in data.coords), None)
#     if not detected_time:
#         raise ValueError("Dimensi waktu tidak ditemukan. Harus ada salah satu dari: time/valid_time/date/Time/t")

#     # Rename jadi "time" supaya konsisten
#     if detected_time != "time":
#         data = data.rename({detected_time: "time"})

#     if "time" not in data.coords:
#         raise ValueError("Koordinat 'time' tidak ditemukan.")

#     # === Penanganan cftime vs datetime64 ===
#     time_type = type(data.time.values[0])
#     if 'cftime' in str(time_type):
#         start_time, end_time = time_type(start_dt.year, start_dt.month, start_dt.day), time_type(end_dt.year, end_dt.month, end_dt.day)
#     else:
#         start_time, end_time = np.datetime64(start_dt, 'D'), np.datetime64(end_dt, 'D')

#     # === Slicing waktu ===
#     start_time_sel = data.time.sel(time=start_time, method="nearest").values
#     end_time_sel = data.time.sel(time=end_time, method="nearest").values
#     sliced_data = data[var_name].sel(time=slice(start_time_sel, end_time_sel))

#     # === Deteksi koordinat spasial ===
#     lat_names = ["lat", "latitude", "j", "y", "J", "Y"]
#     lon_names = ["lon", "longitude", "i", "x", "I", "X"]
#     detected_lat = next((lat for lat in lat_names if lat in sliced_data.dims), None)
#     detected_lon = next((lon for lon in lon_names if lon in sliced_data.dims), None)

#     if not detected_lat or not detected_lon:
#         raise ValueError("Dimensi lat/lon tidak ditemukan.")

#     # === Urutkan agar slicing aman ===
#     if sliced_data[detected_lat][0] > sliced_data[detected_lat][-1]:
#         sliced_data = sliced_data.sortby(detected_lat)
#     if sliced_data[detected_lon][0] > sliced_data[detected_lon][-1]:
#         sliced_data = sliced_data.sortby(detected_lon)

#     # === Slicing spasial ===
#     masked_data = sliced_data.sel(
#         {detected_lat: slice(*lat_range), detected_lon: slice(*lon_range)}
#     ).dropna(dim="time", how="all")

#     if masked_data.size == 0:
#         raise ValueError("Data kosong setelah slicing.")

#     # ✨ Standarisasi dimensi agar selalu lat/lon konsisten
#     return standardize_dims(masked_data)

# File: src/samudra_ai/data_loader.py yang baruuuuuuu
import os
import xarray as xr
import pandas as pd
import numpy as np
import cftime
from .utils import standardize_dims

def load_and_mask_dataset(file_path: str, var_name: str, lat_range: tuple, lon_range: tuple, time_range: tuple) -> xr.DataArray:
    """
    Memuat dataset NetCDF dan otomatis menyesuaikan nama dimensi spasial & waktu
    agar seragam [time, lat, lon]. Juga bisa menangani berbagai engine (h5netcdf/netCDF4)
    dan tipe koordinat (1D atau 2D).

    Parameters
    ----------
    file_path : str
        Path ke file NetCDF
    var_name : str
        Nama variabel utama
    lat_range, lon_range : tuple(float, float)
        Rentang spasial (misal: (-10, 10), (100, 120))
    time_range : tuple(str, str)
        Rentang waktu ("YYYY-MM-DD", "YYYY-MM-DD")
    """
    print(f"-> Memuat dan memproses file: {os.path.basename(file_path)}...")

    # === Validasi waktu ===
    if not (isinstance(time_range, (list, tuple)) and len(time_range) == 2):
        raise ValueError("time_range harus tuple (start, end) dengan format YYYY-MM-DD")

    start_dt, end_dt = map(pd.to_datetime, time_range)
    if start_dt >= end_dt:
        raise ValueError("Tanggal awal harus lebih kecil dari tanggal akhir")

    # === Buka dataset dengan fallback engine ===
    try:
        data = xr.open_dataset(file_path, engine="h5netcdf", decode_times=True)
    except Exception:
        print(f"⚠️ Engine 'h5netcdf' gagal, mencoba 'netCDF4'...")
        data = xr.open_dataset(file_path, engine="netcdf4", decode_times=True)

    # === Pastikan variabel ada ===
    if var_name not in data.variables:
        raise ValueError(f"Variabel '{var_name}' tidak ditemukan di {file_path}")

    da = data[var_name]

    # === Deteksi nama waktu ===
    time_candidates = ["time", "valid_time", "date", "Time", "t"]
    detected_time = next((t for t in time_candidates if t in data.dims or t in data.coords), None)
    if not detected_time:
        raise ValueError("Tidak menemukan koordinat waktu (time/valid_time/date/Time/t).")
    if detected_time != "time":
        data = data.rename({detected_time: "time"})
        da = data[var_name]

    # === Konversi waktu (cftime ke datetime64) ===
    if np.issubdtype(da.time.dtype, np.datetime64):
        pass
    else:
        try:
            da["time"] = xr.decode_cf(da).time
        except Exception:
            try:
                da["time"] = pd.to_datetime(da["time"].values)
            except Exception:
                print("⚠️ Waktu tidak bisa dikonversi otomatis, akan gunakan tipe original.")

    # === Seleksi waktu ===
    try:
        da = da.sel(time=slice(start_dt, end_dt))
    except Exception:
        # fallback jika cftime
        time_type = type(da.time.values[0])
        if "cftime" in str(time_type):
            da = da.sel(time=slice(
                time_type(start_dt.year, start_dt.month, start_dt.day),
                time_type(end_dt.year, end_dt.month, end_dt.day)
            ))

    if da.time.size == 0:
        raise ValueError("Tidak ada data dalam rentang waktu yang diberikan.")

    # === Deteksi nama lat/lon ===
    lat_names = ["lat", "latitude", "nav_lat", "y", "j", "LAT", "Y"]
    lon_names = ["lon", "longitude", "nav_lon", "x", "i", "LON", "X"]

    detected_lat = next((k for k in lat_names if k in da.dims or k in da.coords), None)
    detected_lon = next((k for k in lon_names if k in da.dims or k in da.coords), None)

    if not detected_lat or not detected_lon:
        raise ValueError("Koordinat lat/lon tidak ditemukan dalam dataset.")

    # === Tangani jika lat/lon berbentuk 2D (curvilinear) ===
    lat_vals = da[detected_lat]
    lon_vals = da[detected_lon]
    if lat_vals.ndim == 2 or lon_vals.ndim == 2:
        print("⚠️ Deteksi grid curvilinear (2D), slicing langsung akan di-skip.")
        sliced_data = da  # tidak bisa dislice langsung
    else:
        # Urutkan dan slice
        if lat_vals[0] > lat_vals[-1]:
            da = da.sortby(detected_lat)
        if lon_vals[0] > lon_vals[-1]:
            da = da.sortby(detected_lon)
        sliced_data = da.sel(
            {detected_lat: slice(*lat_range), detected_lon: slice(*lon_range)}
        )

    # === Hapus timestep kosong ===
    sliced_data = sliced_data.dropna(dim="time", how="all")

    if sliced_data.size == 0:
        raise ValueError("Data kosong setelah slicing spasial/waktu.")

    # === Rename dimensi agar konsisten ===
    rename_dict = {detected_lat: "lat", detected_lon: "lon"}
    if detected_lat != "lat" or detected_lon != "lon":
        sliced_data = sliced_data.rename(rename_dict)

    # === Standarisasi dimensi ===
    sliced_data = standardize_dims(sliced_data)

    print(f"✅ Dataset siap → shape={sliced_data.shape}, var={var_name}")
    return sliced_data
