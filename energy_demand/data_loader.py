"""Loads all necessary data"""
import os
from random import randint
#import matplotlib.pyplot as plt
import numpy as np
import energy_demand.data_loader_functions as df
import energy_demand.main_functions as mf
#import energy_demand.plot_functions as pf
# pylint: disable=I0011,C0321,C0301,C0103, C0325

def load_data(path_main, data):
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
    # PATH WITH DATA WHICH I'm NOT ALLOWED TO ULOAD ON GITHUB TODO: LOCAL DATA
    #Z:\01-Data_NISMOD\data_energy_demand
    folder_path_weater_data = os.path.join(data['local_data_path'], r'16-Met_office_weather_data\midas_wxhrly_201501-201512.csv')
    folder_path_weater_stations = os.path.join(data['local_data_path'], r'16-Met_office_weather_data\excel_list_station_details.csv')


    #folder_path_weater_data = r'C:\01-Private\99-Dropbox\Dropbox\00-Office_oxford\07-Data\16-Met_office_weather_data\midas_wxhrly_201501-201512.csv'
    #folder_path_weater_stations = r'C:\01-Private\99-Dropbox\Dropbox\00-Office_oxford\07-Data\16-Met_office_weather_data\excel_list_station_details.csv'
    print("FOLDERPATH: " + str(folder_path_weater_stations))

    # Fuel look-up table
    data['lu_fueltype'] = {
        'hybrid': 0,
        'gas': 1,
        'electricity': 2,
        'oil': 3,
        'heat_sold': 4,
        'bioenergy_waste':5,
        'hydrogen': 6,
        'coal': 7
    }
    data['nr_of_fueltypes'] = len(data['lu_fueltype'])

    # -----------------------------
    # Read in floor area of all regions and store in dict: TODO
    # -----------------------------
    #TODO: REGION LOOKUP: Generate region_lookup from input data (MAybe read in region_lookup from shape?)
    data['lu_reg'] = {}
    for reg_name in data['population'][data['base_yr']]:
        data['lu_reg'][reg_name] = reg_name

    #TODO: FLOOR_AREA_LOOKUP:
    data['reg_floorarea_resid'] = {}
    for reg_name in data['population'][data['base_yr']]:
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
        'path_lu_appliances_HES_matched': os.path.join(path_main, 'residential_model/lookup_appliances_HES_matched.csv'),
        'path_txt_service_tech_by_p': os.path.join(path_main, 'model_output/resid_service_tech_by_p.txt'),

        'path_shape_resid_cooling': os.path.join(path_main, 'residential_model/shape_residential_cooling.csv'),
        'path_out_stats_cProfile': os.path.join(path_main, '/model_output/stats_cProfile.txt'),

        # Technologies
        'path_assumptions_tech_resid': os.path.join(path_main, 'residential_model/technology_base_scenario.csv'),

        # Fuel switches
        'rs_path_fuel_switches': os.path.join(path_main, 'residential_model/switches_fuel_scenaric.csv'),
        'ss_path_fuel_switches': os.path.join(path_main, 'service_model/switches_fuel_scenaric.csv'),

        # Path to excel with ss service switch
        'rs_path_service_switch': os.path.join(path_main, 'residential_model/switches_service_scenaric.csv'),
        'ss_path_service_switch': os.path.join(path_main, 'service_model/switches_service_scenaric.csv'),

        # Paths to fuels
        'path_rs_fuel_raw_data_enduses': os.path.join(path_main, 'residential_model/data_residential_by_fuel_end_uses.csv'),
        'path_ss_fuel_raw_data_enduses': os.path.join(path_main, 'service_model/data_service_by_fuel_end_uses.csv'),

        # Paths to txt shapes
        'path_rs_txt_shapes': os.path.join(path_main, 'residential_model/txt_load_shapes'),
        'path_ss_txt_shapes': os.path.join(path_main, 'service_model/txt_load_shapes')
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

    temp_y = np.zeros((365, 24))
    for day in range(365):
        temp_y[day] += randint(-5, 30)

    data['temperature_data'][9] = temp_y #np.zeros((365, 24)) #10 # DUMMY DATA WITH CONSTANT 10 DEGREES
    data['weather_stations'] = {}
    data['weather_stations'][9] = data['weather_stations_raw'][9]
    # -----------
    #'''
    # ------------------------------------------
    # RESIDENTIAL SECTOR
    # ------------------------------------------
    data['temp_mean'] = mf.read_txt_t_base_by(data['path_dict']['path_temp_txt'], 2015)
    data['dwtype_lu'] = mf.read_csv_dict_no_header(data['path_dict']['path_dwtype_lu'])              # Dwelling types lookup table
    data['app_type_lu'] = mf.read_csv(data['path_dict']['path_lookup_appliances'])                   # Appliances types lookup table
    data['fuel_type_lu'] = mf.read_csv_dict_no_header(data['path_dict']['path_fuel_type_lu'])        # Fuel type lookup
    data['day_type_lu'] = mf.read_csv(data['path_dict']['path_day_type_lu'])                         # Day type lookup
    data['shapes_resid_heating_boilers_dh'] = mf.read_csv_float(data['path_dict']['path_hourly_gas_shape_resid']) # Load hourly shape for gas from Robert Sansom #TODO: REmove because in read_shp_heating_gas
    data['shapes_resid_heating_heat_pump_dh'] = mf.read_csv_float(data['path_dict']['path_hourly_gas_shape_hp']) # Load h
    data['lu_appliances_HES_matched'] = mf.read_csv(data['path_dict']['path_lu_appliances_HES_matched']) # Read in dictionary which matches enduses in HES data with enduses in ECUK data
    data['shapes_resid_cooling_dh'] = mf.read_csv_float(data['path_dict']['path_shape_resid_cooling'])

    # load shapes
    data['rs_shapes_dh'] = {}
    data['rs_shapes_yd'] = {}

    # ------------------------------------------
    # Read in raw fuel data of residential model
    # ------------------------------------------
    data['rs_fuel_raw_data_enduses'] = mf.read_csv_base_data_resid(data['path_dict']['path_rs_fuel_raw_data_enduses']) # Yearly end use data


    # Add fuel data of other model enduses to the fuel data table (E.g. ICT or wastewater) #TODO
    ###data = add_yearly_external_fuel_data(data, rs_fuel_raw_data_enduses) #TODO: ALSO IMPORT ALL OTHER END USE RELATED THINS SUCH AS SHAPE

    # Create dictionary with all enduses based on provided fuel data (after loading in external enduses)
    data['rs_all_enduses'] = create_enduse_dict(data, data['rs_fuel_raw_data_enduses'])

    # ---------------------------------------------------------------------------------------------------------------------------------------------------------
    # SERVICE SECTOR
    # ---------------------------------------------------------------------------------------------------------------------------------------------------------


    # Read fuels
    data['ss_fuel_raw_data_enduses'], data['all_service_sectors'], data['ss_all_enduses'] = mf.read_csv_base_data_service(data['path_dict']['path_ss_fuel_raw_data_enduses'], data['nr_of_fueltypes']) # Yearly end use data

    # ---------------------------------------------------------------------------------------------
    # --- Generate load shapes
    # ---------------------------------------------------------------------------------------------
    data = generate_data(data, data['rs_fuel_raw_data_enduses'], data['ss_fuel_raw_data_enduses']) # Otherwise already read out files are read in from txt files

    # -- Read in load shapes from files #TODO: Make that the correct txt depending on whetaer scenario are read in or out
    data = collect_shapes_from_txts(data, data['path_dict']['path_rs_txt_shapes'], data['path_dict']['path_rs_txt_shapes'])



   # ----------------------------------------
    # Convert units
    # ----------------------------------------
    # TODO: Check in what units external fuel data is provided
    '''for enduse in rs_fuel_raw_data_enduses:
        rs_fuel_raw_data_enduses[enduse] = mf.conversion_ktoe_gwh(rs_fuel_raw_data_enduses[enduse])
    #print("ENDUSES: " + str(rs_fuel_raw_data_enduses))
    '''

    # Residential Sector (TODO: REPLACE)
    data['rs_fuel_raw_data_enduses'] = data['rs_fuel_raw_data_enduses'] # rs_fuel_raw_data_enduses
    data['ss_fuel_raw_data_enduses'] = data['ss_fuel_raw_data_enduses'] #ss_fuel_raw_data_enduses



    # ---TESTS----------------------
    # Test if numer of fuel types is identical (Fuel lookup needs to have same dimension as end-use fuels)
    for end_use in data['rs_fuel_raw_data_enduses']:
        assert data['nr_of_fueltypes'] == len(data['rs_fuel_raw_data_enduses'][end_use]) # Fuel in fuel distionary does not correspond to len of input fuels

    return data


# ---------------------------------------------------
# All pre-processed load shapes are read in from .txt files
# ---------------------------------------------------
def collect_shapes_from_txts(data, rs_path_to_txts, ss_path_to_txts):
    """Rread in load shapes from text without accesing raw files
    """
    # ----------------------------------------------------------------------
    # RESIDENTIAL MODEL txt files
    # ----------------------------------------------------------------------
    # Iterate folders and get all enduse
    all_csv_in_folder = os.listdir(rs_path_to_txts)

    enduses = set([])
    for file_name in all_csv_in_folder:
        enduse = file_name.split("__")[0] # two dashes because individual enduses may contain a single slash
        enduses.add(enduse)

    # Read load shapes from txt files for enduses
    for end_use in enduses:
        shape_peak_dh = df.read_txt_shape_peak_dh(os.path.join(rs_path_to_txts, str(end_use) + str("__") + str('shape_peak_dh') + str('.txt')))
        shape_non_peak_dh = df.read_txt_shape_non_peak_yh(os.path.join(rs_path_to_txts, str(end_use) + str("__") + str('shape_non_peak_dh') + str('.txt')))
        shape_peak_yd_factor = df.read_txt_shape_peak_yd_factor(os.path.join(rs_path_to_txts, str(end_use) + str("__") + str('shape_peak_yd_factor') + str('.txt')))
        shape_non_peak_yd = df.read_txt_shape_non_peak_yd(os.path.join(rs_path_to_txts, str(end_use) + str("__") + str('shape_non_peak_yd') + str('.txt')))

        data['rs_shapes_dh'][end_use] = {'shape_peak_dh': shape_peak_dh, 'shape_non_peak_dh': shape_non_peak_dh}
        data['rs_shapes_yd'][end_use] = {'shape_peak_yd_factor': shape_peak_yd_factor, 'shape_non_peak_yd': shape_non_peak_yd}

    # ----------------------------------------------------------------------
    # SERVICE MODEL .txt files
    # ----------------------------------------------------------------------
    # Iterate folders and get all enduse
    all_csv_in_folder = os.listdir(ss_path_to_txts)

    enduses = set([])
    for file_name in all_csv_in_folder:
        enduse = file_name.split("__")[0] # two dashes because individual enduses may contain a single slash
        enduses.add(enduse)

    # Read load shapes from txt files for enduses
    for end_use in enduses:
        shape_peak_dh = df.read_txt_shape_peak_dh(os.path.join(ss_path_to_txts, str(end_use) + str("__") + str('shape_peak_dh') + str('.txt')))
        shape_non_peak_dh = df.read_txt_shape_non_peak_yh(os.path.join(ss_path_to_txts, str(end_use) + str("__") + str('shape_non_peak_dh') + str('.txt')))
        shape_peak_yd_factor = df.read_txt_shape_peak_yd_factor(os.path.join(ss_path_to_txts, str(end_use) + str("__") + str('shape_peak_yd_factor') + str('.txt')))
        shape_non_peak_yd = df.read_txt_shape_non_peak_yd(os.path.join(ss_path_to_txts, str(end_use) + str("__") + str('shape_non_peak_yd') + str('.txt')))

        data['ss_shapes_dh'][end_use] = {'shape_peak_dh': shape_peak_dh, 'shape_non_peak_dh': shape_non_peak_dh}
        data['ss_shapes_yd'][end_use] = {'shape_peak_yd_factor': shape_peak_yd_factor, 'shape_non_peak_yd': shape_non_peak_yd}

    # ----------------------------------------------------------------------
    # Industry MODEL .txt files
    # ----------------------------------------------------------------------

    return data

def generate_data(data, rs_raw_fuel, ss_raw_fuel):
    """This function loads all that which does not neet to be run every time
    """

    # ===========================================-
    # RESIDENTIAL MODEL - LOAD HES DATA
    # ===========================================
    path_txt_shapes = data['path_dict']['path_rs_txt_shapes']

    # HES data -- Generate generic load profiles (shapes) for all electricity appliances from HES data
    hes_data, hes_y_peak, _ = df.read_hes_data(data)
    year_raw_values_hes = df.assign_hes_data_to_year(data, hes_data, 2015)

    # Load shape for all end_uses
    for end_use in rs_raw_fuel:
        print("Enduse:  " + str(end_use))

        if end_use not in data['lu_appliances_HES_matched'][:, 1]:
            print("Warning: The enduse {} is not defined in lu_appliances_HES_matched, i.e. no generic shape is loades from HES data but enduse needs to be defined with technologies".format(end_use))
            continue

        # Get HES load shapes
        shape_peak_dh, shape_non_peak_dh, shape_peak_yd_factor, shape_non_peak_yd = df.get_hes_end_uses_shape(data, year_raw_values_hes, hes_y_peak, _, end_use)

        # Write .txt files
        df.create_txt_shapes(end_use, path_txt_shapes, shape_peak_dh, shape_non_peak_dh, shape_peak_yd_factor, shape_non_peak_yd, "") # Write shapes to txt


    # TODO: Add load shapes of external enduses (e.g. sewer treatment plants, )

    # ===========================================
    # SERVICE MODEL DATA GENERATION
    # ===========================================
    # ---------------------
    # Load Carbon Trust data - electricity for non-residential
    # ---------------------
    data['ss_shapes_dh'] = {}
    data['ss_shapes_yd'] = {}

    # Iterate sectors and read in shape
    for sector in data['all_service_sectors']:
        print("Read in shape {}".format(sector))
        data['ss_shapes_dh'][sector] = {}
        data['ss_shapes_yd'][sector] = {}

        # ------------------------------------------------------
        # Assign same shape across all enduse for service sector
        # ------------------------------------------------------
        for end_use in ss_raw_fuel[sector]:
            print("Enduse service: {}  in sector '{}'".format(end_use, sector))

            # Match shapes for every sector
            if sector == 'community_arts_leisure':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Community')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Community')

            if sector == 'education':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Education')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Education')

            if sector == 'emergency_services':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_elec')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_gas')

            if sector == 'health':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Health')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Health')

            if sector == 'hospitality':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_elec')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_gas')

            if sector == 'military':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_elec')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_gas')

            if sector == 'offices':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Offices')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Offices')

            if sector == 'retail':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Retail')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\Retail')

            if sector == 'storage':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_elec')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_gas')

            if sector == 'other':
                folder_path_elec = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_elec')
                folder_path_gas = os.path.join(data['local_data_path'], r'09_Carbon_Trust_advanced_metering_trial\_all_gas')

            # Use gas or electricity shape depending on dominante fuelt in enduse
            if end_use in ['ss_hot_water', 'ss_space_heating', 'other']:
                print("For enduse {} in sector {} use the gas shape ".format(end_use, sector))
                folder_path = folder_path_gas # Select gas shape
            else:
                print("For enduse {} in sector {} use the electricity shape ".format(end_use, sector))
                folder_path = folder_path_elec # Select electricity shape

            # Read in shape from carbon trust metering trial dataset
            shape_non_peak_dh, load_peak_shape_dh, shape_peak_yd_factor, shape_non_peak_yd = df.read_raw_carbon_trust_data(data, folder_path)

            # Assign shapes
            data['ss_shapes_dh'][sector][end_use] = {'shape_peak_dh': load_peak_shape_dh, 'shape_non_peak_dh': shape_non_peak_dh}
            data['ss_shapes_yd'][sector][end_use] = {'shape_peak_yd_factor': shape_peak_yd_factor, 'shape_non_peak_yd': shape_non_peak_yd}

            # Write txt
            df.create_txt_shapes(end_use, data['path_dict']['path_ss_txt_shapes'], load_peak_shape_dh, shape_non_peak_dh, shape_peak_yd_factor, shape_non_peak_yd, "") # Write shapes to txt

    # ---------------------
    # Compare Jan and Jul
    # ---------------------
    #df.compare_jan_jul(main_dict_dayyear_absolute)

    return data

def create_enduse_dict(data, rs_fuel_raw_data_enduses):
    """Create dictionary with all residential enduses and store in data dict

    For residential model

    Parameters
    ----------
    data : dict
        Main data dictionary

    rs_fuel_raw_data_enduses : dict
        Raw fuel data from external enduses (e.g. other models)

    Returns
    -------
    resid_enduses : list
        Ditionary with residential enduses
    """
    resid_enduses = []
    for ext_enduse in data['external_enduses_resid']: # Add external enduse
        resid_enduses.append(ext_enduse)

    for enduse in rs_fuel_raw_data_enduses: # Add resid enduses
        resid_enduses.append(enduse)

    return resid_enduses
