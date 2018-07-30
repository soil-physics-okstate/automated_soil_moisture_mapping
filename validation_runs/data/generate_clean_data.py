import cPickle as pickle

depth = 5

site_df = pickle.load(open('../locations/all_sites.pickle'))

sitemap = {
    'LW': {'type': 'SMAP', 'f': '1602%04d_20070101.csv'},
    'FC': {'type': 'SMAP', 'f': '1603%04d_20070101.csv'},
    'JFSP': {'type': 'JFSP', 'f': 'CR200X_%d_data.csv'}
}

import pandas as pd
from datetime import datetime

dfs = []

for (site, station) in site_df.index.values:

    stype = sitemap[site]['type']   
    fname = 'raw/' + stype + '/' + sitemap[site]['f'] % (station)

    if stype == 'SMAP':

        temp_df = pd.read_csv(fname, 
                              skiprows=1, header=[0,1],
                              na_values=['-99', '-88'], 
                              skipinitialspace=True)
        
        # the headers are problematic because each
        # line of data is terminated in a comma (why!?)

        headers = temp_df.columns.tolist()[1:] # get correct headers
        for i, h in enumerate(headers): # cleanup headers
            try:
                d = int(float(h[1])*100) # try to get a valid depth
                if d < 0: raise
            except Exception: # if not valid, don't add depth to the header
                headers[i] = h[0]
            else: # otherwise do add depth to the header
                headers[i] = '%s_%d' % (h[0].rstrip(), d)

        temp_df = temp_df.drop(temp_df.columns[-1], axis=1) # drop bad column
        temp_df.columns = headers # use correct headers
        temp_df.index.name = 'ID' # now the index is named correctly

        # get timestamp
        temp_df['Timestamp'] = temp_df[['Yr', 'Mo', 'Day', 'Hr', 'Min']].apply(
            lambda cols: datetime(*cols),
            axis = 1)
        temp_df = temp_df.set_index('Timestamp')

        # only get midnight values of soil moisture at the wanted depth
        temp_df = temp_df[
            (temp_df.index.hour == 0) & 
            (temp_df.index.minute == 0) & 
            (temp_df.index < datetime.now())]['SM_%d' % (depth)]
        temp_df.name = (site, station) # name the column by the site and station
        
        dfs.append(temp_df)

    if stype == 'JFSP':

        temp_df = pd.read_csv(fname, parse_dates=True, index_col=0)
        temp_df = temp_df[
            (temp_df.index.hour == 0) &
            (temp_df.index.minute == 0) &
            (temp_df.index < datetime.now())]['vwc %d cm' % (depth)]
        temp_df.name = (site, station)
        
        dfs.append(temp_df)

# I wish concat worked here, but there's some kind of bug with the JFSP Series
df = pd.DataFrame(dfs[0])
for temp_df in dfs[1:]:
    df = df.join(temp_df, how='outer')

df.to_pickle('clean/vwc_%dcm_all_sites.pickle' % (depth))
df.to_csv('clean/vwc_%dcm_all_sites.csv' % (depth))
