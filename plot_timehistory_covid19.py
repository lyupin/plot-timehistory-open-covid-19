from funcs_plot_covid19 import plot_covid19_timehistory, download_file

# Data source: https://open-covid-19.github.io/data/data.csv
url_csv = 'https://open-covid-19.github.io/data/data.csv'
fn_csv = '../open-covid-19/data/output/data.csv'
download_file(url_csv, fn_csv)

# Country names.
areaNames = ['United States of America', 'Italy', 'Spain', 'China', 'Germany', 'France', \
	'Iran', 'United Kingdom']

plot_covid19_timehistory(fn_csv, areaNames, dir_export = 'country', debug = False)

# US state names.
stateNames = ['New York', 'New Jersey', 'California', 'Michigan', 'Washington', 'Louisiana',\
	'Georgia', 'Florida', 'Minnesota']
plot_covid19_timehistory(fn_csv, stateNames, dir_export = 'US', \
	is_region = True, debug = False)