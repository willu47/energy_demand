""" Building Generator"""
# pylint: disable=I0011,C0321,C0301,C0103, C0325, R0902, R0913, R0914
import energy_demand.building_stock_functions as bf
import energy_demand.main_functions as mf
import numpy as np

def resid_build_stock(data, assumptions, data_ext):
    """Creates a virtual building stock based on base year data and assumptions

    Parameters
    ----------
    data : dict
        Base data (data loaded)
    assumptions : dict
        All assumptions
    data_ext : dict
        Data provided externally from simulation

    Returns
    -------
    data : dict
        Adds reg_dw_stock_by and reg_building_stock_yr to the data dictionary:

        reg_dw_stock_by : Base year building stock
        reg_building_stock_yr : Building stock for every simulation year

    Notes
    -----
    The assumption about internal temperature change is used as for each dwelling the hdd are calculated
    based on wheater data and assumption on t_base. 

    The header row is always skipped.
    Needs as an input all population changes up to simulation period....(to calculate built housing)

    """
    reg_dw_stock_cy, reg_dw_stock_by, dw_stock_new_dw = {}, {}, []

    # Base year data
    glob_var = data_ext['glob_var']
    base_year = glob_var['base_year']

    dwtype_distr_by = assumptions['assump_dwtype_distr_by']
    dwtype_distr_ey = assumptions['assump_dwtype_distr_ey']

    dwtype_age_distr_by = data['dwtype_age_distr'][base_year]  # Age distribution of dwelling types    {2015: {1918: 20.8, 1928: 36.3, 1949: 29.4, 1968: 8.0, 1995: 5.4}} # year, average_age, percent
    reg_lu = data['reg_lu']                                    # Regions

    sim_period = range(base_year, glob_var['end_yr'] + 1, 1)         #base year, current year + 1, iteration step

    # Get distribution of dwelling types of all simulation years
    dwtype_distr_sim = bf.get_dwtype_dist(dwtype_distr_by, dwtype_distr_ey, glob_var) # Calculate distribution of dwelling types over simulation period

    # Get floor area per person for every simulation year
    data_floorarea_pp = bf.calc_floorarea_pp(data['reg_floorarea'], data_ext['population'][base_year], glob_var, assumptions['assump_change_floorarea_pp']) # Get floor area per person of sim_yr

    # Todo if necessary: Possible to implement that absolute size of households changes #floorarea_by_pd_cy = floorarea_by_pd  ### #TODO:floor area per dwelling get new floorarea_by_pd (if not constant over time, cann't extrapolate for any year)
    floorarea_p_sy = p_floorarea_dwtype(data['dwtype_lu'], assumptions['assump_dwtype_floorarea'], dwtype_distr_sim)
    print(data['dwtype_lu'])
    print(assumptions['assump_dwtype_floorarea'])
    print(dwtype_distr_sim)
    print("floorarea_p_sy: " + str(floorarea_p_sy))

    # Iterate regions
    for reg_id in reg_lu:
        floorarea_by = data['reg_floorarea'][reg_id]        # Read in floor area of base year
        pop_by = data_ext['population'][base_year][reg_id]  # Read in population
        floorarea_pp_by = floorarea_by / pop_by             # Floor area per person [m2/person]

        # Iterate simulation year
        for sim_y in sim_period:

            # Calculate new necessary floor area of simulation year
            floorarea_pp_sy = data_floorarea_pp[reg_id][sim_y] # Get floor area per person of sim_yr
            tot_floorarea_sy = floorarea_pp_sy * data_ext['population'][sim_y][reg_id] # Floor area per person simulation year * population of simulation year in region
            new_floorarea_sy = tot_floorarea_sy - floorarea_by # tot new floor area - area base year

            # Only calculate changing
            if sim_y == base_year:
                print(floorarea_p_sy)
                dw_stock_base = generate_dw_existing(data, reg_id, sim_y, data['dwtype_lu'], floorarea_p_sy[base_year], floorarea_by, dwtype_age_distr_by, floorarea_pp_by, floorarea_by, pop_by, assumptions, data_ext)
                dw_stock_new_dw = dw_stock_base # IF base year, the cy dwellign stock is the base year stock (bug found)
            else:
                # - existing dwellings
                # The number of people in the existing dwelling stock may change. Therfore calculate alos except for base year. Total floor number is assumed to be identical Here age of buildings could be changed
                dw_stock_new_dw = generate_dw_existing(data, reg_id, sim_y, data['dwtype_lu'], floorarea_p_sy[base_year], floorarea_by, dwtype_age_distr_by, floorarea_pp_sy, floorarea_by, floorarea_by/floorarea_pp_sy, assumptions, data_ext)

                # - new dwellings
                if new_floorarea_sy > 0: # If new floor area new buildings are necessary
                    dw_stock_new_dw = generate_dw_new(data, reg_id, sim_y, data['dwtype_lu'], floorarea_p_sy[sim_y], floorarea_pp_sy, dw_stock_new_dw, new_floorarea_sy, assumptions, data_ext)

        # Generate region and save it in dictionary
        reg_dw_stock_cy[reg_id] = bf.DwStockRegion(reg_id, dw_stock_new_dw) # Add old and new buildings to stock
        reg_dw_stock_by[reg_id] = bf.DwStockRegion(reg_id, dw_stock_base) # Add base year stock

    #print("Base dwelling")
    #print(reg_dw_stock_by[0].get_tot_pop())
    #l = reg_dw_stock_by[0].dwellings

    ##print("Curryear dwelling")
    #print(reg_dw_stock_cy[0].get_tot_pop())
    #l = reg_dw_stock_cy[0].dwellings
    #for i in l:
    #    print(i.__dict__)

    data['reg_dw_stock_by'] = reg_dw_stock_by # Add to data
    data['reg_dw_stock_cy'] = reg_dw_stock_cy # Add to data

    return data

def p_floorarea_dwtype(dw_lookup, dw_floorarea_by, dwtype_distr_sim):
    """Calculates the percentage of the total floor area belonging to each dwelling type

    Depending on average floor area per dwelling type and the dwelling type
    distribution, the percentages are calculated for ever simulation year

    Parameters
    ----------
    dw_lookup : dw_lookup
        Dwelling types
    dw_floorarea_by : dict
        floor area per type
    dw_nr_by : int
        Number of dwellings of base year
    dwtype_distr_sim : dict
        Distribution of dwelling time over the simulation period
    dwtype_floorarea : dict
        Average Floor are per dwelling type of base year

    Returns
    -------
    dw_floorarea_p : dict
        Contains the percentage of the total floor area for each dwtype for every simulation year (must be 1.0 in tot)

    Notes
    -----
    This calculation is necessary as the share of dwelling types may differ depending the year
    """
    dw_floorarea_p = {} # Initialise percent of total floor area per dwelling type
    print("dwtype_distr_sim" + str(dwtype_distr_sim))
    # Itreate simulation years
    for sim_yr in dwtype_distr_sim:
        y_dict, _tot_area = {}, 0

        for dw_id in dw_lookup:
            dw_name = dw_lookup[dw_id]

            # Calculate share of dwelling area based on absolute size and distribution
            p_buildings_dw = dwtype_distr_sim[sim_yr][dw_name]  # Get distribution of dwellings of simulation year
            _area_dw = p_buildings_dw * dw_floorarea_by[dw_name] # Get absolut size of dw_type

            _tot_area += _area_dw
            y_dict[dw_name] = _area_dw

        # Convert absolute values into percentages
        for i in y_dict:
            y_dict[i] = (1/_tot_area)*y_dict[i]
        dw_floorarea_p[sim_yr] = y_dict

    return dw_floorarea_p

def generate_dw_existing(data, reg_id, curr_yr, dw_lu, floorarea_p, floorarea_by, dwtype_age_distr_by, floorarea_pp_by, tot_floorarea_cy, pop_by, assumptions, data_ext):
    """Generates dwellings according to age, floor area and distribution assumptsion"""

    dw_stock_base, control_pop, control_floorarea = [], 0, 0

    # Iterate dwelling types
    for dw in dw_lu:
        dw_type_id, dw_type_name = dw, dw_lu[dw]
        dw_type_floorarea = floorarea_p[dw_type_name] * floorarea_by            # Floor area of existing buildlings

        # Distribute according to age
        for dwtype_age_id in dwtype_age_distr_by:
            age_class_p = dwtype_age_distr_by[dwtype_age_id] / 100              # Percent of dw of age class

            # Floor area of dwelling_class_age
            dw_type_age_class_floorarea = dw_type_floorarea * age_class_p       # Distribute proportionally floor area
            control_floorarea += dw_type_age_class_floorarea

            # Pop
            pop_dwtype_age_class = dw_type_age_class_floorarea / floorarea_pp_by # Floor area is divided by base area value
            control_pop += pop_dwtype_age_class

            #HDD = mf.get_hdd_individ_reg(reg_id, data)

            # create building object
            dw_stock_base.append(bf.Dwelling(curr_yr, reg_id, ['X', 'Y'], dw_type_id, float(dwtype_age_id), pop_dwtype_age_class, dw_type_age_class_floorarea, assumptions, data, data_ext))

            # TODO: IF Necessary calculate absolute number of buildings by dividng by the average floor size of a dwelling
            # Calculate number of dwellings

    #Testing
    np.testing.assert_array_almost_equal(tot_floorarea_cy, control_floorarea, decimal=3, err_msg="Error NR XXX")    # Test if floor area are the same
    np.testing.assert_array_almost_equal(pop_by, control_pop, decimal=3, err_msg="Error NR XXX")
    return dw_stock_base

def generate_dw_new(data, reg_id, curr_yr, dw_lu, floorarea_p_by, floorarea_pp_sy, dw_stock_new_dw, new_floorarea_sy, assumptions, data_ext):
    """Generate objects for all new dwellings

    All new dwellings are appended to the existing building stock of the region

    Parameters
    ----------
    uniqueID : uniqueID
        Unique dwellinge id

        ...

    Returns
    -------
    dw_stock_new_dw : list
        List with appended dwellings

    Notes
    -----
    The floor area id divided proprtionally depending on dwelling type
    Then the population is distributed
    builindg is creatd
    """
    control_pop, control_floorarea = 0, 0

    # Iterate dwelling types
    for dw in dw_lu:
        dw_type_id, dw_type_name = dw, dw_lu[dw]

        # Floor area
        dw_type_floorarea_new_build = floorarea_p_by[dw_type_name] * new_floorarea_sy      # Floor area of existing buildlings
        control_floorarea += dw_type_floorarea_new_build

        # Pop
        pop_dwtype_sim_year_new_build = dw_type_floorarea_new_build / floorarea_pp_sy             # Floor area is divided by floorarea_per_person
        control_pop += pop_dwtype_sim_year_new_build

        # create building object
        #Todo: Add climate??/internal heat data
        #HDD = mf.get_hdd_individ_reg(reg_id, data)

        dw_stock_new_dw.append(bf.Dwelling(curr_yr, reg_id, ['X', 'Y'], dw_type_id, curr_yr, pop_dwtype_sim_year_new_build, dw_type_floorarea_new_build, assumptions, data, data_ext))

    assert round(new_floorarea_sy, 3) == round(control_floorarea, 3)  # Test if floor area are the same
    assert round(new_floorarea_sy/floorarea_pp_sy, 3) == round(control_pop, 3)                    # Test if pop is the same

    return dw_stock_new_dw
