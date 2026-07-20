from sys import argv
from datetime import datetime, timedelta
import pickle
import requests, numpy as np, pandas as pd
import io, os, json, tempfile

# Optional import: only used if NetCDF is detected
try:
    import xarray as xr
    _HAS_XARRAY = True
except Exception:
    xr = None
    _HAS_XARRAY = False

BASE_URL   = "https://api.mesonet.org/index.php/product/map_netcdf"
VARS_WANT  = ["vwcs10","vwcs30","vwcs60", "vwcs90"]
DEPTH_MAP  = {"vwcs10":10, "vwcs30":30, "vwcs60":60, "vwcs90":90}
OUT_CSV    = "NewOutput.csv"

def snap_00_30(dt: datetime) -> datetime:
    """Snap to :00 or :30 (ties up)."""
    if dt.minute < 15: m = 0
    elif dt.minute < 45: m = 30
    else: m = 0; dt += timedelta(hours=1)
    return dt.replace(minute=m, second=0, microsecond=0)

def looks_like_netcdf(b: bytes) -> bool:
    """Detect classic NetCDF (CDF…) or NetCDF4/HDF5 magic header."""
    return b.startswith(b"CDF") or b.startswith(b"\x89HDF\r\n\x1a\n")

def open_netcdf(content: bytes):
    """Open NetCDF bytes with xarray (h5netcdf → netcdf4→ scipy)."""
    if not _HAS_XARRAY:
        raise RuntimeError("xarray missing. Install: pip install xarray h5netcdf netCDF4 scipy")
    try:
        return xr.open_dataset(io.BytesIO(content), engine="h5netcdf")
    except Exception:
        pass
    try:
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
            tmp.write(content); path = tmp.name
        ds = xr.open_dataset(path, engine="netcdf4"); ds.load()
        try: os.remove(path)
        except OSError: pass
        return ds
    except Exception:
        return xr.open_dataset(io.BytesIO(content), engine="scipy")

def df_from_netcdf(ds) -> pd.DataFrame:
    """Extract VARS_WANT from xarray Dataset into ('VWC', depth) columns."""
    # find station dimension
    sdim = next((d for d in ds.dims if d.lower() in {"station","stid","site","location","loc"}), None)
    if sdim is None:
        non_time = [d for d in ds.dims if "time" not in d.lower()]
        if len(non_time) == 1: sdim = non_time[0]
        else: raise ValueError(f"Cannot determine station dimension. Dims: {list(ds.dims)}")
    # station IDs
    sid_var = next((k for k in ["STID","stid","station","site","SITE"] if (k in ds.variables or k in ds.coords)), None)
    if sid_var:
        stids = ds[sid_var].values
    else:
        stids = ds[sdim].values if sdim in ds.coords else np.arange(ds.sizes[sdim])
    stids = np.array([s.decode() if isinstance(s,(bytes,bytearray)) else str(s) for s in stids])

    # pull each variable, squeeze non-station dims
    cols, arrays = [], []
    for v in VARS_WANT:
        var = v if v in ds.data_vars else next((n for n in ds.data_vars if n.lower()==v.lower()), None)
        if var is None: raise KeyError(f"Var '{v}' missing. Available: {list(ds.data_vars)}")
        arr = ds[var]
        for d in list(arr.dims):
            if d != sdim: arr = arr.isel({d: 0})
        arrays.append(np.asarray(arr.values).ravel())
        cols.append(("vwc", DEPTH_MAP[v]))

    data = np.vstack(arrays).T
    df = pd.DataFrame(data, index=stids, columns=pd.MultiIndex.from_tuples(cols))
    df.index.name = "STID"
    return df

def df_from_json(j: dict) -> pd.DataFrame:
    """Extract VARS_WANT from Mesonet JSON payload into ('VWC', depth) columns."""
    if not isinstance(j, dict) or "data" not in j:
        raise ValueError("JSON missing 'data'")
    data = j["data"]
    def vec(x):  # unwrap {"data":[...]} → [...]
        return x["data"] if isinstance(x, dict) and "data" in x else x
    # station IDs if present
    stid_key = next((k for k in ["stid"] if k in data), None)
    if stid_key:
        stids = np.array([str(s).upper() for s in vec(data[stid_key])])
    else:
        n = None
        for probe in VARS_WANT + ["lat","lon"]:
            if probe in data: n = len(vec(data[probe])); break
        if n is None: raise ValueError("Cannot infer station count from JSON.")
        stids = np.array([f"S{i:03d}" for i in range(n)])

    cols, arrays = [], []
    for v in VARS_WANT:
        key = v if v in data else next((k for k in data.keys() if k.lower()==v.lower()), None)
        if key is None: raise KeyError(f"JSON var '{v}' missing. Keys: {list(data.keys())[:20]}")
        arrays.append(np.array(vec(data[key]), dtype=float))
        cols.append(("vwc", DEPTH_MAP[v]))

    mat = np.vstack(arrays).T
    if mat.shape[0] != len(stids): raise ValueError("Row mismatch JSON.")
    df = pd.DataFrame(mat, index=stids, columns=pd.MultiIndex.from_tuples(cols))
    df.index.name = "STID"
    return df

def fetch_once(dt: datetime):
    """Request one timestamp; return DataFrame or None if server replies 'false'/empty."""
    params  = {"date": dt.strftime("%Y-%m-%d %H:%M:%S"), "var": ",".join(VARS_WANT)}
    headers = {"Accept": "application/x-netcdf, application/octet-stream, application/json, */*"}
    r = requests.get(BASE_URL, params=params, headers=headers, timeout=45)
    ct, size = r.headers.get("Content-Type",""), len(r.content)
    print(f"HTTP {r.status_code} | {ct} | {size} bytes @ {params['date']}")
    if r.status_code != 200 or size < 10:  # Mesonet returns 5-byte 'false' for “no data”
        return None
    # NetCDF path
    if looks_like_netcdf(r.content) or "netcdf" in ct.lower() or "octet-stream" in ct.lower():
        ds = open_netcdf(r.content)
        return df_from_netcdf(ds)
    # JSON path
    try:
        j = r.json()
        return df_from_json(j)
    except Exception:
        return None

def parse_input(s: str) -> tuple[datetime, bool]:
    """Return (datetime, date_only_flag)."""
    for f in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, f)
            return dt, (f == "%Y-%m-%d")
        except Exception:
            pass
    raise SystemExit("Usage: python api.py YYYY-MM-DD  or  'YYYY-MM-DD HH:MM[:SS]'")

if __name__ == "__main__":
    if len(argv) < 2:
        raise SystemExit("Usage: python api.py YYYY-MM-DD  or  'YYYY-MM-DD HH:MM[:SS]'")

    dt_in, date_only = parse_input(" ".join(argv[1:]))
    if date_only:
        print("Input date (UTC 00:00):", dt_in)
        dt0 = snap_00_30(dt_in + timedelta(hours=6))   # preserve your +6h behavior
        print("Using shifted+snapped:", dt0)
    else:
        dt0 = snap_00_30(dt_in)                        # respect exact datetime, just snap
        print("Using exact datetime (snapped):", dt0)

    # Try a compact window around dt0 (±90 minutes in 30-min steps)
    candidates = [dt0] + [dt0 + timedelta(minutes=m) for m in (-30, 30, -60, 60, -90, 90)]

    df = None
    for dt in candidates:
        df = fetch_once(dt)
    if df is None:
        raise SystemExit(f"No data returned near {dt0}.")
    df.replace({np.nan: 0}, inplace=True)
    print(df.head())
    
# set the data directories
input_data_dir = '../static_data/'
output_data_dir = '../dynamic_data/'

# load the MesoSoil data
df = pickle.load(open(input_data_dir + 'soil_properties/meso_soil/MesoSoilv2_0.pickle'))

# load the Mesonet sensor temperature rise data
tr_df = read_csv(url % (date.year, date.month, date.day, date_str),
              skiprows=2, sep=' ', skipinitialspace=True,
              na_values=['%d' % (i) for i in range(-1000, -980)],
              usecols=['STID', 'TR05', 'TR25', 'TR60'], index_col='STID')
tr_df.columns = [['TR', 'TR', 'TR'], [5, 25, 60]]

# combine data into a single DataFrame
df = df.join(tr_df)

# compute matric potential
MP_df = -2083 / (1 + np.exp(-3.35 * (df['TR'] - 3.17)))

# compute volumetric water content
vwc_df = df['theta_r'] + (df['theta_s'] - df['theta_r']) / (1 + (-df['alpha']*MP_df)**df['n'])**(1 - 1./df['n'])

# compute effective saturation
Se_df = (vwc_df - df['theta_r'])/(df['theta_s'] - df['theta_r'])

# compute hydraulic conductivity -- removed for MesoSoil 2.0 compatibility
#K_df = df['ko']*Se_df**df['l']*(1-(1-Se_df**(df['n']/(df['n']-1)))**(1-1./df['n']))**2

# combine all soil moisture variables into a single DataFrame
#sm_df = concat([df['TR'], MP_df, vwc_df, Se_df, K_df], axis=1, keys=['TR', 'MP', 'vwc', 'Se', 'K'])
sm_df = concat([df['TR'], MP_df, vwc_df, Se_df], axis=1, keys=['TR', 'MP', 'vwc', 'Se'])
sm_df.columns.names = [None, None]
sm_df = sm_df.sort_index(1).loc[:, (slice(None), use_depths)]

# save the soil moisture DataFrame
out_dir = output_data_dir + 'soil_moisture/06Z/'
sm_df.to_csv(out_dir + 'sm_data_%s.csv' % (date.strftime('%Y%m%d')))
