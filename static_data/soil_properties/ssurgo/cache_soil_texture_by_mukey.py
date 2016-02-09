dbname = 'soilmapnik'

# set the soil layers and depths
depths = [5, 25, 60] # [cm]
layers = [(0, 10), (10, 40), (40, 80)] # [cm], which matches SSURGO

# import grid and get distinct mukeys
import pickle
df = pickle.load(open('../../grid/soil_moisture_grid_ssurgo_stageiv.pickle'))
mukeys = df['mukey'].dropna().astype(int).unique()

# connect to the database
import psycopg2
conn = psycopg2.connect('dbname=%s' % (dbname))
cur = conn.cursor()

# loop over mukeys and compute soil textures for each layer
from pandas import DataFrame, MultiIndex, concat
import numpy as np

index = MultiIndex.from_product([mukeys, depths])
df = DataFrame(columns = ['sand', 'silt', 'clay'], index=index)

for mukey in mukeys:

    # grab the cokeys and relative fractions from components table
    query = '''
    SELECT cokey, comppct_r 
    FROM component 
    WHERE (mukey = %s AND majcompflag = %s) ORDER BY comppct_r DESC;
    '''

    cur.execute(query, (str(mukey), 'Yes'))
    result = cur.fetchall()

    # check result
    if result:
        cokeys = list(zip(*result)[0])
        comppcts = list(zip(*result)[1])
    else:
        continue

    # for each layer...
    for depth_i, (top, bottom) in enumerate(layers):

        columns = ['cokey', 'hztop', 'hzbot', 'sand', 'silt', 'clay']
        layer_df = DataFrame()
        cokey_valid = []
        
        # and each component...
        for cokey_i,cokey in enumerate(cokeys):
           
            # get the horizon depths and sand, silt, and clay contents 
            # that exist anywhere within the layer
            query = '''
            SELECT cokey, hzdept_r, hzdepb_r, sandtotal_r, silttotal_r, claytotal_r 
            FROM chorizon 
            WHERE cokey = %s AND NOT (%s > hzdepb_r OR %s < hzdept_r);
            '''

            cur.execute(query, (cokey, top, bottom))
            result = cur.fetchall()
            
            # check result
            if result:
                comp_df = DataFrame(result, columns = columns)
                comp_df['cokey'] = comp_df['cokey'].astype(int)
            else: # if no data exist, skip this component
                cokey_valid.append(False)
                continue
            
            # drop horizons with missing sand, silt, or clay values
            comp_df = comp_df.dropna()
            if len(comp_df) == 0: # if no horizons are left, skip this component
                cokey_valid.append(False)
                continue

            # normalize the remaining horizon tops and bottoms to fit the layer
            comp_df.loc[comp_df['hztop'] == comp_df['hztop'].min(), 'hztop'] = top
            comp_df.loc[comp_df['hzbot'] == comp_df['hzbot'].max(), 'hzbot'] = bottom
            
            # compute the representative fraction of the layer for each horizon
            comp_df['flayer'] = (
                np.minimum(comp_df['hzbot'], bottom) - np.maximum(comp_df['hztop'], top)
            ) / float(bottom - top)
            
            # save this component's data
            layer_df = concat([layer_df, comp_df])
            cokey_valid.append(True)

        # if no components resulted in any data, skip this mapunit
        if len(layer_df) == 0:
            continue

        # compute the new weighted fraction for each component
        ckeys = np.array(cokeys)[np.array(cokey_valid)].astype(int)
        cpcts = np.array(comppcts)[np.array(cokey_valid)]
        fcomps = cpcts/float(np.sum(cpcts))
        fcomps = dict(zip(ckeys, fcomps))
        layer_df['fcomp'] = [fcomps[c] for c in layer_df['cokey'].values]
        
        # compute the sand, silt, and clay contents using the weighted averages
        sand = np.around(sum(layer_df['sand'] * layer_df['fcomp'] * layer_df['flayer']), 1)
        clay = np.around(sum(layer_df['clay'] * layer_df['fcomp'] * layer_df['flayer']), 1)
        silt = np.around(100 - (sand + clay), 1)
        
        # save data in DataFrame
        df.loc[(mukey, depths[depth_i])] = (sand, silt, clay)

# set depths as a column index and save DataFrame
df = df.unstack()
df.to_pickle('ssurgo_texture_by_mukey.pickle')
