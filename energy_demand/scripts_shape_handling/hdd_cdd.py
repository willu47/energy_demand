"""Functions related to heating or cooling degree days
"""
import numpy as np
from energy_demand.scripts_geography import weather_station_location as weather_station
from energy_demand.scripts_technologies import diffusion_technologies

def calc_hdd(t_base, temp_yh):
    """Heating Degree Days for every day in a year

    Parameters
    ----------
    t_base : int
        Base temperature
    temp_yh : array
        Array containing daily temperatures for each day (shape 365, 24)

    Returns
    -------
    hdd_d : array
        An array containing the Heating Degree Days for every day (shape 365, 1)
    """
    hdd_d = np.zeros((365))

    for day, temp_day in enumerate(temp_yh):
        hdd = 0
        for temp_h in temp_day:
            diff = t_base - temp_h
            if diff > 0:
                hdd += diff
        if hdd > 0:
            hdd_d[day] = hdd/24.0
        else:
            hdd_d[day] = 0

    return hdd_d

def calc_cdd(rs_t_base_cooling, temperatures):
    """Calculate cooling degree days

    The Cooling Degree Days are calculated based on
    cooling degree hours with temperatures of a full year

    Parameters
    ----------
    rs_t_base_cooling : float
        Base temperature for cooling
    temperatures : array
        Temperatures for every hour in a year

    Return
    ------
    cdd_d : array
        Contains all CDD for every day in a year (365, 1)

    Info
    -----
    For more info see Formual 2.1: Degree-days: theory and application

    https://www.designingbuildings.co.uk/wiki/Cooling_degree_days
    """
    cdd_d = np.zeros((365))

    for day_nr, day in enumerate(temperatures):
        sum_d = 0
        for temp_h in day:
            diff_t = temp_h - rs_t_base_cooling
            if diff_t > 0: # Only if cooling is necessary
                sum_d += diff_t
        if sum_d > 0:
            cdd_d[day_nr] = sum_d/24
        else:
            cdd_d[day_nr] = 0

    return cdd_d

def get_hdd_country(regions, data, t_base_type):
    """Calculate total number of heating degree days in a region for the base year

    Parameters
    ----------
    regions : dict
        Dictionary containing regions
    data : dict
        Dictionary with data
    """
    hdd_regions = {}

    for region in regions:
        longitude = data['reg_coordinates'][region]['longitude']
        latitude = data['reg_coordinates'][region]['latitude']

        # Get closest weather station and temperatures
        closest_weatherstation_id = weather_station.get_closest_station(
            longitude,
            latitude,
            data['weather_stations']
            )

        # Temp data
        temperatures = data['temperature_data'][closest_weatherstation_id][data['base_yr']]

        # Base temperature for base year
        t_base_heating_cy = sigm_t_base(
            data['base_yr'],
            data['assumptions'],
            data['base_yr'],
            data['end_yr'],
            t_base_type
            )

        # Calc HDD
        hdd_reg = calc_hdd(t_base_heating_cy, temperatures)
        hdd_regions[region] = np.sum(hdd_reg) # get regional temp over year

    return hdd_regions

def sigm_t_base(curr_y, assumptions, base_yr, end_yr, t_base_type):
    """Calculate base temperature depending on sigmoid diff and location

    Depending on the base temperature in the base and end year
    a sigmoid diffusion from the base temperature from the base year
    to the end year is calculated

    This allows to model changes e.g. in thermal confort

    Parameters
    ----------
    curr_y : float
        Current Year
    assumptions : dict
        Dictionary with assumptions
    base_yr : float
        Base year
    end_yr : float
        Simulation End year

    Return
    ------
    t_base_cy : float
        Base temperature of current year
    """
    # Base temperature of end year minus base temp of base year
    t_base_diff = assumptions[t_base_type]['end_yr'] - assumptions[t_base_type]['base_yr']

    # Sigmoid diffusion
    t_base_frac = diffusion_technologies.sigmoid_diffusion(
        base_yr,
        curr_y,
        end_yr,
        assumptions['sig_midpoint'],
        assumptions['sig_steeppness']
        )

    # Temp diff until current year
    t_diff_cy = t_base_diff * t_base_frac

    # Add temp change to base year temp
    t_base_cy = t_diff_cy + assumptions[t_base_type]['base_yr']

    return t_base_cy
