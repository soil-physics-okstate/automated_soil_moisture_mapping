from pandas import read_csv
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import pickle

m = pickle.load(open('oklahoma_basemap.pickle'))

## Map 

# Oklahoma bounds 
# ('o' = origin at corner of Kingfisher/Logan/Canadian/Oklahoma counties)
lats = {'n':  37.1, 's':  33.6,  'c':  35.5, 'o':  35.726}
lons = {'e': -94.4, 'w': -103.0, 'c': -97.5, 'o': -97.674}

buf = 0.05 # plot buffer size [deg]

dx = 800 # pixel resolution [m]

# projection parameters
lon_0 = lons['o']  # x=0 at counties corner
lat_0 = lats['o']  # y=0 at counties corner

# lat_0 and lon_0 don't work right in Basemap,
# so record the offset here for later use
offset = m(lon_0, lat_0)

## Read example, grid, and soil data
df = read_csv('daily_OKSMM_kriging_vwc_depth1_20151019.csv')
df['x'] = df['x'].astype('int')
df['y'] = df['y'].astype('int')

grid_df = pickle.load(open('grid.pickle'))
soil_df = pickle.load(open('sand_content.pickle'))

## Create a patch collection for each depth
depths = [5, 25, 60]
for d in depths:

    map_df = df.join(grid_df, on=['x','y'])\
               .join(soil_df[d], on='mukey')\
               .rename(columns={d: 'sand'})\
               .dropna(subset=['sand'])\
               .sort_values(by=['x', 'y'])
    
    ## Put the grid in map coordinates
    map_df['x'], map_df['y'] = (map_df.x + offset[0], map_df.y + offset[1])

    ## Create rectangle patches from the grid
    xy_pairs = zip(map_df.x.values - dx/2., map_df.y.values - dx/2.)
    map_df['patches'] = [Rectangle(xy, width=dx, height=dx) for xy in xy_pairs]

    ## Make patch collection
    p = PatchCollection(map_df.patches.values, edgecolor='None')

    ## Save patch collection
    pickle.dump(p, open('800m_patches_%dcm.pickle' % (d), 'w'))
