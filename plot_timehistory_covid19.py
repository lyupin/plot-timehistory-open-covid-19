from funcs_plot_covid19 import plot_covid19_timehistory

# Data source: https://github.com/open-covid-19/data/tree/master/output
fn_csv = '../open-covid-19/data/output/data.csv'

# Country names.
areaNames = ['Italy', 'United States of America', 'Spain', 'Germany', 'France', 'Iran', 'United Kingdom']

plot_covid19_timehistory(fn_csv, areaNames, dir_export = 'country', debug = False)

# US state names.
stateNames = ['New York', 'Washington', 'California', 'Louisiana', 'New Jersey', 'Georgia', \
	'Michigan', 'Florida']
plot_covid19_timehistory(fn_csv, stateNames, dir_export = 'US', \
	is_region = True, debug = False)