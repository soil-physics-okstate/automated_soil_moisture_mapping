from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list('sm', 
                                         (
                                             (1,0.95,0.7),
                                             (0.9,0.75,0.6),
                                             (0.3,0.5,1),
                                             (0,0,0.4)
                                         ), N=60)

import pickle

pickle.dump(cmap, open('cmap.pickle', 'w'))
