# this code downloads and joins together data from all meteorological sensors for a period of 1 month

from selenium import webdriver
from selenium.webdriver.support.ui import Select
import bs4
import pandas as pd
import ast
import requests
import io
import datetime
from dateutil.relativedelta import relativedelta
import glob

# the following chunk of code retrieves a given amount of data points from sensorcloud.tk and writes it to a dataframe

# set number of data points to be retrieved for each sensor
num_data_points = '50000'  # options: 25000, 50000, 75000, 100000, 125000, 150000, 175000, 200000, 225000, 250000 or 275000

# names of dataframe columns created by the retrieveVals function
sensors = ['Timestamp', 'Avg. wind speed', 'Battery voltage', 'Hum_basement', 'Hum_outside', 'Max. wind speed',
           'Min. wind speed', 'Pressure', 'Temp_basement', 'Temp_hut', 'Temp_outside', 'Temp_snow', 'Wind direction']

# two dicts associating name of each sensor with a link to data from the sensor

# 5 sensors are connected to the 1st weather station, include a public link to each between quotation marks
station1 = {'Temp_snow': '',
            'Temp_hut': '',
            'Pressure': '',
            'Hum_outside': '',
            'Temp_outside': ''}

# 2 more -- to the 2nd one, include a public link to each between quotation marks
station2 = {'Hum_basement': '',
            'Temp_basement': ''}

def retrieveVals(links, cols):
    df = pd.DataFrame(columns=cols)  # create an empty dataframe with predefined names of columns
    driver = webdriver.Chrome()  # define which browser will be used by selenium
    for key, value in links.items():
        driver.get(links[key])  # send a GET request to a public web interface of each sensor
        Select(driver.find_element_by_name('s')).select_by_value(
            num_data_points)  # chose the desired number of data points
        driver.find_element_by_xpath("//form[1]").submit()  # submit the choice to a JS
        sensor_html = driver.page_source  # get the html code of the JS-rendered page
        sensor_soup = bs4.BeautifulSoup(sensor_html, 'html.parser')  # parse the html code
        x = sensor_soup.text.split('x_array=([\n')[1].split('\n]);var dt')[0]  # refine the html code
        x = ast.literal_eval(x)  # convert the resulting string into a list
        sensorDF = pd.DataFrame(list(x), columns=['Timestamp', key])  # create a dataframe for this particular sensor
        df['Timestamp'] = sensorDF['Timestamp']  # add data from it to the general dataframe
        df[key] = sensorDF[key]
    return df

# use the function for both weather stations
df1 = retrieveVals(station1, sensors)
df2 = retrieveVals(station2, sensors)

df3 = df1.append(df2, ignore_index=True)  # glue it all together

df3['Timestamp'] = df3['Timestamp'].div(
    1000)  # because all sensorcloud sensors' timestamps happen to end with 3 extra zeros

# the resulting sensorcloud dataframe contains double the no. of lines compared to the selected no. of data points
# because Timestamps received from 2 stations don't match

# the following code retrieves data from anemometer using a GET request

date_min = datetime.date.today() + relativedelta(
    months=-1)  # set a time span for which data from anemometer will be retrieved

# names of columns in raw data from the anemometer
cols = ['timestamp, sec', 'full date', 'date, DMy', 'temp, C', 'Pressure, mm/r/st', 'Average(last min), m/s',
        'Min (last min), m/s', 'Max(last min), m/s', 'Average(period), m/s', 'Min(period), m/s', 'Max(period), m/',
        'Last direction, gradus', 'v_solar, V', 'humidity, %']

blank_df = pd.DataFrame(columns=cols)  # create an empty dataframe and define names of its columns

# missing part of a link used to download data from anemometer goes between the quotation marks
data = requests.get('' + date_min.strftime(
    '%Y%m%d') + '&date_max=' + datetime.date.today().strftime('%Y%m%d'))

df = pd.read_csv(io.StringIO(data.text), names=cols, sep=';')

df = df.drop([0, 1])  # remove header and names of columns from the downloaded data (first two lines, that is)

populated_df = blank_df.append(df, ignore_index=True)  # add the new dataframe to the main one

# select only meaningful columns
df4 = populated_df[['timestamp, sec', 'Average(period), m/s', 'Min(period), m/s', 'Max(period), m/',
                    'Last direction, gradus', 'v_solar, V']]

df4.columns = ['Timestamp', 'Avg. wind speed', 'Min. wind speed', 'Max. wind speed',
               'Wind direction', 'Battery voltage']  # rename columns

df4 = df4.applymap(lambda x: x.replace(',', '.'))  # replace comas with dots so strings can be converted to floats
df4 = df4.apply(pd.to_numeric)  # convert strings to floats

# merge data from anemometer with that gathered from other sensors
df5 = df3.append(df4, ignore_index=True)

df5['Timestamp'] = pd.to_datetime(df5['Timestamp'], unit='s')  # convert timestamps to regular date format

df5.drop_duplicates('Timestamp', inplace=True)  # drop duplicates

df5.sort_values(by=['Timestamp'], inplace=True)

df5 = df5.set_index('Timestamp')

df5.to_csv(datetime.date.today().strftime('%Y_%m_%d_') + 'meteolog.csv')  # save log covering the last month

# the following section updates the joint log
df = pd.DataFrame(columns=sensors)  # create an empty dataframe and define names of the columns

path = r'C:\ARCHIVE\Meteo\Logs'  # specify a folder from which logs will be aggregated
filenames = glob.glob(path + '/*.csv')  # select all the files in the folder that have *.csv extension

for filename in filenames:
    tmp = pd.read_csv(filename, names=sensors)

    tmp = tmp.iloc[1:]  # remove header

    df = df.append(tmp, ignore_index=True)  # add each new dataframe to the main one

df.drop_duplicates('Timestamp', inplace=True)  # drop duplicates

df.sort_values(by = ['Timestamp'], inplace=True)

df = df.set_index('Timestamp')

df.to_csv('joint_meteolog_' + datetime.date.today().strftime('%Y_%m_%d') + '.csv')  # save the joint log
