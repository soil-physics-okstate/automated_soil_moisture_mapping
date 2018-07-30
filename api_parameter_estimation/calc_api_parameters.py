from datetime import datetime, timedelta
import numpy as np
season = slice(None)

# pick a season
season = 'winter' # comment this if no season

# set the candidate parameters
step = 0.001
k_test = [
    np.arange(0.991, 1.000, step),
    #np.arange(0.986, 1.000, step),
    np.arange(0.991, 1.005, step)
]
    
step = 1
nd_test = [
    range(165, 171, step),
    #range(44, 46, step),
    range(140, 147, step)
]

# set up the slice for the season
s = (slice(None), slice(None), season)

# read the precip and soil moisture data
import cPickle as pickle
data_df = pickle.load(open('tmp/meso_precip_sm_data.pickle'))
data_df = data_df.reset_index(level='Season')

# return all precip data in array with shape (n_sites, n_dates)
precip = data_df['daily_precip'].unstack().sort_index(axis=1, ascending=False).values
(n_sites, n_precip) = precip.shape

# store correlation data
rs = []

# loop over candidate parameters
iiter = 1
niter = np.sum([len(ks) * len(ndays) for (ks, ndays) in zip(k_test, nd_test)])

for (ks, ndays) in zip(k_test, nd_test):
    for k in ks:
        for nday in ndays:
            print '%d/%d' % (iiter, niter)

            # compute the API weights
            weights = k**np.arange(nday)

            # make a copy of the data where API will be stored
            temp_df = data_df.copy()
            temp_df['api'] = np.nan

            # compute API for each site/day, use NaN if not enough days available
            apis = []
            for i in xrange(n_precip):
                if (i + nday) < n_precip:
                    api = np.sum(precip[:, i:i+nday] * weights, axis=1)
                else:
                    api = np.array([np.nan]*n_sites)
                apis += list(api)

            # store API and sort the index
            temp_df['api'] = apis
            temp_df = temp_df[temp_df['Season'] == season]

            # compute correlations at each depth
            r5 = temp_df['api'].corr(temp_df['vwc_5'])
            r25 = temp_df['api'].corr(temp_df['vwc_25'])
            r60 = temp_df['api'].corr(temp_df['vwc_60'])

            # store correlations
            rs.append((k, nday, r5, r25, r60))

            iiter += 1

# convert list of correlations to DataFrame
from pandas import DataFrame
df = DataFrame(rs, columns=['k', 'nday', 'r_5', 'r_25', 'r_60']).set_index(['k', 'nday'])

print df.sort_values('r_5', ascending=False)['r_5'].head()
print df.sort_values('r_25', ascending=False)['r_25'].head()
print df.sort_values('r_60', ascending=False)['r_60'].head()

