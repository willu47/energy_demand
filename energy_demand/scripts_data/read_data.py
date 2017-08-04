"""Reading raw data
"""
import sys
import csv
import numpy as np
from energy_demand.scripts_technologies import technologies_related
# pylint: disable=I0011,C0321,C0301,C0103, C0325

def convert_out_format_es(data, model_run_object, sub_modules):
    """Adds total hourly fuel data into nested dict

    Parameters
    ----------
    data : dict
        Dict with own data
    model_run_object : object
        Contains objects of the region

    Returns
    -------
    results : dict
        Returns a list for energy supply model with fueltype, region, hour
    """
    print("...Convert to dict for energy_supply_model")
    control_total_sum = 0
    results = {}

    for fueltype, fueltype_id in data['lu_fueltype'].items():
        results[fueltype] = []
        control_sum = 0
        for region_name in data['lu_reg']:

            hourly_all_fuels = model_run_object.get_fuel_region_all_models_yh(
                data,
                region_name,
                sub_modules,
                'enduse_fuel_yh')

            for day, day_demand in enumerate(hourly_all_fuels[fueltype_id]):
                for hour, hour_demand in enumerate(day_demand):
                    result = (region_name, "{}_{}".format(day, hour), float(hour_demand), "units")
                    results[fueltype].append(result)

                    control_sum += hour_demand

        print("Model output: fueltype {}   {}".format(fueltype, control_sum))
        control_total_sum += control_sum
    print(" ----------")
    print("Total Sum  {} ".format(control_total_sum))
    return results

def read_csv_base_data_service(path_to_csv, nr_of_fueltypes):
    """This function reads in base_data_CSV all fuel types

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    nr_of_fueltypes : str
        Nr of fueltypes

    Returns
    -------
    elements_array : dict
        Returns an dict with arrays

    Notes
    -----
    the first row is the fuel_ID
    The header is the sub_key
    """
    lines = []
    end_uses_dict = {}

    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',')
        _headings = next(read_lines) # Skip first row
        _secondline = next(read_lines) # Skip first row

        # All sectors
        all_sectors = set([])
        for sector in _secondline[1:]: #skip fuel ID:
            all_sectors.add(sector)

        # All enduses
        all_enduses = set([])
        for enduse in _headings[1:]: #skip fuel ID:
            all_enduses.add(enduse)

        # Initialise dict
        for sector in all_sectors:
            end_uses_dict[sector] = {}
            for enduse in all_enduses:
                end_uses_dict[sector][enduse] = np.zeros((nr_of_fueltypes))

        # Iterate rows
        for row in read_lines:
            lines.append(row)

        for cnt_fueltype, row in enumerate(lines):
            for cnt, entry in enumerate(row[1:], 1):
                enduse = _headings[cnt]
                sector = _secondline[cnt]
                end_uses_dict[sector][enduse][cnt_fueltype] += float(entry)

    return end_uses_dict, list(all_sectors), list(all_enduses)

def read_csv_dict_no_header(path_to_csv):
    """Read in csv file into a dict (without header)

    Parameters
    ----------
    path_to_csv : str
        Path to csv file

    Returns
    -------
    out_dict : dict
        Dictionary with first row element as main key and headers as key for nested dict.
        All entries and main key are returned as float

    Info
    -------
    Example:

        Year    Header1 Header2
        1990    Val1    Val2

        returns {{str(Year): float(1990), str(Header1): float(Val1), str(Header2): float(Val2)}}
    """
    out_dict = {}
    with open(path_to_csv, 'r') as csvfile:               # Read CSV file
        read_lines = csv.reader(csvfile, delimiter=',')   # Read line
        _headings = next(read_lines)                      # Skip first row

        for row in read_lines: # Iterate rows
            try:
                out_dict[int(row[0])] = float(row[1])
            except ValueError:
                out_dict[int(row[0])] = str(row[1])

    return out_dict

def read_csv_float(path_to_csv):
    """This function reads in CSV files and skips header row.

    Parameters
    ----------
    path_to_csv : str
        Path to csv file

    Returns
    -------
    elements_array : array_like
        Returns an array `elements_array` with the read in csv files.

    Notes
    -----
    The header row is always skipped.
    """
    service_switches = []

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',') # Read line
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            service_switches.append(row)

    return np.array(service_switches, float)

def read_csv_load_shapes_technology(path_to_csv):
    """This function reads in csv technology shapes

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    """
    load_shapes_dh = {}

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',') # Read line
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            dh_shape = np.zeros(24)
            for cnt, row_entry in enumerate(row[1:], 1):
                dh_shape[int(_headings[cnt])] = float(row_entry)

            load_shapes_dh[str(row[0])] = dh_shape

    return load_shapes_dh

def read_csv(path_to_csv):
    """This function reads in CSV files and skips header row.

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    _dt : str
        Defines dtype of array to be read in (takes float)

    Returns
    -------
    elements_array : array_like
        Returns an array `elements_array` with the read in csv files.

    Notes
    -----
    The header row is always skipped.
    """
    service_switches = []
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',')
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            service_switches.append(row)

    return np.array(service_switches) # Convert list into array

def read_service_switch(path_to_csv, all_specified_tech_enduse_by):
    """This function reads in service assumptions from csv file

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    all_specified_tech_enduse_by : dict

    Returns
    -------
    dict_with_switches : dict
        All assumptions about fuel switches provided as input
    enduse_tech_maxl_by_p : dict
        Maximum service per technology which can be switched
    service_switches : dict
        Service switches
    #service_switch_enduse_crit : dict
    #    Criteria whether service switches are defined in an enduse.
    # If no assumptions about service switches, return empty dicts

    Notes
    -----
    The base year service shares are generated from technology stock definition
    - skips header row
    - It also test if plausible inputs
    While not only loading in all rows, this function as well tests if inputs are plausible (e.g. sum up to 100%)
    """
    service_switches = []
    enduse_tech_ey_p = {}
    enduse_tech_maxl_by_p = {}
    service_switch_enduse_crit = {} #Store to list enduse specific switchcriteria (true or false)

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',')
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            try:
                service_switches.append(
                    {
                        'enduse': str(row[0]),
                        'tech': str(row[1]),
                        'service_share_ey': float(row[2]),
                        'tech_assum_max_share': float(row[3])
                    }
                )
            except (KeyError, ValueError):
                sys.exit("Error in loading service switch: Check if provided data is complete (no emptly csv entries)")

    # Group all entries according to enduse
    all_enduses = []
    for line in service_switches:
        enduse = line['enduse']
        if enduse not in all_enduses:
            all_enduses.append(enduse)
            enduse_tech_ey_p[enduse] = {}
            enduse_tech_maxl_by_p[enduse] = {}

    # Iterate all endusese and assign all lines
    for enduse in all_enduses:
        for line in service_switches:
            if line['enduse'] == enduse:
                tech = line['tech']
                enduse_tech_ey_p[enduse][tech] = line['service_share_ey']
                enduse_tech_maxl_by_p[enduse][tech] = line['tech_assum_max_share']

    # ------------------------------------------------
    # Testing wheter the provided inputs make sense
    # -------------------------------------------------
    for enduse in all_specified_tech_enduse_by:
        if enduse in service_switch_enduse_crit: #If switch is defined for this enduse
            for tech in all_specified_tech_enduse_by[enduse]:
                if tech not in enduse_tech_ey_p[enduse]:
                    sys.exit("Error XY: No end year service share is defined for technology '{}' for the enduse '{}' ".format(tech, enduse))

    # Test if more service is provided as input than possible to maximum switch
    for entry in service_switches:
        if entry['service_share_ey'] > entry['tech_assum_max_share']:
            sys.exit("Error: More service switch is provided for tech '{}' in enduse '{}' than max possible".format(entry['enduse'], entry['tech']))

    # Test if service of all provided technologies sums up to 100% in the end year
    for enduse in enduse_tech_ey_p:
        if round(sum(enduse_tech_ey_p[enduse].values()), 2) != 1.0:
            sys.exit("Error while loading future services assumptions: The provided ey service switch of enduse '{}' does not sum up to 1.0 (100%)".format(enduse))

    # ------------------------------------------------------
    # Add all other enduses for which no switch is defined
    # ------------------------------------------------------
    for enduse in all_specified_tech_enduse_by:
        if enduse not in enduse_tech_ey_p:
            enduse_tech_ey_p[enduse] = {}

    return enduse_tech_ey_p, enduse_tech_maxl_by_p, service_switches

def read_assump_fuel_switches(path_to_csv, data):
    """This function reads in from CSV file defined fuel switch assumptions

    Parameters
    ----------
    path_to_csv : str
        Path to csv file

    Returns
    -------
    dict_with_switches : dict
        All assumptions about fuel switches provided as input
    """
    service_switches = []

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',') # Read line
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            try:
                service_switches.append(
                    {
                        'enduse': str(row[0]),
                        'enduse_fueltype_replace': data['lu_fueltype'][str(row[1])],
                        'technology_install': str(row[2]),
                        'year_fuel_consumption_switched': float(row[3]),
                        'share_fuel_consumption_switched': float(row[4]),
                        'max_theoretical_switch': float(row[5])
                    }
                )
            except (KeyError, ValueError):
                sys.exit("Error in loading fuel switch: Check if provided data is complete (no emptly csv entries)")

    # -------------------------------------------------
    # Testing wheter the provided inputs make sense
    # -------------------------------------------------
    for element in service_switches:
        if element['share_fuel_consumption_switched'] > element['max_theoretical_switch']:
            sys.exit("Error while loading fuel switch assumptions: More fuel is switched than theorically possible for enduse '{}' and fueltype '{}".format(element['enduse'], element['enduse_fueltype_replace']))

        if element['share_fuel_consumption_switched'] == 0:
            sys.exit("Error: The share of switched fuel needs to be bigger than than 0 (otherwise delete as this is the standard input)")

    # Test if more than 100% per fueltype is switched
    for element in service_switches:
        enduse = element['enduse']
        fuel_type = element['enduse_fueltype_replace']

        tot_share_fueltype_switched = 0
        # Do check for every entry
        for element_iter in service_switches:
            if enduse == element_iter['enduse'] and fuel_type == element_iter['enduse_fueltype_replace']:
                # Found same fueltypes which is switched
                tot_share_fueltype_switched += element_iter['share_fuel_consumption_switched']

        if tot_share_fueltype_switched > 1.0:
            print("SHARE: " + str(tot_share_fueltype_switched))
            sys.exit("ERROR: The defined fuel switches are larger than 1.0 for enduse {} and fueltype {}".format(enduse, fuel_type))

    # Test whether defined enduse exist
    for element in service_switches:
        if element['enduse'] in data['ss_all_enduses'] or element['enduse'] in data['rs_all_enduses'] or element['enduse'] in data['is_all_enduses']:
            pass
        else:
            sys.exit("ERROR: The defined enduse '{}' to switch fuel from is not defined...".format(element['enduse']))

    return service_switches

def read_technologies(path_to_csv, data):
    """This function reads in CSV files and skips header row.

    Parameters
    ----------
    path_to_csv : str
        Path to csv file

    Returns
    -------
    dict_technologies : dict
        All technologies and their assumptions provided as input
    """
    dict_technologies = {}

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',') # Read line
        _headings = next(read_lines) # Skip first row

        # Iterate rows
        for row in read_lines:
            technology = row[0]

            # Because for hybrid technologies, none needs to be defined
            if row[1] == 'hybrid':
                fueltype = 'None'
            else:
                fueltype = data['lu_fueltype'][str(row[1])]

            dict_technologies[technology] = {
                'fuel_type': fueltype,
                'eff_by': float(row[2]),
                'eff_ey': float(row[3]),
                'eff_achieved': float(row[4]),
                'diff_method': str(row[5]),
                'market_entry': float(row[6])
            }

    return dict_technologies

def read_csv_base_data_resid(path_to_csv):
    """This function reads in base_data_CSV all fuel types

    (first row is fueltype, subkey), header is appliances

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    _dt : str
        Defines dtype of array to be read in (takes float)

    Returns
    -------
    elements_array : dict
        Returns an dict with arrays

    Notes
    -----
    the first row is the fuel_ID
    The header is the sub_key
    """
    try:
        lines = []
        end_uses_dict = {}

        with open(path_to_csv, 'r') as csvfile:
            read_lines = csv.reader(csvfile, delimiter=',')
            _headings = next(read_lines) # Skip first row

            # Iterate rows
            for row in read_lines:
                lines.append(row)

            for i in _headings[1:]: # skip first
                end_uses_dict[i] = np.zeros((len(lines)))

            for cnt_fueltype, row in enumerate(lines):
                cnt = 1 #skip first
                for i in row[1:]:
                    end_use = _headings[cnt]
                    end_uses_dict[end_use][cnt_fueltype] = i
                    cnt += 1
    except (KeyError, ValueError):
        sys.exit("Error: Check whether tehre any empty cells in the csv files for enduse '{}".format(end_use))

    # Create list with all rs enduses
    all_enduses = []
    for enduse in end_uses_dict:
        all_enduses.append(enduse)

    return end_uses_dict, all_enduses

def read_csv_base_data_industry(path_to_csv, nr_of_fueltypes, lu_fueltypes):
    """This function reads in base_data_CSV all fuel types

    Parameters
    ----------
    path_to_csv : str
        Path to csv file
    _dt : str
        Defines dtype of array to be read in (takes float)

    Returns
    -------
    elements_array : dict
        Returns an dict with arrays

    Notes
    -----
    the first row is the fuel_ID
    The header is the sub_key
    """
    lines = []
    end_uses_dict = {}

    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',')
        _headings = next(read_lines)
        _secondline = next(read_lines)

        # All sectors
        all_enduses = set([])
        for enduse in _headings[1:]:
            if enduse is not '':
                all_enduses.add(enduse)

        # All enduses
        all_sectors = set([])
        for line in read_lines:
            lines.append(line)
            all_sectors.add(line[0])

        # Initialise dict
        for sector in all_sectors:
            end_uses_dict[sector] = {}
            for enduse in all_enduses:
                end_uses_dict[str(sector)][str(enduse)] = np.zeros((nr_of_fueltypes))

        for row in lines:
            sector = row[0]
            for position, entry in enumerate(row[1:], 1): # Start with position 1

                if entry != '':
                    enduse = str(_headings[position])
                    fueltype = _secondline[position]
                    fueltype_int = technologies_related.get_fueltype_int(lu_fueltypes, fueltype)
                    end_uses_dict[sector][enduse][fueltype_int] += float(row[position])

    return end_uses_dict, list(all_sectors), list(all_enduses)
