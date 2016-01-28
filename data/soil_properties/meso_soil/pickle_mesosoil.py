from pandas import read_excel

fname = 'MesoSoilv1_3.xlsx'

df = read_excel(fname, header=0, skiprows=[0,2], na_values=['-9.9'])
df.columns = [c.lower() for c in df.columns]
df = df.rename(columns={'site': 'STID'}).set_index(['STID', 'depth']).unstack()

df.to_pickle(fname.replace('xlsx', 'pickle'))
