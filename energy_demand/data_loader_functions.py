
#import energy_demand.main_functions as mf
import numpy as np
import os
import csv
import main_functions as mf
from datetime import date
import unittest
import json
import data_loader_functions as df


# HES-----------------------------------
def read_hes_data(data):
    '''
    Read in HES and give out for every yearday all types.

    # TODO: Don't read in HES relsted paramters but save them here (e.g. appliances)

    # NOTES: Yearly peak demand is stored in Month January = 0
    # Improve: Could read in shape of HES nicer (e.g. peak seperately)
    '''
    # initialise
    paths_hes = data['path_dict']['path_bd_e_load_profiles']
    daytype_lu = data['day_type_lu'] #0: Weekd_day, 1: Weekend, 2 : Coldest, 3 : Warmest
    app_type_lu = data['app_type_lu']
    month_nr = 12
    hours = 24
    hes_data = np.zeros((len(daytype_lu), month_nr, hours, len(app_type_lu)), dtype=float)

    hes_y_coldest = np.zeros((hours, len(app_type_lu)))
    hes_y_warmest = np.zeros((hours, len(app_type_lu)))

    # Read in raw HES data from CSV
    raw_elec_data = mf.read_csv(paths_hes)

    # Iterate raw data of hourly eletrictiy demand
    for row in raw_elec_data:
        month, daytype, appliance_typ = int(row[0]), int(row[1]), int(row[2])
        k_header = 3    # TODO: Check if in excel data starts here

        # iterate over hour  = row in csv file
        for hour in range(hours):
            # [kWH electric] Converts the summed watt into kWH TODO: Is not necessary as we are only calculating in relative terms
            _value = float(row[k_header]) * (float(1)/float(6)) * (float(1)/float(1000))

            # if coldest (see HES file)
            if daytype == 2:
                hes_y_coldest[hour][appliance_typ] = _value
                k_header += 1
                continue

            if daytype == 3:
                hes_y_warmest[hour][appliance_typ] = _value
                k_header += 1
                continue

            hes_data[daytype][month][hour][appliance_typ] = _value
            k_header += 1

    return hes_data, hes_y_coldest, hes_y_warmest

def assign_hes_data_to_year(data, hes_data, base_year):
    ''' Fill every base year day with correct data '''

    app_type_lu = data['app_type_lu']

    year_raw_values = np.zeros((365, 24, len(app_type_lu)), dtype=float)

    # Create list with all dates of a whole year
    start_date, end_date = date(base_year, 1, 1), date(base_year, 12, 31)
    list_dates = list(mf.datetime_range(start=start_date, end=end_date))

    # Assign every date to the place in the array of the year
    for yearday in list_dates:
        month_python = yearday.timetuple()[1] - 1 # - 1 because in _info: Month 1 = Jan
        yearday_python = yearday.timetuple()[7] - 1 # - 1 because in _info: 1.Jan = 1
        daytype = mf.get_weekday_type(yearday)

        _data = hes_data[daytype][month_python] # Get day from HES raw data array

        # Add values to yearly array
        year_raw_values[yearday_python] = _data   # now [yearday][hour][appliance_typ]

    return year_raw_values

def assign_carbon_trust_data_to_year(data, end_use, carbon_trust_data, base_year):
    """Fill every base year day with correct data"""

    shape_h_non_peak = np.zeros((365, 24))

    # -- Daily shape over full year (365,1)

    # Create list with all dates of a whole year
    start_date, end_date = date(base_year, 1, 1), date(base_year, 12, 31)
    list_dates = list(mf.datetime_range(start=start_date, end=end_date))

    # Assign every date to the place in the array of the year
    for yearday in list_dates:
        month_python = yearday.timetuple()[1] - 1 # - 1 because in _info: Month 1 = Jan
        yearday_python = yearday.timetuple()[7] - 1 # - 1 because in _info: 1.Jan = 1
        daytype = mf.get_weekday_type(yearday)
        _data = carbon_trust_data[daytype][month_python] # Get day from HES raw data array

        # Add values to yearly
        _data = np.array(list(_data.items()))
        shape_h_non_peak[yearday_python] = np.array(_data[:,1], dtype=float)   # now [yearday][24 hours with relative shape]


    # -- Daily shape over full year (365,1)

    # Add to hourly shape
    #data['dict_shp_enduse_h_resid'][end_use] = {'shape_h_peak': shape_h_peak, 'shape_h_non_peak': shape_h_non_peak}

    # Add to daily shape
    #data['dict_shp_enduse_d_resid'][end_use]  = {'shape_d_peak': shape_d_peak, 'shape_d_non_peak': shape_d_non_peak}

    return shape_h_non_peak

def get_hes_end_uses_shape(data, hes_data, year_raw_values, hes_y_peak, hes_y_warmest, end_use):
    ''' read out end-use shape'''
    # Calculate yearly total demand over all day years and all appliances

    # -----------------------------------
    # Peak calculation
    # -----------------------------------
    #Todo: Warmest load shape is not used

    #-- daily peak
    # Relationship of total yearly demand with averaged values and a peak day
    appliances_HES = data['app_type_lu']


    # If enduse is not in data
    #print(data['lu_appliances_HES_matched'])
    #if end_use not in data['lu_appliances_HES_matched'][:, 1]:
    #    print("Enduse not HES data: " + str(end_use))
    #    return data #, shape_h_peak, shape_h_non_peak, shape_d_peak, shape_d_non_peak

    # Get end use of HES data of current end_use of EUREC Data
    for i in data['lu_appliances_HES_matched']: #TODO: Here the HES DATA ARE MACHTED
        if i[1] == end_use:
            hes_app_id = int(i[0])
            break
            
    # Select end use daily peak demand
    peak_h_values = hes_y_peak[:, hes_app_id]
    #print("peak_h_values: " + str(peak_h_values))

    total_d_peak_demand = np.sum(peak_h_values)  # Peak is stored in JAN READ_IN HES DATA 2: PEak, 0: January, Select column

    # Total yearly demand of end_use
    total_y_end_use_demand = np.sum(year_raw_values[:, :, hes_app_id]) 

    # Factor to calculate daily peak demand from total
    shape_d_peak = (100/total_y_end_use_demand) * total_d_peak_demand

    #print("total_d_peak_demand: " + str(total_d_peak_demand))
    #print("total_y_end_use_demand: " + str(total_y_end_use_demand))
    #print("yshape_d_peak: " + str(shape_d_peak))


    # -----------------------------------
    # Get peak daily load shape
    # -----------------------------------

    #-- hourly shape [% of total daily]
    # 2: PEAK coldest daytype
    shape_h_peak = hes_y_peak[:, hes_app_id] / total_d_peak_demand

    # -------------------------
    # Calculate non-peak shapes
    # -------------------------
    shape_d_non_peak = np.zeros((365, 1))
    shape_h_non_peak = np.zeros((365, 24))
    
    for day in range(365):
        d_sum = np.sum(year_raw_values[day, :, hes_app_id])
        shape_d_non_peak[day] = (1 / total_y_end_use_demand) * d_sum

        # daily shape
        shape_h_non_peak[day] = (1 / d_sum) * year_raw_values[day, :, hes_app_id]

    print("finishddd")
    return data, shape_h_peak, shape_h_non_peak, shape_d_peak, shape_d_non_peak

# CWV WEATER GAS SAMSON-----------------------------------
def read_shp_heating_gas(data, model_type, wheater_scenario):
    """Creates the shape of the base year heating demand over the full year

    Depending wheter residential or service, a different correlation is used TODO:
    Input:
    -csv_temp_2015      SNCWV temperatures for every gas-year day
    -hourly_gas_shape   Shape of hourly gas for Day, weekday, weekend (Data from Robert Sansom)

    #TODO: THIS CAN BE USED TO DERIVED temp_2015_non_residential_gas data
    """
    # Initilaise array to store all values for a year
    hourly_hd = np.zeros((1, 24), dtype=float)
    hd_data = np.zeros((365, 24), dtype=float)

    hourly_gas_shape = mf.read_csv_float(data['path_dict']['path_hourly_gas_shape_resid']) / 100 # Because given in percentages (division no inlfuence on results as relative anyway)

    # Get hourly distribution (Sansom Data)
    #hourly_gas_shape_day = hourly_gas_shape[0]  # Hourly gas shape
    hourly_gas_shape_wkday = hourly_gas_shape[1] # Hourly gas shape
    hourly_gas_shape_wkend = hourly_gas_shape[2] # Hourly gas shape
    shape_h_peak = hourly_gas_shape[3] # Manually derived peak from Robert Sansom

    # Read in SNCWV and calculate heating demand for every yearday
    for row in data['path_temp_2015']:
        sncwv = float(row[1])
        row_split = row[0].split("/")
        date_gas_day = date(int(row_split[2]), int(row_split[1]), int(row_split[0])) # year, month, day

        yearday_python = date_gas_day.timetuple()[7] - 1 # - 1 because in _info: 1.Jan = 1
        weekday = date_gas_day.timetuple()[6] # 0: Monday

        # Calculate demand based on correlation Source: Correlation taken from CWV: Linear Correlation between SNCWV and Total NDM (RESIDENTIAL)
        if model_type == 'service':

            if wheater_scenario == 'max_cold':
                heating_demand_correlation = -13.589 * sncwv + 1022.9

            if wheater_scenario == 'min_warm':
                heating_demand_correlation = -7.2134 * sncwv + 905.46

            if wheater_scenario == 'actual':
                heating_demand_correlation = -10.159 * sncwv + 958.79

        if model_type == 'residential':

            if wheater_scenario == 'max_cold':
                heating_demand_correlation = -216.065 * sncwv + 4740.7

            if wheater_scenario == 'min_warm':
                heating_demand_correlation = -107.77 * sncwv + 2687.5

            if wheater_scenario == 'actual':
                heating_demand_correlation = -158.15 * sncwv + 3622.5
            
        # Distribute daily deamd into hourly demand
        if weekday == 5 or weekday == 6:
            hd_data[yearday_python] = hourly_gas_shape_wkend * heating_demand_correlation
        else:
            hd_data[yearday_python] = hourly_gas_shape_wkday * heating_demand_correlation

    # NON-PEAK------------------------------------------------------------------------------

    # --hourly
    shape_h_non_peak = np.zeros((365,24), dtype=float)

    for cnt, hourly_values in enumerate(hd_data):
        day_sum = np.sum(hourly_values)
        shape_h_non_peak[cnt] = (1.0 / day_sum) * hourly_values

    print("shape_h_non_peak: " + str(shape_h_non_peak))

    # --day
    shape_d_non_peak = np.zeros((365, 1)) #Two dimensional array with one row
    total_y_hd = np.sum(hd_data) # Total yearly heating demand

    # Percentage of total demand for every day
    for cnt, day in enumerate(hd_data):
        #print("---")
        #print("total_y_hd: " + str(total_y_hd))
        #print("np.sum(day): " + str(np.sum(day)))
        #print((1.0/total_y_hd) * np.sum(day))
        shape_d_non_peak[cnt] = (1.0 / total_y_hd) * np.sum(day) #calc daily demand in percent

    # PEAK-----------------------------------------------------------------------------

    # Get maximum daily demand
    _list = []
    for demand in data['path_temp_2015']:
        _list.append(float(demand[1]))
    max_day_demand = max(_list) #maximum demand

    # Factor to calc maximum daily peak #TODO: INclude uncertainty?
    shape_d_peak = max_day_demand / total_y_hd

    return shape_h_peak, shape_h_non_peak, shape_d_peak, shape_d_non_peak






# CARBON TRUST-----------------------------------
def dict_init():
    main_dict = {0: {}, 1: {}}
    for i in main_dict:
        month_dict = {}
        for ff in range(12):
            day_dict = {k: [] for k in range(24)}
            month_dict[ff] = day_dict
        main_dict[i] = month_dict

    # Initialise yearday dict
    main_dict_dayyear_absolute = {}
    for f in range(365):
        day_dict_h = {k: [] for k in range(24)}
        main_dict_dayyear_absolute[f] = day_dict_h
    main_dict, main_dict_dayyear_absolute
    return main_dict, main_dict_dayyear_absolute

def read_raw_carbon_trust_data(data, folder_path):
    """
    Folder with all csv files stored

    A. Get gas peak day load shape (the max daily demand can be taken from weather data, the daily shape however is not provided by samson)
        I. Iterate individual files which are about a year (even though gaps exist)
        II. Select those day with the maximum load
        III. Get the hourly shape of this day



    """
    # Dictionary: month, daytype, hour
    #
    # 0. Find what day it is (with date function). Then define daytype and month
    # 1. Calculate total demand of every day
    # 2. Assign percentag of total daily demand to each hour

    # out_dict_av: Every daily measurment is taken from all files and averaged
    # out_dict_not_average: Every measurment of of every file is plotted

    # Get all files in folder
    all_csv_in_folder = os.listdir(folder_path)

    # Initialise dictionaries
    main_dict, main_dict_dayyear_absolute = dict_init()
    dict_result = {0: {}, 1: {}}
    nr_of_line_entries = 0
    hourly_shape_of_maximum_days = {}

    # Itreateu folder with csv files
    for path_csv_file in all_csv_in_folder:
        path_csv_file = os.path.join(folder_path, path_csv_file)
        print("path: " + str(path_csv_file))

        # Read csv file
        with open(path_csv_file, 'r') as csv_file:            # Read CSV file
            read_lines = csv.reader(csv_file, delimiter=',')  # Read line
            _headings = next(read_lines)                      # Skip first row
            maximum_dayly_demand = 0                          # Used for searching maximum

            # Count number of lines in CSV file
            row_data = []
            for count_row, row in enumerate(read_lines):
                row_data.append(row)
            print("Number of lines in csv file: " + str(count_row))

            if count_row > 364: # if more than one year is recorded in csv file

                # Iterate day
                for row in row_data:

                    # Test if file has correct form and not more entries than 48 half-hourly entries
                    if len(row) != 49: # Skip row
                        continue

                    row[1:] = map(float, row[1:])   # Convert all values except date into float values
                    daily_sum = sum(row[1:])        # Total daily sum
                    if daily_sum == 0:              # Skip row if no demand of the day
                        continue

                    # Nr of lines added
                    nr_of_line_entries += 1

                    day, month, year  = int(row[0].split("/")[0]), int(row[0].split("/")[1]), int(row[0].split("/")[2])
                    date_row = date(year, month, day)

                    # Daytype
                    daytype = mf.get_weekday_type(date_row)

                    # Get yearday
                    yearday_python = date_row.timetuple()[7] - 1    # - 1 because in _info: 1.Jan = 1

                    # Month Python
                    month_python = month - 1

                    # Iterate hours
                    cnt, h_day, control_sum = 0, 0, 0
                    hourly_load_shape = np.zeros((24, 1))

                    for half_hour_val in row[1:]:  # Skip first date row in csv file
                        cnt += 1
                        if cnt == 2:
                            demand = first_half_hour + half_hour_val
                            control_sum += abs(demand)

                            # Calc percent of total daily demand
                            main_dict[daytype][month_python][h_day].append(demand * (1.0 / daily_sum))

                            # Load shape of this day
                            hourly_load_shape[h_day] = demand * (1.0 / daily_sum)

                            cnt = 0
                            h_day += 1

                        first_half_hour = half_hour_val # must be at this position

                    # Test if this is the day with maximum demand of this CSV file
                    if daily_sum >= maximum_dayly_demand:
                        maximum_dayly_demand = daily_sum
                        max_h_shape = hourly_load_shape

                    # Check if 100 %
                    assertions = unittest.TestCase('__init__')
                    assertions.assertAlmostEqual(control_sum, daily_sum, places=7, msg=None, delta=None)

                # Add load shape of maximum day in csv file
                hourly_shape_of_maximum_days[path_csv_file] = max_h_shape

    # -----------------------------------------------
    # Calculate average load shapes for every month
    # -----------------------------------------------

    # -- Calculate each value
    out_dict_not_av = {0: {}, 1: {}}

    # Initialise out_dict_not_av
    for daytype in out_dict_not_av:
        month_dict = {}
        for f in range(12): # hours
            day_dict = {k: [] for k in range(24)}   # Add all daily values into a list (not average)
            month_dict[f] = day_dict
        out_dict_not_av[daytype] = month_dict

    # copy values from main_dict
    for daytype in main_dict:
        for month_python in main_dict[daytype]:
            for h_day in main_dict[daytype][month_python]:
                out_dict_not_av[daytype][month_python][h_day] = main_dict[daytype][month_python][h_day]

    # -- Average (initialise dict)
    out_dict_av = {0: {}, 1: {}}
    for dtype in out_dict_av:
        month_dict = {}
        for month in range(12):
            month_dict[month] = {k: 0 for k in range(24)}
        out_dict_av[dtype] = month_dict

    # Iterate daytype
    for daytype in main_dict:

        # Iterate month
        for _month in main_dict[daytype]:

            # Iterate hour
            for _hr in main_dict[daytype][_month]:
                nr_of_entries = len(main_dict[daytype][_month][_hr]) # nr of added entries

                if nr_of_entries != 0: # Because may not contain data because not available in the csv files
                    out_dict_av[daytype][_month][_hr] = sum(main_dict[daytype][_month][_hr]) / nr_of_entries

    # Test to for summing
    for daytype in out_dict_av:
        for month in out_dict_av[daytype]:
            test_sum = sum(map(abs, out_dict_av[daytype][month].values())) # Sum absolute values
            assertions = unittest.TestCase('__init__')
            #TODO: Don't know why it doesnt owrk
            #np.testing.assert_almost_equal(test_sum, 100.0, decimal=7, err_msg='', verbose=True)
            #assertions.assertAlmostEqual(test_sum, 100.0, places=2, msg=None, delta=None)

    # Add SHAPES
    # Add to hourly non-residential shape
    #data['dict_shp_enduse_h_resid'][end_use] = {'shape_h_peak_non_resid': maxday_h_shape, 'shape_h_non_peak': } 

    # Add to daily shape
    #data['dict_shp_enduse_d_resid'][end_use]  = {'shape_d_peak_non_resid': CCWDATA, 'shape_d_non_peak_non_resid': } # No peak
    #prnt("..")

    # Write out enduse load shape #TODO
    #write_enduse_load_shape_to_csv()

    return out_dict_av, out_dict_not_av, hourly_shape_of_maximum_days

def non_residential_peak_h(hourly_shape_of_maximum_days):
    """ Returns the peak of the day """
    # -----------------------------------------
    # Calculate daily peak of maximum day
    # If all_gas --> heating_gas demand peak
    # -----------------------------------------
    maxday_h_shape = np.zeros((24,1))

    for shape_d in hourly_shape_of_maximum_days:
        maxday_h_shape += hourly_shape_of_maximum_days[shape_d]

    # Calc average
    maxday_h_shape = maxday_h_shape / len(hourly_shape_of_maximum_days)
    #print("maxday_h_shape: " + str(maxday_h_shape))
    #print(len(hourly_shape_of_maximum_days))
    #pf.plot_load_shape_d(maxday_h_shape)
    return maxday_h_shape



'''def followup_processing(out_dict_average, out_dict_not_average):

    # --------------------------------------------------------
    # Calculate average daily load shape for all mongth (averaged)
    # --------------------------------------------------------
    # Initiate
    yearly_averaged_load_curve = {0: {}, 1: {}}
    for daytype in yearly_averaged_load_curve:
        yearly_averaged_load_curve[daytype] = {k: 0 for k in range(24)}

    for daytype in out_dict_average:

        # iterate month
        for hour in range(24):
            h_average_y = 0

            # Get every hour of all months
            for month in range(12):
                h_average_y += out_dict_average[daytype][month][hour]

            h_average_y = h_average_y / 12
            yearly_averaged_load_curve[daytype][hour] = h_average_y

    print("Result yearly averaged:")
    print(yearly_averaged_load_curve)
    return
'''



def create_txt_shapes(end_use, path_txt, shape_h_peak, shape_h_non_peak, shape_d_peak, shape_d_non_peak, other_string_info):
    """ Function collecting functions to write out txt files"""
    #print(shape_h_peak.shape)       # 24
    #print(shape_h_non_peak.shape)   # 365, 24
    #print(shape_d_peak.shape)       # ()
    #print(shape_d_non_peak.shape)   # 365, 1
    jason_to_txt_shape_h_peak(shape_h_peak, os.path.join(path_txt, str(end_use) + str("__") + str('shape_h_peak') + str(other_string_info) + str('.txt')))
    jason_to_txt_shape_h_non_peak(shape_h_non_peak, os.path.join(path_txt, str(end_use) + str("__") + str('shape_h_non_peak') + str(other_string_info) + str('.txt')))
    jason_to_txt_shape_d_peak(shape_d_peak, os.path.join(path_txt, str(end_use) + str("__") + str('shape_d_peak') + str(other_string_info) + str('.txt')))
    jason_to_txt_shape_d_non_peak(shape_d_non_peak, os.path.join(path_txt, str(end_use) + str("__") + str('shape_d_non_peak') + str('.txt')))



def jason_to_txt_shape_h_peak(input_array, outfile_path):
    """Wrte to txt. Array with shape: (24,)"""
    np_dict = dict(enumerate(input_array))
    with open(outfile_path, 'w') as outfile:
        json.dump(np_dict, outfile)

def jason_to_txt_shape_h_non_peak(input_array, outfile_path):
    """Wrte to txt. Array with shape: (365, 24)"""
    out_dict = {}
    for k, row in enumerate(input_array):
        out_dict[k] = dict(enumerate(row))
    with open(outfile_path, 'w') as outfile:
        json.dump(out_dict, outfile)

def jason_to_txt_shape_d_peak(input_array, outfile_path):
    """Wrte to txt. Array with shape: ()"""
    with open(outfile_path, 'w') as outfile:
        json.dump(input_array, outfile)

def jason_to_txt_shape_d_non_peak(input_array, outfile_path):
    """Wrte to txt. Array with shape: (365, 1)"""
    out_dict = {}
    for k, row in enumerate(input_array):
        out_dict[k] = row[0]
    with open(outfile_path, 'w') as outfile:
        json.dump(out_dict, outfile)

def read_txt_shape_h_peak(file_path):
    """Read to txt. Array with shape: (24,)"""
    read_dict = json.load(open(file_path))
    read_dict_list = list(read_dict.values())
    out_dict = np.array(read_dict_list, dtype=float)
    return out_dict

def read_txt_shape_h_non_peak(file_path):
    """Read to txt. Array with shape: (365, 24)"""
    out_dict = np.zeros((365, 24))
    read_dict = json.load(open(file_path))
    read_dict_list = list(read_dict.values())
    for day, row in enumerate(read_dict_list):
        out_dict[day] = np.array(list(row.values()), dtype=float)
    return out_dict

def read_txt_shape_d_peak(file_path):
    """Read to txt. Array with shape: (365, 24)"""
    out_dict = json.load(open(file_path))
    return out_dict

def read_txt_shape_d_non_peak(file_path):
    """Read to txt. Array with shape: (365, 1)"""
    out_dict = np.zeros((365, 1))
    read_dict = json.load(open(file_path))
    read_dict_list = list(read_dict.values())
    for day, row in enumerate(read_dict_list):
        out_dict[day] = np.array(row, dtype=float)
    return out_dict
