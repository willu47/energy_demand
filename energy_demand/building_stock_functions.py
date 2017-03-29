""" Functions for building stock"""
# pylint: disable=I0011,C0321,C0301,C0103, C0325, R0902, R0913
import numpy as np
import energy_demand.main_functions as mf
class Dwelling(object):
    """Class of a single dwelling or of a aggregated group of dwelling

    For every dwelling, the scenario drivers are calculated for each residential end_use.

    Parameters
    ----------
    curr_y : int
        Current year of simulation
    coordinates : float
        coordinates
    dwtype : int
        Dwelling type id. Description can be found in `daytype_lu`
    house_id : int
        Unique ID of dwelling or dwelling group
    age : int
        Age of dwelling in years (year the building was built)
    pop : float
        Dwelling population
    floorarea : float
        Floor area of dwelling
    hlc : float
        Heat loss coefficient
    hdd : float
        Heating degree days
    assumptions : dict
        Modelling assumptions stored in dictionary
    """
    def __init__(self, curr_y, region_dw_is_in, coordinates, dwtype, age, pop, floorarea, assumptions, data, data_ext):
        """Returns a new dwelling object"""
        self.curr_y = curr_y
        self.coordinates = coordinates
        self.dwtype = dwtype
        self.age = age
        self.pop = pop
        self.floorarea = floorarea
        self.region_dw_is_in = region_dw_is_in

        self.hdd = get_hdd_based_on_int_temp(curr_y, assumptions, data, data_ext) #: Get internal temperature depending on assumptions of sim_yr
        self.hlc = get_hlc(dwtype, age) #: Calculate heat loss coefficient with age and dwelling type
        #self.HOUSEHOLDINCOME?
        #self.otherattribute

        # Scenario drivers for residential end demands
        self.heating = self.scenario_driver_heating()
        self.water_heating = self.scenario_driver_water_heating()
        self.cooking = self.scenario_driver_cooking()
        self.lighting = self.scenario_driver_lighting()
        self.cold = self.scenario_driver_cold()
        self.wet = self.scenario_driver_wet()
        self.consumer_electronics = self.scenario_driver_consumer_electronics()
        self.computing = self.scenario_driver_computing()

    def scenario_driver_heating(self):
        """calc scenario driver with population and floor area"""
        return self.floorarea * self.pop * self.hdd * self.hlc

    def scenario_driver_water_heating(self):
        """calc scenario driver with population and heat loss coefficient"""
        return self.pop

    def scenario_driver_cooking(self):
        """calc scenario driver with population and floor area"""
        return self.pop

    def scenario_driver_lighting(self):
        """calc scenario driver with population and floor area"""
        return self.floorarea * self.pop

    def scenario_driver_cold(self):
        """calc scenario driver with population and floor area"""
        return self.pop

    def scenario_driver_wet(self):
        """calc scenario driver with population and floor area"""
        return self.pop

    def scenario_driver_consumer_electronics(self):
        """calc scenario driver with population and floor area"""
        return self.pop

    def scenario_driver_computing(self):
        """calc scenario driver with population and floor area"""
        return self.pop

def get_hdd_based_on_int_temp(curr_y, assumptions, data, data_ext):
    """ Get internal temperature based on assumptions
    
    Based on year the t_temp is choosen
    
    """
    
    
    # Diffusion of internal temperature
    t_base_cy = mf.get_t_base(curr_y, assumptions, data_ext)

    # Regional hdd #CREATE DICT WHICH POINT IS IN WHICH REGION (e.g. do with closest)
    #temperature_region_relocated = mf.get_temp_region(self.region_dw_is_in)
    temperature_region_relocated = 'Midlands'

     # READ OUT TEMP: Recalcuulate heating degree days based on internal temperature change
    t_mean_reg_months = data['temp_mean'][temperature_region_relocated]

    hdd = mf.get_tot_y_hdd_reg(t_mean_reg_months, t_base_cy)

    
    return hdd


def get_hlc(dw_type, age):
    """Calculates the linearly derived hlc depending on age and dwelling type

    Parameters
    ----------
    dw_type : int
        Dwelling type
    age : int
        Age of dwelling

    Returns
    -------
    hls : Heat loss coefficient [W/m2 * K]

    Notes
    -----
    Source: Linear trends derived from Table 3.17 ECUK Tables
    https://www.gov.uk/government/collections/energy-consumption-in-the-uk
    """
    # Dict with linear fits for all different dwelling types { dw_type: [slope, constant]}
    linear_fits_hlc = {
        0: [-0.0223, 48.292],       # Detached
        1: [-0.0223, 48.251],       # Semi-Detached
        2: [-0.0223, 48.063],       # Terraced Average
        3: [-0.0223, 47.02],        # Flats
        4: [-0.0223, 48.261],       # Bungalow
        }

    # Get linearly fitted value
    hlc = linear_fits_hlc[dw_type][0] * age + linear_fits_hlc[dw_type][1]
    return hlc

class DwStockRegion(object):
    """Class of the building stock in a region"""

    def __init__(self, region_ID, dwellings):
        """Returns a new building stock region object.

        Parameters
        ----------
        region_ID : float
            Region ID of building stock
        dwellings : list
            List containing all dwelling objects

        """
        self.region_ID = region_ID
        self.dwellings = dwellings
        self.pop = self.get_tot_pop()

        # SUM: (but same name as in dwelling)Summed scenario drivers across all dwellings for every enduse
        self.heating = self.get_scenario_driver_enduse('heating')
        self.water_heating = self.get_scenario_driver_enduse('water_heating')
        self.cooking = self.get_scenario_driver_enduse('cooking')
        self.cold = self.get_scenario_driver_enduse('cold')
        self.wet = self.get_scenario_driver_enduse('wet')
        self.consumer_electronics = self.get_scenario_driver_enduse('consumer_electronics')
        self.computing = self.get_scenario_driver_enduse('computing')

    def get_scenario_driver_enduse(self, enduse):
        """Sum all scenario driver for space heating"""
        sum_driver = 0
        for dwelling in self.dwellings:
            sum_driver += getattr(dwelling, enduse)
        return sum_driver

    def get_tot_pop(self):
        """Get total population of all dwellings"""
        totpop = 0
        for dwelling in self.dwellings:
            totpop += dwelling.pop
        return round(totpop, 3)

def calc_floorarea_pp(reg_floorarea, reg_pop_by, glob_var, assump_final_diff_floorarea_pp):
    """ Calculates future floor area per person depending on
    assumptions on final change and base year data

    Parameters
    ----------
    reg_floorarea : dict
        Floor area base year for all region

    reg_pop_by : dict
        Population of base year for all region

    glob_var : dict
        Contains all global simulation variables

    assump_final_diff_floorarea_pp : float
        Assumption of change in floor area up to end of simulation

    Returns
    -------
    data_floorarea_pp : dict
        Contains all values for floor area per person for every year

    Linear change of floor area
    # todo: check with simulation period
    """

    # initialisation
    data_floorarea_pp = {}
    sim_period = range(glob_var['base_year'], glob_var['end_yr'] + 1, 1) #base year, current year, iteration step
    base_year = glob_var['base_year']

    # Iterate regions
    for reg_id in reg_pop_by:
        sim_yrs = {}
        floorarea_pp_by = reg_floorarea[reg_id] / reg_pop_by[reg_id] # Floor area per person of base year

        # Iterate simulation years
        for y in sim_period:
            curr_year = y - glob_var['base_year']

            if y == base_year:
                sim_yrs[y] = floorarea_pp_by # base year value
            else:
                # Change up to current year (linear)
                diff_cy = curr_year * (((1 + assump_final_diff_floorarea_pp) - 1) / (len(sim_period)-1)) # substract from sim_period 1 because of base year

                floor_ara_pp_sim_yr = floorarea_pp_by * (1 + diff_cy)                                  # Floor area of simulation year
                sim_yrs[y] = floor_ara_pp_sim_yr
        data_floorarea_pp[reg_id] = sim_yrs  # Values for every simulation year

    return data_floorarea_pp

def get_dwtype_dist(dwtype_distr_by, assump_dwtype_distr_ey, glob_var):
    """Calculates the yearly distribution of dw types
    based on assumption of distribution on end_yr

    Linear change over time

    # Todo: Check modelling interval (2050/2051)

    Parameters
    ----------
    base_dwtype_distr : dict
        Distribution of dwelling types base year

    assump_dwtype_distr_ey : dict
        Distribution of dwelling types end year

    glob_var : dict
        Contains all global simulation variables

    Returns
    -------
    dwtype_distr : dict
        Contains all dwelling type distribution for every year

    Example
    -------

    out = {year: {'dwtype': 0.3}}
    """
    dwtype_distr = {}
    sim_period = range(glob_var['base_year'], glob_var['end_yr'] + 1, 1) #base year, current year, iteration step

    # Iterate years
    for sim_yr in sim_period:
        sim_yr_nr = sim_yr - glob_var['base_year']

        if sim_yr == glob_var['base_year']:
            y_distr = dwtype_distr_by # If base year, base year distribution
        else:
            y_distr = {}

            for dtype in dwtype_distr_by:
                val_by = dwtype_distr_by[dtype] # base year value
                sim_y = assump_dwtype_distr_ey[dtype] # cur year value
                diff_val = sim_y - val_by # Total difference
                diff_y = diff_val / (len(sim_period)-1) # Linear difference per year
                y_distr[dtype] = val_by + (diff_y * sim_yr_nr) # Difference up to current year

        dwtype_distr[sim_yr] = y_distr

    # Test if distribution is 100%
    for y in dwtype_distr:
        np.testing.assert_almost_equal(sum(dwtype_distr[y].values()), 1.0, decimal=7, err_msg='The distribution of dwelling types went wrong', verbose=True)
    return dwtype_distr
