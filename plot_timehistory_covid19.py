from funcs_plot_covid19 import plot_covid19_timehistory

# Data source: https://github.com/open-covid-19/data/tree/master/output
fn_csv = '../open-covid-19/data/output/data.csv'

# Country names.
areaNames = ['Italy', 'United States of America', 'Spain']

plot_covid19_timehistory(fn_csv, areaNames, debug = False)