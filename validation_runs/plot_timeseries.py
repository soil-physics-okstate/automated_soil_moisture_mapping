map_var = 'vwc'
depth = 5
#site = ('FC', '1')
year = 2015

from pandas import read_csv

# the arguments are the same across all read_csv functions
kwargs = {'header': [0, 1], 'index_col': 0, 'parse_dates': True}

data_df = read_csv('data/clean/%s_%dcm_all_sites.csv' % (map_var, depth), 
                   **kwargs)
ba_df = read_csv('output/merged_timeseries/%s_%dcm_barnes.csv' % (map_var, depth), 
                 **kwargs)
rk_df = read_csv('output/merged_timeseries/%s_%dcm_residual_kriged.csv' % (map_var, depth),
                 **kwargs)
ok_df = read_csv('output/merged_timeseries/%s_%dcm_ordinary_kriged.csv' % (map_var, depth),
                 **kwargs)


years = range(2010, 2016)
sites = data_df.columns.values

import matplotlib
#matplotlib.style.use('ggplot')

import matplotlib.pyplot as plt

for year in years:
    for site in sites:

        fig = plt.figure()
        
        ax = fig.add_subplot(1,1,1)

        for df in [data_df, ba_df, ok_df, rk_df]:
            df[df.index.year == year][site].plot(axes=ax)

        ax.legend(['in-situ', 'Barnes', 'OK', 'RK'])
        ax.set_title('Site %s - Station %s - %d' % (site[0], site[1], year))

        fig.savefig('plots/%s_%s_%d.png' % (site[0], site[1], year))
        plt.close(fig)
