import numpy as np
import pandas as pd
import scipy.stats as stats
from datetime import datetime, timedelta
import os

precip_data_dir = '/home/jpatton/RFC_StageIV_QPE_nc/api_data/'
precip_fname = 'daily_precip_%s.csv' # % (date_str)

# daily precip on day n:
# total precip that falls from midnight day n to midnight day n+1

sm_data_dir = '../data/soil_moisture/midnight/'
sm_fname = 'sm_data_%s.csv' # % (date_str)

# soil moisutre on day n:
# soil moisture at midnight day n

# set bounds for years
years = range(2014, 2016)

# set bounds for months (avoid freezing)
month_i = 4  # start in April
month_f = 10 # end in October

#depths = [5, 25, 60]
#depths = [5]
#depths = [25]
depths = [60]

# set ranges of days to test
#day_ranges = [3, 5, 7, 10, 14, 21, 30]
#day_ranges = range(5,35)
#day_ranges = range(20,30)
#day_ranges = range(21, 27)
#day_ranges = [24] # 5 cm
#day_ranges = [24, 25] # 25 cm
day_ranges = [22] # 60 cm

# set range of k to test
#ks = np.arange(0.25, 5.01, 0.25)
#ks = np.arange(0.7, 2.01, 0.05)
#ks = np.arange(0.95, 1.10, 0.01)
#ks = np.arange(0.98, 1.04, 0.005)
#ks = np.arange(1.02, 1.03, 0.001) # 5 cm
#ks = np.arange(1.00, 1.01, 0.001) # 25 cm
ks = np.arange(0.99, 1.00, 0.001) # 60 cm

r_df = pd.DataFrame(columns=['k', 'ndays', 'depth','corr', 'pval']).set_index(['k', 'ndays', 'depth'])

for ik,k in enumerate(ks):

    for iday,day_range in enumerate(day_ranges):

        # initialize totals DataFrame to store total API and soil moisture data
        df = pd.DataFrame()

        for year in years:

            # initialize date
            month = month_i
            date = datetime(year, month, 1)
            
            while month < month_f:
                skip_date = False

                # initialize daily DataFrame to store daily API and soil moisture data
                daily_df = pd.DataFrame()

                # get a list of dates to load precip data for
                precip_dates = date - np.array([timedelta(days=d+1) for d in range(day_range)])

                # compute the API
                for i,precip_date in enumerate(precip_dates):

                    # compute the date string
                    date_str = precip_date.strftime('%Y%m%d')

                    # check if file exists
                    if not os.path.isfile(precip_data_dir + precip_fname % (date_str)):
                        skip_date = True
                        continue

                    # read in precip data, calculate daily API components, then combine with daily DataFrame
                    temp_df = pd.read_csv(precip_data_dir + precip_fname % (date_str), names=['STID', i+1]).set_index('STID')
                    temp_df = temp_df * k**(-(i+1))
                    daily_df = daily_df.join(temp_df, how='outer')

                # skip this date if precip data isn't available
                if skip_date:
                    date = date + timedelta(days=1)
                    month = date.month
                    continue

                # compute the API by summing the daily API components
                daily_df = pd.DataFrame(daily_df.sum(axis=1))
                daily_df.columns = ['api']

                # join the soil moisture data
                daily_df = daily_df.join(pd.read_csv(sm_data_dir + sm_fname % (date_str), index_col=0, header=[0,1])['vwc'], how='outer')

                # add the date
                daily_df['date'] = date
                daily_df = daily_df.reset_index().set_index(['STID', 'date'])

                # combine with the total DataFrame
                df = pd.concat([df, daily_df])

                # increment the day
                date = date + timedelta(days=1)
                month = date.month

        if len(df) == 0: continue # if there is no populated DataFrame, skip correlation stats

        for depth in depths:
            r_df.loc[k, day_range, depth] = stats.pearsonr(df.dropna(subset=[str(depth)])['api'], df[str(depth)].dropna())

        print '%.2f\t%d\t%.2f%%' % (k, day_range, 100*(ik*len(day_ranges) + iday + 1)/float(len(ks)*len(day_ranges)))

r_df.to_csv('vwc_api_correlation.csv')
