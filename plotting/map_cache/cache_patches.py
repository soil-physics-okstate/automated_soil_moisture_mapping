import pickle

# load map params
p = pickle.load(open('map_params.pickle'))

# load grid
input_dir = '../static_data/'
df = pickle.load(open(input_dir + 'grid/soil_moisture_grid_ssurgo_stageiv.pickle'))

# put the grid in map coordinates
df['x'], df['y'] = (df['x'] + p['offset']['x'], df['y'] + p['offset']['y'])

# create the rectangle patches
from matplotlib.patches import Rectangle

xy_pairs = zip(df['x'].values - p['dx']/2., df['y'].values - p['dy']/2.)
df['patches'] = [Rectangle(xy, width=p['dx'], height=p['dy']) for xy in xy_pairs]

# save the patches
df['patches'].to_pickle('patches.pickle')
