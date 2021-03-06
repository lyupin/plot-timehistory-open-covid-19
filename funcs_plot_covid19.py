import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy import interpolate
from datetime import timedelta, date
import os

# For downloading file
import requests
from tqdm import tqdm

# Set the font
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei'] # 'Arial', 'SimHei'

# Set the options of pandas printing for debug
pd.set_option('display.max_columns', None)  # or 1000
pd.set_option('display.max_rows', None)  # or 1000
pd.set_option('display.max_colwidth', 199) 

key_date = 'Date'
key_country = 'CountryName'
key_region = 'RegionName'
key_confirmedIncrement = 'ConfirmedIncrement'
key_curedIncrement = 'curedIncrement'
key_deadIncrement = 'DeathIncrement'
key_confirmedCount = 'Confirmed'
key_deadCount = 'Deaths'

label_latestValue = 'latest'

cwd = os.getcwd()

class RegionData:
    name = ''
    nameParent = None

    infected : bool = False

    # Latest counts.
    confirmedCount : int = 0
    deadCount : int = 0
    confirmedIncrement : int = 0
    deadIncrement : int = 0
    curedCount : int = 0
    curedIncrement : int = 0
    inHospital : int = 0

    # DataFrame which stores the time history.
    dfRegion = None
    nCol : int = 0
    nRow : int = 0

    def __init__(self, name, nameParent = None):
        self.name = name
        self.nameParent = nameParent
        self.dfRegion = pd.DataFrame(columns = [key_date, key_region, \
            key_confirmedCount, key_deadCount, key_confirmedIncrement, \
            key_deadIncrement])
        self.nCol = len(self.dfRegion.columns)
        return

    # Set the accumulated counts of the confirmed cases and dead cases to the object
    def SetAccumulatives(self, sr_dates, sr_confirmedCounts = None, sr_deadCounts = None, \
        sr_curedCounts = None, debug = False):

        if sr_confirmedCounts is not None:
            sr_confirmedCounts.fillna(0, inplace = True)

        if sr_deadCounts is not None:
            sr_deadCounts.fillna(0, inplace = True)

        dateFormat = '%Y-%m-%d'
        dateMin = pd.to_datetime(sr_dates, format = dateFormat).min()
        dateMax = pd.to_datetime(sr_dates, format = dateFormat).max()
        dateRange = pd.date_range(dateMin, dateMax) # In ascending order.
        nDate = len(dateRange)
        for iDate in range(nDate):
            dateTmp = dateRange[iDate]
            dateStrTmp = '{:d}-{:02d}-{:02d}'.format(dateTmp.year, dateTmp.month, dateTmp.day)
            self.dfRegion.loc[dateStrTmp] = np.zeros((1, self.nCol), dtype = 'int')[0]
            self.dfRegion.loc[dateStrTmp, key_date] = dateStrTmp

        nDate = len(sr_dates)        
        for iDate in range(nDate):
            #print(sr_dates.iloc[iDate])
            dateTmp = sr_dates.iloc[iDate]
            if sr_confirmedCounts is not None:
                self.dfRegion.loc[dateTmp, key_confirmedCount] = int(sr_confirmedCounts.iloc[iDate])
            if sr_deadCounts is not None:
                self.dfRegion.loc[dateTmp, key_deadCount] = int(sr_deadCounts.iloc[iDate])

        if debug:
            print('In SetAccumulatives.')
            print(self.dfRegion)
        return

    # Calculate daily increments
    def CalcIncrements(self):
        colConfirmedCount = self.dfRegion.columns.get_loc(key_confirmedCount)
        colConfirmedInc = self.dfRegion.columns.get_loc(key_confirmedIncrement)
        colDeadCount = self.dfRegion.columns.get_loc(key_deadCount)
        colDeadInc = self.dfRegion.columns.get_loc(key_deadIncrement)
        self.dfRegion.iloc[0, colConfirmedInc] = self.dfRegion.iloc[0, colConfirmedCount]
        self.dfRegion.iloc[0, colDeadInc] = self.dfRegion.iloc[0, colDeadCount]
        for iDate in range(1, self.nRow):
            self.dfRegion.iloc[iDate, colConfirmedInc] = \
                self.dfRegion.iloc[iDate, colConfirmedCount] - self.dfRegion.iloc[iDate-1, colConfirmedCount] 
            self.dfRegion.iloc[iDate, colDeadInc] = \
                self.dfRegion.iloc[iDate, colDeadCount] - self.dfRegion.iloc[iDate-1, colDeadCount]
        return

    # (Not used) Set daily increments from data source.
    def SetIncrements(self, sr_dates, sr_confirmedIncrements, sr_curedIncrements, sr_deadIncrements, debug = False):
        if debug:
            print('In SetIncrements:')
            print(sr_dates)
            print(sr_confirmedIncrements)
            print(sr_curedIncrements)
            print(sr_deadIncrements)

        dateFormat = '%Y年%m月%d日'
        dateMin = pd.to_datetime(sr_dates, format = dateFormat).min()
        dateMax = pd.to_datetime(sr_dates, format = dateFormat).max()
        dateRange = pd.date_range(dateMin, dateMax)
        nDate = len(dateRange)
        for iDate in range(nDate):
            dateTmp = dateRange[iDate]
            dateStrTmp = '{:d}年{:d}月{:d}日'.format(dateTmp.year, dateTmp.month, dateTmp.day)
            self.dfRegion.loc[dateStrTmp] = np.zeros((1, self.nCol), dtype = 'int')[0]
            self.dfRegion.loc[dateStrTmp, key_date] = dateStrTmp
        nDate = len(sr_dates)
        for iDate in range(nDate):
            #print(sr_dates.iloc[iDate])
            dateTmp = sr_dates.iloc[iDate]
            self.dfRegion.loc[dateTmp, key_confirmedIncrement] = int(sr_confirmedIncrements.iloc[iDate])
            self.dfRegion.loc[dateTmp, key_curedIncrement] = int(sr_curedIncrements.iloc[iDate])
            self.dfRegion.loc[dateTmp, key_deadIncrement] = int(sr_deadIncrements.iloc[iDate])
        return

    # Complete some properties of the dataframe
    def CheckOut(self, debug = False):
        self.dfRegion[key_region] = self.name
        self.nRow = len(self.dfRegion.index)
        self.nCol = len(self.dfRegion.columns)
        self.dfRegion.index = np.arange(self.nRow)
        if debug:
            print('In CheckOut:')
            print(self.dfRegion)
        return

def download_file_old(url_in, fn_out, debug = True):
    r = requests.get(url_in, stream = True)   
    with open(fn_out,"wb") as fn_down:
        if debug:
            i_chunk = 0
        for chunk in r.iter_content(chunk_size=1024):     
            # writing one chunk at a time to the file 
            if chunk:
                if debug:
                    i_chunk += 1
                    if i_chunk%100 == 0:
                        print('Downloading ({:d} kB).'.format(i_chunk))
                fn_down.write(chunk) 
    return

def download_file(url_in, fn_out, chunk_size = 512):
    req = requests.get(url_in, stream = True)  
    total_size = int(req.headers['content-length']) 
    with open(fn_out,"wb") as fn_down:
        for chunk in tqdm(iterable = req.iter_content(chunk_size = chunk_size),\
            total = total_size / chunk_size, unit='KB'):
            fn_down.write(chunk)
    print('File downloaded: {:s}'.format(fn_out))
    return

def get_unique_record_on_each_day(df_in, strategy = 'latest', debug = False):
    '''
    Some databases provide a unique record in a region for each day. That's good.
    Some databases provide multiple records on the same day for a region,
    which is this function designed for.
    By default, this function select the latest record on each day.
    `strategy` determines how to deal with multiple records in a single day. 
    It can be 'sum' or 'latest'(default).
    '''
    dates = df_in[key_date]
    nDate = len(dates)
    nCol = len(df_in.columns)

    uniqueDates = dates.unique()
    nUniqueDate = len(uniqueDates)

    # Group dates to uniqueDates
    dateGroups = []
    dateTmp = dates.iloc[0]
    dateGroupTmp = [0]
    for iDate in range(1, nDate):
        dateTmp2 = dates.iloc[iDate]
        if dateTmp2 == dateTmp:
            dateGroupTmp.append(iDate)
        else:
            dateGroups.append(dateGroupTmp)
            dateTmp = dates.iloc[iDate]
            dateGroupTmp = [iDate]

    dateGroups.append(dateGroupTmp)

    if debug:
        print('In get_unique_record_on_each_day:')
        print(dateGroups)
        print(len(dateGroups))
        print(nUniqueDate)

    dfNewTmp = pd.DataFrame(index = np.arange(nUniqueDate), columns = df_in.columns)

    for iDateGroup in range(nUniqueDate):
        dateGroupTmp = dateGroups[iDateGroup]
        dfNewTmp.iloc[iDateGroup] = df_in.iloc[dateGroupTmp[-1]]

    if debug:
        print('df_in')
        print(df_in)
        print('df_out')
        print(dfNewTmp)

    return dfNewTmp

def extract_by_area(df_in, areaName, is_region = False, debug = False):
    '''
    Extract data of a certain area by the name of area.
    '''
    if is_region:
        df_tmp2 = df_in[df_in[key_region] == areaName].copy()
    else:
        # is country.
        df_tmp2_1 = df_in[df_in[key_country] == areaName]
        df_tmp2 = df_tmp2_1[df_tmp2_1[key_region].isnull()].copy() 

    if debug:
        print('In extracted_by_area, pos 1:')
        print(df_tmp2)

    df_tmp3 = get_unique_record_on_each_day(df_tmp2, debug = debug)
    if debug:
        print('In extracted_by_area, pos 2:')
        print(df_tmp3)

    regionData = RegionData(areaName)
    regionData.SetAccumulatives(df_tmp3[key_date], df_tmp3[key_confirmedCount], \
        df_tmp3[key_deadCount], debug = debug)
    regionData.CheckOut(debug = debug)
    regionData.CalcIncrements()
    return regionData.dfRegion

def find_start_date(df_in, startNum = 10):
    '''
    Find the first date on which the confirmed count reaches `startNum`.
    '''
    dfTmp = df_in[df_in[key_confirmedCount] >= startNum]
    datesTmp = pd.to_datetime(dfTmp[key_date]).sort_values()
    startDate = datesTmp.iloc[0]
    return startDate

def plot_region_timehistory(df_in, areaNames, dir_export = None, savefig = True, show = False, debug = False):
    '''
    Plot the time histories and save figures to disk.
    '''
    # matplotlib date format object
    dateFormat = '%Y-%m-%d'
    hfmt = mpl.dates.DateFormatter(dateFormat)    

    columnNames = [key_confirmedCount, key_confirmedIncrement, key_deadCount, key_deadIncrement]
    columnDisplayStr = ['Confirmed', 'Daily Increment of Confirmed', 'Deaths', 'Daily Increment of Deaths']
    nColumnName = len(columnNames)

    nArea = len(areaNames)

    # plot all areas in a single figure
    for iCol in range(nColumnName):
        fig, ax = plt.subplots()
        for iArea in range(nArea):
            areaName = areaNames[iArea]
            df_tmp = df_in[df_in[key_region] == areaName]
            xTmp = pd.to_datetime(df_tmp[key_date], format = dateFormat)
            yTmp = df_tmp[columnNames[iCol]]
            ax.plot(xTmp, yTmp, '.-', \
                label = areaName+'({:s} {:d})'.format(\
                label_latestValue, int(df_tmp[columnNames[iCol]].iloc[-1])))

        ax.xaxis.set_major_formatter(hfmt)
        plt.legend()
        #plt.xlabel('日期')
        plt.ylabel(columnDisplayStr[iCol])

        ylims = ax.get_ylim()
        ax.set_ylim([0, ylims[1]])

        startDate = find_start_date(df_tmp)
        xlims = ax.get_xlim()
        ax.set_xlim(startDate, xlims[1])  
        # rotates and right aligns the x labels, and moves the bottom of the
        # axes up to make room for them                  
        fig.autofmt_xdate()
        
        if savefig:
            fn_tmp = columnNames[iCol]+'.png'
            if dir_export is not None:
                fn_tmp = os.path.join(dir_export, fn_tmp)
            plt.savefig(fn_tmp, dpi = 300)
            print('Figure saved: {:s}'.format(fn_tmp))
        if show:
            plt.show()
        plt.close()

    # plot a figure for each area
    for iCol in range(nColumnName):
        for iArea in range(nArea):
            areaName = areaNames[iArea]
            df_tmp = df_in[df_in[key_region] == areaName]
            fig, ax = plt.subplots()
            xTmp = pd.to_datetime(df_tmp[key_date], format = dateFormat)
            yTmp = df_tmp[columnNames[iCol]]
            
            if debug:
                print('In plot_region_timehistory, pos 1:')
                print(xTmp)
            xDeltaTmp = xTmp - xTmp.iloc[0]
            xDeltaDays = np.array([egg.days for egg in xDeltaTmp], dtype = 'int')

            # Refined x data for spline fit.
            xDeltaTmp2 = pd.timedelta_range(start = '{:d} days'.format(xDeltaDays.min()), \
                end = '{:d} days'.format(xDeltaDays.max()), freq = '12H')
            if debug:
                print('In plot_region_timehistory, pos 2:')
                print(xDeltaTmp2)
                print(xDeltaTmp2[0])
            xDeltaDays2 = np.array([egg.days for egg in xDeltaTmp2], dtype = 'int')
            xDeltaHours2 = np.array([egg.seconds//3600 for egg in xDeltaTmp2], dtype = 'int')
            xDeltaToHours2 = xDeltaDays2 * 24 + xDeltaHours2

            xSpline = xTmp.iloc[0] + xDeltaTmp2
            tck = interpolate.splrep(xDeltaDays * 24, yTmp)
            ySpline = interpolate.splev(xDeltaToHours2, tck)

            ax.plot(xTmp, yTmp, 'k.', markersize = 2)
            ax.plot(xSpline, ySpline, \
                label = areaName+'({:s} {:d})'.format(\
                label_latestValue, df_tmp[columnNames[iCol]].iloc[-1]))
            ax.xaxis.set_major_formatter(hfmt)
            plt.legend()
            plt.ylabel(columnDisplayStr[iCol])

            ylims = ax.get_ylim()
            ax.set_ylim([0, ylims[1]])

            startDate = find_start_date(df_tmp)
            xlims = ax.get_xlim()
            ax.set_xlim(startDate, xlims[1])            
            fig.autofmt_xdate()
        
            if savefig:
                fn_tmp = columnNames[iCol]+'_'+areaName+'.png'
                if dir_export is not None:
                    fn_tmp = os.path.join(dir_export, fn_tmp)
                plt.savefig(fn_tmp, dpi = 300)
                print('Figure saved: {:s}'.format(fn_tmp))
            if show:
                plt.show()
            plt.close()

    return

def plot_covid19_timehistory(fn_csv, areaNames, dir_export = 'export', \
    is_region = False, debug = False):
    '''
    Interface for external usage.
    '''
    df_orig = pd.read_csv(fn_csv)
    #print(df_orig)
    nArea = len(areaNames)

    if (not os.path.exists(dir_export)):
        os.mkdir(dir_export)

    datasets = []
    for iArea in range(nArea):
        df_tmp1 = extract_by_area(df_orig, areaNames[iArea], is_region = is_region, debug = debug)
        datasets.append(df_tmp1)
    df_out = pd.concat(datasets)

    df_out.to_csv(os.path.join(dir_export, 'extracted_data.csv'), encoding = 'utf-8')

    plot_region_timehistory(df_out, areaNames, dir_export = dir_export, debug = debug)
    return

if __name__ == '__main__':
    fn_csv = '../open-covid-19/data/output/world.csv'
    areaNames = ['Italy', 'United States of America', 'Spain']
    plot_covid19_timehistory(fn_csv, areaNames, debug = False)

