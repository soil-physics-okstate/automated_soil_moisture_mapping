from datetime import datetime
start_date = datetime(2015, 10, 23)
end_date = datetime(2015, 11, 07)
fname_suffix = 'zoom'

map_var = 'vwc'
depth = 5
site = ('JFSP', '4')
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


#years = range(2010, 2016)
#sites = data_df.columns.values

import matplotlib.pyplot as plt
plt.style.use('ggplot')
(width, height) = (1280, 720) # width, height
dpi = 150. # screens are usually 96 dpi
size = (width/dpi, height/dpi)

fig = plt.figure(1, size, dpi=dpi)

ax = fig.add_subplot(1,1,1)

for df in [data_df, ba_df, ok_df, rk_df]:
    df[(df.index > start_date) & (df.index < end_date)][site].plot(axes=ax)

ax.legend(['in-situ', 'Barnes', 'OK', 'RK'], loc=2, ncol=2)
ax.set_title('Site %s - Station %s' % (site[0], site[1]))

ax.set_ylim([0, 0.5])
ax.set_ylabel('VWC [cm$^3$ cm$^{-3}$]')

fig.tight_layout()
fig.savefig('../moisst_workshop_plots/plots/%s_%s_validation_timeseries_%s.png' % (site[0], site[1], fname_suffix), dpi=dpi)
plt.close(fig)
