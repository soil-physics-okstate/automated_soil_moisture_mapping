import matplotlib
matplotlib.use('agg')

from sys import argv, exit
from datetime import datetime

date_in = argv[1]
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object
date_str = date_str = date.strftime('%Y%m%d') # filenames all end in yyyymmdd
depth = int(argv[2])

output_dir = '../output/diagnostics/semivariogram/'

import cPickle as pickle
from pandas import read_csv

input_semivar_dir = '../output/semivariogram/data/'
semivar_fname = 'semivariogram_%dcm_%s.csv' % (depth, date_str)

df = read_csv(input_semivar_dir + semivar_fname)

input_model_dir = '../output/semivariogram/model/'
model_fname = 'model_%dcm_%s.csv' % (depth, date_str)

model_names = {
    'spherV': 'Spherical',
    'gaussV': 'Gaussian',
    'exponV': 'Exponential'
}

with open(input_model_dir + model_fname) as f:
    model = f.readline().rstrip()
    if not (model in model_names):
        exit('%s is not a valid model!' % (model))
    params = [float(col) for col in f.readline().rstrip().split(',')]

import numpy as np
import vgram_funcs as v
vmodel = getattr(v, model)

h = np.linspace(1,df['h'].max())
gamma_fit = vmodel(h, *params)

rmse = np.sqrt(np.mean((df['gamma'] - vmodel(df['h'], *params))**2))
params.append(rmse)

(width, height) = (720, 720) # width, height
dpi = 150. # screens are usually 96 dpi

import matplotlib.pyplot as plt

plt.style.use('ggplot')
size = (width/dpi, height/dpi)
fig = plt.figure(1, size, dpi=dpi)
ax = fig.add_subplot(1,1,1)

ax.scatter(df['h']/1000, df['gamma'], 
           marker='s', s=25, 
           facecolor='None', edgecolor='k')
ax.plot(h/1000, gamma_fit, c='b')
ax.plot([0, 0], [0, params[0]], c='b', ls='--', lw=3)

ymax = np.round(max(max(gamma_fit), max(df['gamma'])), 3) + 2e-3
ax.set_xlim(xmin=0, xmax=500)
ax.set_ylim(ymin=0, ymax=ymax)

ax.set_xlabel('lag distance [km]', fontsize=9)
ax.set_ylabel('semivariance [(cm$^3$ cm$^{-3}$)$^2$]', fontsize=9)

ax.set_title('%s semivariogram model\nfor (%s, %d cm, %s)' % 
             (model_names[model], 'vwc', depth, date_in), fontsize=10.5)

param_text = 'nugget = %.3g \nsill = %.3g \nrange = %d m\nRMSE = %.3g'
t = ax.text(10, ymax-2e-4, param_text % tuple(params),
            ha='left', va='top', fontsize=8)
t.set_bbox({'facecolor': 'w', 'alpha': 0.66})

fig.tight_layout()
fig.savefig(output_dir + 'semivariogram_%02dcm_%s.png' % (depth, date_in), dpi=dpi)

