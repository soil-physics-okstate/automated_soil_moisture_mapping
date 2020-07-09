from pandas import read_excel

# input file
fname = 'MesoSoilv2_0.xlsx'

# skip the first row (describes file) and third row (describes units)
# and turn missing data (-9.9) into NaNs
df = read_excel(fname, header=0, skiprows=[0,2], na_values=['-9.9'])

# make the columns use lowercase
df.columns = [c.lower() for c in df.columns]

# rename the "site" column to the more standard "STID" that's used elsewhere
df = df.rename(columns={'site': 'STID'})

# set STID and depth as the index and unstack the depth index
# so that it is a column index
df = df.set_index(['STID', 'depth']).unstack()

# save the DataFrame in a pickle named the same as the input file
df.to_pickle(fname.replace('xlsx', 'pickle'))
