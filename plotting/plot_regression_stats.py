import matplotlib
matplotlib.use('agg')

from sys import argv
from datetime import datetime

date_in = argv[1]
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd
depth = int(argv[2])

output_dir = '../output/diagnostics/regression/'

import cPickle as pickle
from pandas import read_csv, concat

input_model_dir = '../dynamic_data/regression/model/'
model_fname = 'model_%s.pickle' % (date_str)

input_sm_dir = '../dynamic_data/soil_moisture/06Z/'
sm_fname = 'sm_data_%s.csv' % (date_str)

model = pickle.load(open(input_model_dir + model_fname))[depth]
sm = read_csv(input_sm_dir + sm_fname, header=[0,1], index_col=0)[('vwc', '%d' % (depth))]

df = concat((sm, model.fittedvalues), axis=1)
df.columns = ['vwc', 'vwc_fitted']

(w, h) = (720, 720) # width, height
dpi = 150. # screens are usually 96 dpi

import matplotlib.pyplot as plt

plt.style.use('ggplot')
size = (w/dpi, h/dpi)
fig = plt.figure(1, size, dpi=dpi)
ax = fig.add_subplot(1,1,1)
ax.set_aspect('equal', adjustable='box')

ax.scatter(df['vwc'], df['vwc_fitted'], 
           marker='^', s=25, 
           facecolor='#000044', edgecolor='None', alpha=0.66)
ax.plot([0, 0.6], [0, 0.6], c='k', ls='--', lw=1)

ax.set_xlim(0,0.5)
ax.set_ylim(0,0.5); #ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])

ax.set_xlabel('measured vwc [cm$^3$ cm$^{-3}$]', fontsize=9)
ax.set_ylabel('predicted vwc [cm$^3$ cm$^{-3}$]', fontsize=9)

ax.set_title('Regression statistics for (%s, %d cm, %s)' % ('vwc', depth, date_in),
             fontsize=10.5)

ax.text(0.01, 0.49,
        '$\widehat{vwc} = (%.3g) + (%.3g \\times \/S\/) + (%.3g \\times \/API\/)$' %
        tuple(model.params),
        ha='left', va='top', fontsize=7.5)
ax.text(0.01, 0.47,
        '$p\mathrm{-values:} \/(%.3g)\/(%.3g)\/(%.3g)$' %
        tuple(model.pvalues),
        ha='left', va='top', fontsize=7.5)
ax.text(0.01, 0.43,
        '$\mathrm{RMSE:} \/%.3g \/\mathrm{cm^3 cm^{-3}}$' %
        (model.mse_resid**0.5),
        ha='left', va='bottom', fontsize=7.5)
ax.text(0.01, 0.410,
        '$\mathrm{R^2:} \/%.3g$' %
        (model.rsquared),
        ha='left', va='bottom', fontsize=7.5)

max_vwc    = df[       df['vwc'] == df.max()['vwc']       ].reset_index()
max_fitvwc = df[df['vwc_fitted'] == df.max()['vwc_fitted']].reset_index()
min_vwc    = df[       df['vwc'] == df.min()['vwc']       ].reset_index()
min_fitvwc = df[df['vwc_fitted'] == df.min()['vwc_fitted']].reset_index()

buf = 0.01
ax.text(max_vwc['vwc'] + buf, max_vwc['vwc_fitted'], max_vwc['index'].values[0],
        ha='left', va='center', fontsize=7)
ax.text(max_fitvwc['vwc'], max_fitvwc['vwc_fitted'] + buf, max_fitvwc['index'].values[0],
        ha='center', va='bottom', fontsize=7)
ax.text(min_vwc['vwc'] - buf, min_vwc['vwc_fitted'], min_vwc['index'].values[0],
        ha='right', va='center', fontsize=7)
ax.text(min_fitvwc['vwc'], min_fitvwc['vwc_fitted'] - buf, min_fitvwc['index'].values[0],
        ha='center', va='top', fontsize=7)

fig.savefig(output_dir + 'regression_%02dcm_%s.png' % (depth, date_in), dpi=dpi)
