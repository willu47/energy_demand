"""Clean original temperature data
"""
import os
import csv
import numpy as np

from energy_demand.basic import date_prop
from energy_demand.basic import basic_functions

def nan_helper(y):
    """Helper to handle indices and logical indices of NaNs.

    Input:
        - y, 1d numpy array with possible NaNs
    Output:
        - nans, logical indices of NaNs
        - index, a function, with signature indices= index(logical_indices),
          to convert logical indices of NaNs to 'equivalent' indices
    Example:
        >>> # linear interpolation of NaNs
        >>> nans, x= nan_helper(y)
        >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])

    Taken from: https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array
    """
    return np.isnan(y), lambda z: z.nonzero()[0]

def run(path_files, path_out_files, crit_missing_values=100):
    """Iterate weather data from MIDAS and
    generate annual hourly temperatre data files
    for every weather station by interpolating missing values
    http://data.ceda.ac.uk/badc/ukmo-midas/data/WH/yearly_files/

    The data are obtained from the Centre for Environmental Data Analysis

    [Download link]http://data.ceda.ac.uk/badc/ukmo-midas/data/WH/yearly_files/ ()

    http://badc.nerc.ac.uk/artefacts/badc_datadocs/ukmo-midas/WH_Table.html (metadata)

    Weather Stations information: http://badc.nerc.ac.uk/search/midas_stations/
    http://badc.nerc.ac.uk/cgi-bin/midas_stations/search_by_name.cgi.py?name=&minyear=&maxyear=

    The values are then written to a created folder as follows:

        year__stationname.txt

    Arguments
    ---------
    path_files : str
        Path to folder with original weather data files
    path_out_files : str
        Path to folder where the cleaned data are stored

    Note
    -----
        - In case of a leap year the 29 of February is ignored
    """
    print("... starting to clean original weather files")
    # Number of missing values until weather station quality
    # is considered as not good enough and ignored
    #crit_missing_values = 100

    # Stations which are outisde of the uk and are ignored
    stations_outside_UK = [
        1605, # St. Helena
        1585, # Gibraltar
        1609] # Falkland Islands

    # Create out folder to store station specific csv
    if os.path.isdir(path_out_files):
        basic_functions.delete_folder(path_out_files)
        os.mkdir(path_out_files)
    else:
        os.mkdir(path_out_files)

    # Placeholder value for missing entry
    placeholder_value = np.nan

    # Read all files
    all_annual_raw_files = os.listdir(path_files)

    # Sort according to year
    all_annual_raw_files.sort()

    # Annual temperature file
    for file_name in all_annual_raw_files:
        print(" ")
        print("... reading csv file: " + str(file_name), flush=True)
        print(" ")
        path_to_csv = os.path.join(path_files, file_name)

        temp_stations = {}

        with open(path_to_csv, 'r') as csvfile:
            read_lines = csv.reader(csvfile, delimiter=',')

            for row in read_lines:

                date_measurement = row[0].split(" ")
                year = int(date_measurement[0].split("-")[0])
                month = int(date_measurement[0].split("-")[1])
                day = int(date_measurement[0].split("-")[2])
                hour = int(date_measurement[1][:2])

                yearday = date_prop.date_to_yearday(year, month, day)

                if date_prop.is_leap_year(year):
                    yearday = yearday - 1 # Substract because 29. of Feb is later ignored
                else:
                    pass

                year_hour = (yearday * 24) + hour

                # Weather station id
                station_id = int(row[5])

                # If station is outside uk or leap year day
                if (station_id in stations_outside_UK) or (month == 2 and day == 29):
                    pass
                else:
                    # Air temperature in Degrees Celcius
                    if row[35] == ' ' or row[35] == '': # If no data point
                        air_temp = placeholder_value
                    else:
                        air_temp = float(row[35])

                    # Add weather station if not already added to dict
                    if station_id not in temp_stations:
                        temp_stations[station_id] = np.zeros((8760), dtype="float")
                    else:
                        pass

                    temp_stations[station_id][year_hour] = air_temp

        # ---------------------
        # Interpolate missing values (np.nan)
        # ---------------------
        temp_stations_cleaned_reshaped = {}

        for station in list(temp_stations.keys()):

            nans, x = nan_helper(temp_stations[station])
            nr_of_nans = list(nans).count(True)

            if nr_of_nans > crit_missing_values:
                print("Info - ignored station for year: {}  {} nr_of_nans: {}".format(station, year, nr_of_nans), flush=True)
                pass
            else:

                # Interpolate missing np.nan values
                temp_stations[station][nans] = np.interp(
                    x(nans),
                    x(~nans),
                    temp_stations[station][~nans])

                # test if still np.nan value
                list_with_all_nan_args = list(np.argwhere(np.isnan(temp_stations[station])))

                if list_with_all_nan_args:
                    raise Exception("Still has np.nan entries")

                # Replace with day, hour array
                interpolated_values_reshaped = temp_stations[station].reshape(365, 24)
                temp_stations_cleaned_reshaped[station] = interpolated_values_reshaped

        # Write temperature data out to csv file
        for station_name, temp_values in temp_stations_cleaned_reshaped.items():

            file_name = "{}__{}.{}".format(year, station_name, "txt")

            path_out = os.path.join(path_out_files, file_name)

            np.savetxt(
                path_out,
                temp_values,
                delimiter=",")
        
        print("--Number of stations '{}' with crit_missing_values '{}'  " + str(
            len(list(temp_stations_cleaned_reshaped.keys()))),
            crit_missing_values)

    print("... finished cleaning weather data")

# -------------
#run("//linux-filestore.ouce.ox.ac.uk/mistral/nismod/data/energy_demand/H-Met_office_weather_data/_complete_meteo_data_all_yrs",
#   "//linux-filestore.ouce.ox.ac.uk/mistral/nismod/data/energy_demand/H-Met_office_weather_data/_complete_meteo_data_all_yrs_cleaned")
run("//linux-filestore.ouce.ox.ac.uk/mistral/nismod/data/energy_demand/H-Met_office_weather_data/_year_selection",
   "//linux-filestore.ouce.ox.ac.uk/mistral/nismod/data/energy_demand/H-Met_office_weather_data/_year_selection_cleaned",
   crit_missing_values=0) #1: 219, 0: 161

#run(path_files= "C:/Users/cenv0553/ED/data/_raw_data/_test_raw_weather_data",
#    path_out_files ="C:/Users/cenv0553/ED/data/_raw_data/_test_raw_weather_data_cleaned")