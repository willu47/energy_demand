"""Loads all necessary data"""
import os
import csv
#import unittest
import matplotlib.pyplot as plt
import numpy as np
import energy_demand.data_loader_functions as df
import energy_demand.main_functions as mf
import energy_demand.plot_functions as pf
# pylint: disable=I0011,C0321,C0301,C0103, C0325

def load_data(path_main, data_ext):
    """All base data no provided externally are loaded

    All necessary data to run energy demand model is loaded.
    This data is loaded in the wrapper.

    Parameters
    ----------
    data : dict
        Dict with own data
    path_main : str
        Path to all data of model run which are not provided externally by wrapper

    Returns
    -------
    data : list
        Returns a list where storing all data

    """
    data = {} # Data container


    # PATH WITH DATA WHICH I'm NOT ALLOWED TO ULOAD ON GITHUB TODO: LOCAL DATA
    folder_path_weater_data = r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\16-Met_office_weather_data\midas_wxhrly_201501-201512.csv'
    folder_path_weater_stations = r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\16-Met_office_weather_data\excel_list_station_details.csv'

    # Fuel look-up table
    data['lu_fueltype'] = {
        'solid_fuel': 0,
        'gas': 1,
        'electricity': 2,
        'oil': 3,
        'heat_sold': 4,
        'bioenergy_waste':5,
        'hydrogen': 6,
        'future_fuel': 7
    }

    # -----------------------------
    # Read in floor area of all regions and store in dict: TODO
    # -----------------------------
    #TODO: REGION LOOKUP: Generate region_lookup from input data (MAybe read in region_lookup from shape?)
    data['lu_reg'] = {}
    for reg_name in data_ext['population'][data_ext['glob_var']['base_yr']]:
        data['lu_reg'][reg_name] = reg_name

    #TODO: FLOOR_AREA_LOOKUP:
    data['reg_floorarea_resid'] = {}
    for reg_name in data_ext['population'][data_ext['glob_var']['base_yr']]:
        data['reg_floorarea_resid'][reg_name] = 100000

    # Paths
    data['path_dict'] = {

        # Residential
        # -----------
        'path_main': path_main,
        'path_temp_txt': os.path.join(path_main, 'scenario_and_base_data/mean_temp_data'),
        'path_pop_lu_reg': os.path.join(path_main, 'scenario_and_base_data/lookup_nr_regions.csv'),
        'path_dwtype_lu': os.path.join(path_main, 'residential_model/lookup_dwelling_type.csv'),
        'path_lookup_appliances':os.path.join(path_main, 'residential_model/lookup_appliances_HES.csv'),
        'path_fuel_type_lu': os.path.join(path_main, 'scenario_and_base_data/lookup_fuel_types.csv'),
        'path_day_type_lu': os.path.join(path_main, 'residential_model/lookup_day_type.csv'),
        'path_temp_2015': os.path.join(path_main, 'residential_model/SNCWV_YEAR_2015.csv'),
        'path_bd_e_load_profiles': os.path.join(path_main, 'residential_model/HES_base_appliances_eletricity_load_profiles.csv'),
        'path_hourly_gas_shape_resid': os.path.join(path_main, 'residential_model/SANSOM_residential_gas_hourly_shape.csv'),
        'path_hourly_gas_shape_hp': os.path.join(path_main, 'residential_model/SANSOM_residential_gas_hourly_shape_hp.csv'),
        'path_dwtype_age': os.path.join(path_main, 'residential_model/data_residential_model_dwtype_age.csv'),
        'path_dwtype_floorarea_dw_type': os.path.join(path_main, 'residential_model/data_residential_model_dwtype_floorarea.csv'),
        'path_reg_floorarea_resid': os.path.join(path_main, 'residential_model/data_residential_model_floorarea.csv'),
        'path_fuel_raw_data_resid_enduses': os.path.join(path_main, 'residential_model/data_residential_by_fuel_end_uses.csv'),
        'path_lu_appliances_HES_matched': os.path.join(path_main, 'residential_model/lookup_appliances_HES_matched.csv'),
        'path_txt_shapes_resid': os.path.join(path_main, 'residential_model/txt_load_shapes'),

        # Technologies
        'path_assumptions_STANDARD': os.path.join(path_main, 'residential_model/technology_base_scenario.csv'),
        'path_FUELSWITCHES': os.path.join(path_main, 'residential_model/fuel_switches_SCNEARIO.csv'), #SCENARIO

        # Service
        # -------
        'path_txt_shapes_service': os.path.join(path_main, 'service_model/txt_load_shapes')


        }

    # ----------------------------------------------------------
    # Read in weather data and clean data
    # ----------------------------------------------------------
    data['weather_stations_raw'] = df.read_weather_stations_raw(folder_path_weater_stations) # Read all weater stations properties
    '''data['temperature_data_raw'] = df.read_weather_data_raw(folder_path_weater_data, 9999) # Read in raw temperature data

    data['temperature_data'] = df.clean_weather_data_raw(data['temperature_data_raw'], 9999) # Clean weather data
    data['weather_stations'] = df.reduce_weather_stations(data['temperature_data'].keys(), data['weather_stations_raw']) # Reduce weater stations for which there is data provided
    print("Number of weater stations with cleaned data: " + str(len(data['weather_stations'].keys())))

    del data['weather_stations_raw'] # Delete raw data from data
    del data['temperature_data_raw'] # Delete raw data from data

    '''

    # SCRAP DUMMY DATA FOR FAST CALCULATION
    # -----------
    #print(data['weather_stations'].keys())
    data['temperature_data'] = {}
    data['temperature_data'][9] = np.zeros((365,24)) + 10 # DUMMY DATA WITH CONSTANT 10 DEGREES
    data['weather_stations'] = {}
    data['weather_stations'][9] = data['weather_stations_raw'][9]
    # -----------


    # ------------------------------------------
    # RESIDENTIAL SECTOR
    # ------------------------------------------
    data['temp_mean'] = mf.read_txt_t_base_by(data['path_dict']['path_temp_txt'], 2015)
    data['dwtype_lu'] = mf.read_csv_dict_no_header(data['path_dict']['path_dwtype_lu'])              # Dwelling types lookup table
    data['app_type_lu'] = mf.read_csv(data['path_dict']['path_lookup_appliances'])                   # Appliances types lookup table
    data['fuel_type_lu'] = mf.read_csv_dict_no_header(data['path_dict']['path_fuel_type_lu'])        # Fuel type lookup
    data['day_type_lu'] = mf.read_csv(data['path_dict']['path_day_type_lu'])                         # Day type lookup
    data['hourly_gas_shape'] = mf.read_csv_float(data['path_dict']['path_hourly_gas_shape_resid']) # Load hourly shape for gas from Robert Sansom #TODO: REmove because in read_shp_heating_gas
    data['hourly_gas_shape_hp'] = mf.read_csv_float(data['path_dict']['path_hourly_gas_shape_hp']) # Load h
    #data['dwtype_age_distr'] = mf.read_csv_nested_dict(data['path_dict']['path_dwtype_age'])
    data['temp_2015_resid'] = mf.read_csv(data['path_dict']['path_temp_2015'])                       # Residential daily gas data

    data['lu_appliances_HES_matched'] = mf.read_csv(data['path_dict']['path_lu_appliances_HES_matched']) # Read in dictionary which matches enduses in HES data with enduses in ECUK data

    # load shapes
    data['dict_shp_enduse_resid_dh'] = {}
    data['dict_shp_enduse_resid_yd'] = {}

    # Read in raw fuel data of residential model
    fuel_raw_data_resid_enduses = mf.read_csv_base_data_resid(data['path_dict']['path_fuel_raw_data_resid_enduses']) # Yearly end use data

    
    # Add fuel data of other model enduses to the fuel data table (E.g. ICT or wastewater) #TODO
    ###data = add_yearly_external_fuel_data(data, data_ext, fuel_raw_data_resid_enduses) #TODO: ALSO IMPORT ALL OTHER END USE RELATED THINS SUCH AS SHAPE

    # Create dictionary with all enduses based on provided fuel data (after loading in external enduses)
    data = create_enduse_dict(data, data_ext, fuel_raw_data_resid_enduses)


    # ---------------------------------------------------------------------------------------------------------------------------------------------------------
    # SERVICE SECTOR
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------
    data['dict_shp_enduse_h_service'] = {}
    data['dict_shp_enduse_d_service'] = {}






    # ----------------------------------------
    # Convert loaded data into correct units
    # ----------------------------------------
    # TODO: Check in what units external fuel data is provided

    # Residential #TODO: DO CONVERSION
    '''for enduse in fuel_raw_data_resid_enduses:
        fuel_raw_data_resid_enduses[enduse] = mf.conversion_ktoe_gwh(fuel_raw_data_resid_enduses[enduse])
    #print("ENDUSES: " + str(fuel_raw_data_resid_enduses))
    '''

    data['fuel_raw_data_resid_enduses'] = fuel_raw_data_resid_enduses


    # ---------------------------------------------------------------------------------------------
    # --- Generate load_shape
    # ---------------------------------------------------------------------------------------------
    data = generate_data(data) # Otherwise already read out files are read in from txt files

    # -- Read in load shapes from files #TODO: Make that the correct txt depending on whetaer scenario are read in or out
    data = collect_shapes_from_txts(data)








    # ---TESTS----------------------
    # Test if numer of fuel types is identical (Fuel lookup needs to have same dimension as end-use fuels)
    for end_use in data['fuel_raw_data_resid_enduses']:
        assert len(data['fuel_type_lu']) == len(data['fuel_raw_data_resid_enduses'][end_use]) # Fuel in fuel distionary does not correspond to len of input fuels

    scrap = 0
    for enduse in data['fuel_raw_data_resid_enduses']:
        scrap += np.sum(fuel_raw_data_resid_enduses[enduse])
    print("scrap FUELS FINAL FOR OUT: " + str(scrap))
    # ---TESTS----------------------

    return data


# ---------------------------------------------------
# All pre-processed load shapes are read in from .txt files
# ---------------------------------------------------
def collect_shapes_from_txts(data):
    """Rread in load shapes from text without accesing raw files
    """

    # ----------------------------------------------------------------------
    # RESIDENTIAL MODEL txt files
    # ----------------------------------------------------------------------
    # Iterate folders and get all enduse
    all_csv_in_folder = os.listdir(data['path_dict']['path_txt_shapes_resid'])

    enduses = []
    for file_name in all_csv_in_folder:
        enduse = file_name.split("__")[0] # two dashes because individual enduses may contain a single slash
        if enduse not in enduses:
            enduses.append(enduse)

    # Read load shapes from txt files
    for end_use in enduses:
        shape_peak_dh = df.read_txt_shape_peak_dh(os.path.join(data['path_dict']['path_txt_shapes_resid'], str(end_use) + str("__") + str('shape_peak_dh') + str('.txt')))
        shape_non_peak_h = df.read_txt_shape_non_peak_yh(os.path.join(data['path_dict']['path_txt_shapes_resid'], str(end_use) + str("__") + str('shape_non_peak_h') + str('.txt')))
        shape_peak_yd = df.read_txt_shape_peak_yd(os.path.join(data['path_dict']['path_txt_shapes_resid'], str(end_use) + str("__") + str('shape_peak_yd') + str('.txt')))
        shape_non_peak_yd = df.read_txt_shape_non_peak_yd(os.path.join(data['path_dict']['path_txt_shapes_resid'], str(end_use) + str("__") + str('shape_non_peak_yd') + str('.txt')))
        data['dict_shp_enduse_resid_dh'][end_use] = {'shape_peak_dh': shape_peak_dh, 'shape_non_peak_h': shape_non_peak_h}
        data['dict_shp_enduse_resid_yd'][end_use] = {'shape_peak_yd': shape_peak_yd, 'shape_non_peak_yd': shape_non_peak_yd}

    # ----------------------------------------------------------------------
    # SERVICE MODEL .txt files
    # ----------------------------------------------------------------------


    # ----------------------------------------------------------------------
    # Industry MODEL .txt files
    # ----------------------------------------------------------------------

    return data

def generate_data(data):
    """This function loads all that which does not neet to be run every time"""

    base_yr_load_data = 2015

    # ===========================================-
    # RESIDENTIAL MODEL
    # ===========================================
    path_txt_shapes = data['path_dict']['path_txt_shapes_resid']

    # HES data -- Generate generic load profiles (shapes) for all electricity appliances from HES data
    hes_data, hes_y_peak, _ = df.read_hes_data(data)
    year_raw_values_hes = df.assign_hes_data_to_year(data, hes_data, base_yr_load_data)

    # Load shape for all end_uses
    for end_use in data['fuel_raw_data_resid_enduses']:
        if end_use not in data['lu_appliances_HES_matched'][:, 1]: #Enduese not in HES data
            continue

        # Get HES load shapes
        shape_peak_dh, shape_non_peak_h, shape_peak_yd_factor, shape_non_peak_yd = df.get_hes_end_uses_shape(data, year_raw_values_hes, hes_y_peak, _, end_use)

        print("TEST:")
        print(len(shape_peak_dh))
        print(len(shape_non_peak_h))
        print(shape_peak_yd_factor)
        print(len(shape_non_peak_yd))
        #prnt("..")

        df.create_txt_shapes(end_use, path_txt_shapes, shape_peak_dh, shape_non_peak_h, shape_peak_yd_factor, shape_non_peak_yd, "") # Write shapes to txt

    # Robert Sansom, Yearly peak from CSWV - Residential Gas demand, Daily shapes
    wheater_scenarios = ['actual'] #, 'max_cold', 'min_warm'# Different wheater scenarios to iterate #TODO: MAybe not necessary to read in indivdual shapes for different wheater scneario

    # Iterate wheater scenarios
    for wheater_scen in wheater_scenarios:
        shape_peak_dh, shape_non_peak_h, shape_peak_yd, shape_non_peak_yd = df.read_shp_heating_gas(data, 'residential', wheater_scen) # Composite Wheater Variable for residential gas heating
        df.create_txt_shapes('space_heating', path_txt_shapes, shape_peak_dh, shape_non_peak_h, shape_peak_yd, shape_non_peak_yd, wheater_scen) # Write shapes to txt

    # TODO
    # Add load shapes of external enduses (e.g. sewer treatment plants, )




    # ===========================================
    # SERVICE MODEL DATA GENERATION
    # ===========================================


    # ----------------------------
    # Service Gas demand
    # ----------------------------

    # ---------------------
    # Load Carbon Trust data - electricity for non-residential
    # ---------------------
    #folder_path_elec = r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\09_Carbon_Trust_advanced_metering_trial_(owen)\_all_elec' #Community _OWN_SEWAGE Education
    #folder_path_gas= r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\09_Carbon_Trust_advanced_metering_trial_(owen)\_all_gas' #Community _OWN_SEWAGE Education
    folder_path_elec= r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\09_Carbon_Trust_advanced_metering_trial_(owen)\Education' #Community _OWN_SEWAGE Education

    # ENDUSE XY
    #out_dict_av, _, hourly_shape_of_maximum_days, main_dict_dayyear_absolute = df.read_raw_carbon_trust_data(data, folder_path_elec)

    #print(out_dict_av)
    #print(hourly_shape_of_maximum_days)
    #print(main_dict_dayyear_absolute)

    #path_txt_shapes_service = data['path_dict']['path_txt_shapes_service']

    #df.create_txt_shapes('service_all_elec', path_txt_shapes_service, shape_peak_yh, shape_non_peak_h, shape_peak_yd, shape_non_peak_yd, "scrap")

    # Compare Jan and Jul
    #df.compare_jan_jul(main_dict_dayyear_absolute)


    # Get yearly profiles
    enduse = 'WHATEVERENDUSE'
    #year_data = df.assign_carbon_trust_data_to_year(data, enduse, out_dict_av, base_yr_load_data) #TODO: out_dict_av is percentages of day sum up to one

    #out_dict_av [daytype, month, ...] ---> Calculate yearly profile with averaged monthly profiles

    # ENDUSE XY
    #folder_path = r'C:\Users\cenv0553\Dropbox\00-Office_oxford\07-Data\09_Carbon_Trust_advanced_metering_trial_(owen)\__OWN_SEWAGE' #Community _OWN_SEWAGE


    return data

def create_enduse_dict(data, data_ext, fuel_raw_data_resid_enduses):
    """Create dictionary with all residential enduses and store in data dict

    For residential model

    Parameters
    ----------
    data : dict
        Main data dictionary

    data_ext : dict
        Main external ditionary

    fuel_raw_data_resid_enduses : dict
        Raw fuel data from external enduses (e.g. other models)

    Returns
    -------
    data : dict
        Main data dictionary with added enduse dictionary
    """
    data['resid_enduses'] = {}
    for ext_enduse in data_ext['external_enduses_resid']: # Add external enduse
        data['resid_enduses'][ext_enduse] = ext_enduse

    for enduse in fuel_raw_data_resid_enduses: # Add resid enduses
        data['resid_enduses'][enduse] = enduse

    return data
