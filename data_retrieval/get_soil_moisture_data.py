from sys import argv
from datetime import datetime, timedelta
import pickle
import numpy as np
from pandas import read_csv, concat

date_in = argv[1] # current date passed in as yyyy-mm-dd
date = datetime.strptime(date_in, '%Y-%m-%d') # convert to a datetime object

print 'Getting Mesonet soil moisture data for %s...' % (date_in)

# 'date' is Current Date, 0000 UTC
# midnight is at Current Date, 0600 UTC
date = date + timedelta(hours=6)

date_str = date.strftime('%Y%m%d%H%M') # yyyymmddHHMM
url = 'http://www.mesonet.org/data/public/mesonet/mdf/%04d/%02d/%02d/%s.mdf'
# url takes (year, month, day, date_str)

# set the data directory
data_dir = '../data/'

# load the MesoSoil data
soil_df = pickle.load(open(data_dir + 'soil_properties/meso_soil/MesoSoil_v1_3.pickle'))

# load the Mesonet sensor temperature rise data
tr_df = read_csv(url % (date.year, date.month, date.day, date_str),
              skiprows=2, sep=' ', skipinitialspace=True,
              na_values=['%d' % (i) for i in range(-1000, -980)],
              usecols=['STID', 'TR05', 'TR25', 'TR60'], index_col='STID')
tr_df.columns = [['TR', 'TR', 'TR'], [5, 25, 60]]

# combine data into a single DataFrame
df = soil_df.join(tr_df)

# compute matric potential
MP_df = -0.717 * np.exp(1.788*df['TR'])

# compute volumetric water content
vwc_df = df['theta_r'] + (df['theta_s'] - df['theta_r']) / (1 + (-df['alpha']*MP_df)**df['n'])**(1 - 1./df['n'])

# compute effective saturation
Se_df = (vwc_df - df['theta_r'])/(df['theta_s'] - df['theta_r'])

# compute hydraulic conductivity
K_df = df['Ko']*Se_df**df['L']*(1-(1-Se_df**(df['n']/(df['n']-1)))**(1-1./df['n']))**2

# combine all soil moisture variables into a single DataFrame
sm_df = concat([df['TR'], MP_df, vwc_df, Se_df, K_df], axis=1, keys=['TR', 'MP', 'vwc', 'Se', 'K'])

# save the soil moisture DataFrame
out_dir = data_dir + 'soil_moisture/midnight/'
sm_df.to_csv(out_dir + 'sm_data_%s.csv' % (date.strftime('%Y%m%d')))

print '  Done.'
