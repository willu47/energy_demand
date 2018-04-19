""" A ``WeatherRegion`` object is is generated per
weather station and regional load profile and technology
stocks are assigned."""
import uuid
import logging
import numpy as np
from energy_demand.technologies import technological_stock
from energy_demand.profiles import load_profile
from energy_demand.profiles import hdd_cdd
from energy_demand.technologies import diffusion_technologies
from energy_demand.basic import basic_functions
from energy_demand import enduse_func
from energy_demand.initalisations import helpers
from energy_demand.profiles import generic_shapes

class WeatherRegion(object):
    """WeaterRegion

    Arguments
    ----------
    name : str
        Unique identifyer of weather region
    base_yr : int
        Base year
    curr_yr : int
        Current year
    assumptions : dict
        Assumptions
    fueltypes : dict
        fueltypes
    all_enduse : list
        All enduses
    temp_by, temp_ey : array
        Temperature data
    tech_lp : dict
        Technology load profiles
    sectors : list
        Sectors

    Note
    ----
    - For each region, a technology stock is defined
    - regional specific fuel shapes are assigned to technologies
    """
    def __init__(
            self,
            name,
            base_yr,
            curr_yr,
            strategy_variables,
            t_bases,
            t_diff_param,
            tech_lists,
            technologies,
            assumptions,
            fueltypes,
            model_yeardays_nrs,
            model_yeardays,
            yeardays_month_days,
            all_enduses,
            temp_by,
            tech_lp,
            sectors,
        ):
        """Constructor of weather region
        """
        self.name = name

        # -----------------------------------
        # Calculate current year temperatures
        # -----------------------------------
        temp_cy = change_temp_climate(
            temp_by,
            yeardays_month_days,
            strategy_variables,
            base_yr,
            curr_yr)

        # Change base temperatures depending on change in t_base
        rs_t_base_heating_cy = hdd_cdd.sigm_temp(
            strategy_variables['rs_t_base_heating_future_yr']['scenario_value'],
            t_bases.rs_t_heating_by,
            base_yr,
            curr_yr,
            t_diff_param)
        '''rs_t_base_cooling_cy = hdd_cdd.sigm_temp(
            strategy_variables['rs_t_base_cooling_future_yr']['scenario_value'],
            t_bases.rs_t_cooling_by, base_yr, curr_yr,
            t_diff_param)'''

        ss_t_base_heating_cy = hdd_cdd.sigm_temp(
            strategy_variables['ss_t_base_heating_future_yr']['scenario_value'],
            t_bases.ss_t_heating_by,
            base_yr,
            curr_yr,
            t_diff_param)
        ss_t_base_cooling_cy = hdd_cdd.sigm_temp(
            strategy_variables['ss_t_base_cooling_future_yr']['scenario_value'],
            t_bases.ss_t_cooling_by,
            base_yr,
            curr_yr,
            t_diff_param)

        is_t_base_heating_cy = hdd_cdd.sigm_temp(
            strategy_variables['is_t_base_heating_future_yr']['scenario_value'],
            t_bases.is_t_heating_by,
            base_yr,
            curr_yr,
            t_diff_param)
        '''is_t_base_cooling_cy = hdd_cdd.sigm_temp(
            strategy_variables['is_t_base_cooling_future_yr']['scenario_value'],
            t_bases.is_t_cooling_by,
            base_yr,
            curr_yr,
            t_diff_param)'''

        # ==================================================================
        # Technology stocks
        # ==================================================================
        self.rs_tech_stock = technological_stock.TechStock(
            'rs_tech_stock',
            technologies,
            assumptions.enduse_overall_change['other_enduse_mode_info'],
            base_yr,
            curr_yr,
            fueltypes,
            temp_by,
            temp_cy,
            t_bases.rs_t_heating_by,
            all_enduses['rs_enduses'],
            rs_t_base_heating_cy,
            assumptions.rs_specified_tech_enduse_by)

        self.ss_tech_stock = technological_stock.TechStock(
            'ss_tech_stock',
            technologies,
            assumptions.enduse_overall_change['other_enduse_mode_info'],
            base_yr,
            curr_yr,
            fueltypes,
            temp_by,
            temp_cy,
            t_bases.ss_t_heating_by,
            all_enduses['ss_enduses'],
            ss_t_base_heating_cy,
            assumptions.ss_specified_tech_enduse_by)

        self.is_tech_stock = technological_stock.TechStock(
            'is_tech_stock',
            technologies,
            assumptions.enduse_overall_change['other_enduse_mode_info'],
            base_yr,
            curr_yr,
            fueltypes,
            temp_by,
            temp_cy,
            t_bases.is_t_heating_by,
            all_enduses['is_enduses'],
            ss_t_base_heating_cy,
            assumptions.is_specified_tech_enduse_by)


        # ==================================================================
        # Load profiles
        # ==================================================================

        # Flat load profiles
        flat_shape_yd, flat_shape_yh = generic_shapes.flat_shape(
            assumptions.model_yeardays_nrs)
    
        # ==================================================================
        # Residential submodel load profiles
        # ==================================================================
        self.rs_load_profiles = load_profile.LoadProfileStock("rs_load_profiles")

        # --------Calculate HDD/CDD
        self.rs_hdd_by, _ = hdd_cdd.calc_reg_hdd(
            temp_by, t_bases.rs_t_heating_by, model_yeardays)
        self.rs_hdd_cy, rs_fuel_shape_heating_yd = hdd_cdd.calc_reg_hdd(
            temp_cy, rs_t_base_heating_cy, model_yeardays)
        #self.rs_cdd_by, _ = hdd_cdd.calc_reg_cdd(
        #    temp_by, t_bases.rs_t_cooling_by, model_yeardays)
        #self.rs_cdd_cy, rs_fuel_shape_cooling_yd = hdd_cdd.calc_reg_cdd(
        #    temp_cy, rs_t_base_cooling_cy, model_yeardays)

        # -------Calculate climate change correction factors
        try:
            self.f_heat_rs_y = np.nan_to_num(
                1.0 / float(np.sum(self.rs_hdd_by))) * np.sum(self.rs_hdd_cy)
            #self.f_cooling_rs_y = np.nan_to_num(
            #    1.0 / float(np.sum(self.rs_cdd_by))) * np.sum(self.rs_cdd_cy)
            self.f_cooling_rs_y = 1
        except ZeroDivisionError:
            self.f_heat_rs_y = 1
            self.f_cooling_rs_y = 1

        # Calculate rs peak day
        rs_peak_day = enduse_func.get_peak_day(self.rs_hdd_cy)

        logging.info(
            "Regional specific peak day (rs_peak_day): %s", rs_peak_day)


        # ========
        # Enduse specific profiles
        # ========
        # -- Apply enduse sepcific shapes for enduses with not technologies with own defined shapes
        for enduse in all_enduses['rs_enduses']:

            # Enduses where technology specific load profiles are defined for yh
            if enduse == 'rs_space_heating':
                pass
            else:
                tech_list = helpers.get_nested_dict_key(assumptions.rs_fuel_tech_p_by[enduse])

                shape_y_dh = insert_peak_dh_shape(
                    peak_day=rs_peak_day,
                    shape_y_dh=tech_lp['rs_shapes_dh'][enduse]['shape_non_peak_y_dh'],
                    shape_peak_dh=tech_lp['rs_shapes_dh'][enduse]['shape_peak_dh'])

                shape_yh = load_profile.calc_yh(
                    tech_lp['rs_shapes_yd'][enduse]['shape_non_peak_yd'],
                    tech_lp['rs_shapes_dh'][enduse]['shape_non_peak_y_dh'],
                    model_yeardays)

                self.rs_load_profiles.add_lp(
                    unique_identifier=uuid.uuid4(),
                    technologies=tech_list,
                    enduses=[enduse],
                    shape_yd=shape_y_dh,
                    shape_yh=shape_yh)

        # ==========
        # Technology specific profiles for residential heating
        # ===========

        # ------Heating boiler
        rs_profile_boilers_yh = load_profile.calc_yh(
            rs_fuel_shape_heating_yd, tech_lp['rs_profile_boilers_y_dh'], model_yeardays)

        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['heating_const'],
            enduses=['rs_space_heating'],
            shape_yd=rs_fuel_shape_heating_yd,
            shape_yh=rs_profile_boilers_yh)

        # ------Heating CHP
        rs_profile_chp_y_dh = insert_peak_dh_shape(
            peak_day=rs_peak_day,
            shape_y_dh=tech_lp['rs_profile_chp_y_dh'],
            shape_peak_dh=tech_lp['rs_lp_heating_CHP_dh']['peakday'])

        rs_profile_chp_yh = load_profile.calc_yh(
            rs_fuel_shape_heating_yd, rs_profile_chp_y_dh, model_yeardays)

        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['tech_CHP'],
            enduses=['rs_space_heating'],
            shape_yd=rs_fuel_shape_heating_yd,
            shape_yh=rs_profile_chp_yh)

        # ------Electric heating, storage heating (primary)
        rs_profile_storage_heater_yh = load_profile.calc_yh(
            rs_fuel_shape_heating_yd, tech_lp['rs_profile_storage_heater_y_dh'], model_yeardays)
        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['storage_heating_electricity'],
            enduses=['rs_space_heating'],
            shape_yd=rs_fuel_shape_heating_yd,
            shape_yh=rs_profile_storage_heater_yh)

        # ------Electric heating secondary (direct elec heating)
        rs_profile_elec_heater_y_dh = insert_peak_dh_shape(
            peak_day=rs_peak_day,
            shape_y_dh=tech_lp['rs_profile_elec_heater_y_dh'],
            shape_peak_dh=tech_lp['rs_lp_second_heating_dh']['peakday'])
        rs_profile_elec_heater_yh = load_profile.calc_yh(
            rs_fuel_shape_heating_yd, rs_profile_elec_heater_y_dh, model_yeardays)

        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['secondary_heating_electricity'],
            enduses=['rs_space_heating'],
            shape_yd=tech_lp['rs_profile_elec_heater_y_dh'],
            shape_yh=rs_profile_elec_heater_yh)

        # ------Heat pump heating
        rs_profile_hp_y_dh = insert_peak_dh_shape(
            peak_day=rs_peak_day,
            shape_y_dh=tech_lp['rs_profile_hp_y_dh'],
            shape_peak_dh=tech_lp['rs_lp_heating_hp_dh']['peakday'])

        rs_fuel_shape_hp_yh = get_fuel_shape_heating_hp_yh(
            rs_profile_hp_y_dh,
            self.rs_tech_stock,
            self.rs_hdd_cy,
            model_yeardays)

        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['heating_non_const'],
            enduses=['rs_space_heating'],
            shape_yd=rs_fuel_shape_heating_yd,
            shape_yh=rs_fuel_shape_hp_yh)

        # ------District_heating_electricity. Assumption made that same curve as CHP
        rs_profile_chp_y_dh = load_profile.calc_yh(
            rs_fuel_shape_heating_yd, tech_lp['rs_profile_chp_y_dh'], model_yeardays)

        self.rs_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['tech_district_heating'],
            enduses=['rs_space_heating'],
            shape_yd=rs_fuel_shape_heating_yd,
            shape_yh=rs_profile_chp_y_dh)

        # ==================================================================
        # Service Submodel load profiles
        # ==================================================================
        self.ss_load_profiles = load_profile.LoadProfileStock("ss_load_profiles")

        # --------HDD/CDD
        ss_hdd_by, _ = hdd_cdd.calc_reg_hdd(
            temp_by, t_bases.ss_t_heating_by, model_yeardays)
        ss_hdd_cy, ss_fuel_shape_heating_yd = hdd_cdd.calc_reg_hdd(
            temp_cy, ss_t_base_heating_cy, model_yeardays)

        ss_cdd_by, _ = hdd_cdd.calc_reg_cdd(
            temp_by, t_bases.ss_t_cooling_by, model_yeardays)
        ss_cdd_cy, ss_lp_cooling_yd = hdd_cdd.calc_reg_cdd(
            temp_cy, ss_t_base_cooling_cy, model_yeardays)

        try:
            self.f_heat_ss_y = np.nan_to_num(
                1.0 / float(np.sum(ss_hdd_by))) * np.sum(ss_hdd_cy)
            self.f_cooling_ss_y = np.nan_to_num(
                1.0 / float(np.sum(ss_cdd_by))) * np.sum(ss_cdd_cy)
        except ZeroDivisionError:
            self.f_heat_ss_y = 1
            self.f_cooling_ss_y = 1

        # ========
        # Enduse specific profiles
        # ========
        # - Assign to each enduse the carbon fuel trust dataset
        for enduse in all_enduses['ss_enduses']:

            # Skip temperature dependent end uses (regional) because load profile in regional load profile stock
            if enduse in assumptions.enduse_space_heating or enduse in assumptions.ss_enduse_space_cooling:
                pass
            else:
                for sector in sectors['ss_sectors']:

                    # Get technologies with assigned fuel shares
                    tech_list = helpers.get_nested_dict_key(
                        assumptions.ss_fuel_tech_p_by[enduse][sector])

                    # Apply correction factor for weekend_effect
                    shape_non_peak_yd = tech_lp['ss_shapes_yd'][enduse][sector]['shape_non_peak_yd'] * assumptions.ss_weekend_f
                    shape_non_peak_yd_weighted = load_profile.abs_to_rel(shape_non_peak_yd)

                    shape_yh = load_profile.calc_yh(
                        shape_non_peak_yd_weighted,
                        tech_lp['ss_shapes_dh'][enduse][sector]['shape_non_peak_y_dh'],
                        model_yeardays)

                    self.ss_load_profiles.add_lp(
                        unique_identifier=uuid.uuid4(),
                        technologies=tech_list,
                        enduses=[enduse],
                        shape_yd=shape_non_peak_yd_weighted,
                        shape_yh=shape_yh,
                        sectors=[sector])

        # Apply correction factor for weekend_effect for space heating
        ss_fuel_shape_heating_yd = ss_fuel_shape_heating_yd * assumptions.ss_weekend_f
        ss_fuel_shape_heating_yd_weighted = load_profile.abs_to_rel(ss_fuel_shape_heating_yd)

        # ========
        # Technology specific profiles
        # ========

        # Flatten list of all potential technologies
        ss_space_heating_tech_lists = list(tech_lists.values())
        all_techs_ss_space_heating = [item for sublist in ss_space_heating_tech_lists for item in sublist]

        # --
        # Heat pump (RESIDENTIAL HEAT PUMP PROFILE FOR SERVICE SECTOR)
        # --
        # Remove tech from all space heating techs
        all_techs_ss_space_heating = basic_functions.remove_element_from_list(
            all_techs_ss_space_heating, 'heat_pumps_electricity')

        ss_fuel_shape_hp_yh = get_fuel_shape_heating_hp_yh(
            rs_profile_hp_y_dh,
            self.rs_tech_stock,
            ss_hdd_cy,
            model_yeardays)

        self.ss_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=['heat_pumps_electricity'],
            enduses=['ss_space_heating'],
            sectors=sectors['ss_sectors'],
            shape_yd=ss_fuel_shape_heating_yd_weighted,
            shape_yh=ss_fuel_shape_hp_yh)

        # --------
        # secondary_heater_electricity
        # Info: The residential direct heating load profile is used
        # -------
        # Remove tech from all space heating techs
        all_techs_ss_space_heating = basic_functions.remove_element_from_list(
            all_techs_ss_space_heating, 'secondary_heater_electricity')

        ss_profile_elec_heater_yh = load_profile.calc_yh(
            ss_fuel_shape_heating_yd_weighted,
            rs_profile_elec_heater_y_dh,
            model_yeardays)

        # Get aggregated electricity load profile
        '''ss_fuel_shape_electricity, _ = ss_get_sector_enduse_shape(
            tech_lp['ss_all_tech_shapes_dh'],
            ss_fuel_shape_heating_yd_weighted,
            'ss_other_electricity',
            model_yeardays_nrs)'''

        self.ss_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['secondary_heating_electricity'],
            enduses=['ss_space_heating'],
            sectors=sectors['ss_sectors'],
            shape_yd=ss_fuel_shape_heating_yd_weighted,
            shape_yh=ss_profile_elec_heater_yh)
            # ELEC CURVE ss_fuel_shape_electricity # DIRECT HEATING ss_profile_elec_heater_yh

        # --
        # Heating technologies (all other)
        #
        # (the heating shape follows the gas shape of aggregated sectors)
        # meaning that for all technologies, the load profile is the same
        ss_fuel_shape_any_tech_non_electric, _ = ss_get_sector_enduse_shape(
            tech_lp['ss_all_tech_shapes_dh'],
            ss_fuel_shape_heating_yd_weighted,
            'ss_space_heating',
            model_yeardays_nrs)

        self.ss_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=all_techs_ss_space_heating,
            enduses=['ss_space_heating'],
            sectors=sectors['ss_sectors'],
            shape_yd=ss_fuel_shape_heating_yd_weighted,
            shape_yh=ss_fuel_shape_any_tech_non_electric) #flat_shape_yh,

        #------
        # Add cooling technologies for service sector
        #------
        coolings_techs = tech_lists['cooling_const']

        for cooling_enduse in assumptions.ss_enduse_space_cooling:
            for sector in sectors['ss_sectors']:

                # Apply correction factor for weekend_effect 'cdd_weekend_cfactors'
                ss_lp_cooling_yd = ss_lp_cooling_yd * assumptions.cdd_weekend_cfactors
                ss_lp_cooling_yd_weighted = load_profile.abs_to_rel(ss_lp_cooling_yd)

                ss_shape_yh = load_profile.calc_yh(
                    ss_lp_cooling_yd_weighted,
                    tech_lp['ss_profile_cooling_y_dh'],
                    model_yeardays)

                self.ss_load_profiles.add_lp(
                    unique_identifier=uuid.uuid4(),
                    technologies=coolings_techs,
                    enduses=[cooling_enduse],
                    sectors=[sector],
                    shape_yd=ss_lp_cooling_yd_weighted,
                    shape_yh=ss_shape_yh)

        # ==================================================================
        # Industry submodel load profiles
        # ==================================================================
        self.is_load_profiles = load_profile.LoadProfileStock("is_load_profiles")

        # --------HDD/CDD
        is_hdd_by, _ = hdd_cdd.calc_reg_hdd(
            temp_by, t_bases.is_t_heating_by, model_yeardays)
        #is_cdd_by, _ = hdd_cdd.calc_reg_cdd(
        #    temp_by, t_bases.is_t_cooling_by, model_yeardays)

        # Take same base temperature as for service sector
        is_hdd_cy, is_fuel_shape_heating_yd = hdd_cdd.calc_reg_hdd(
            temp_cy, is_t_base_heating_cy, model_yeardays)
        #is_cdd_cy, _ = hdd_cdd.calc_reg_cdd(
        #    temp_cy, ss_t_base_cooling_cy, model_yeardays)

        try:
            self.f_heat_is_y = np.nan_to_num(1.0 / float(np.sum(is_hdd_by))) * np.sum(is_hdd_cy)
            #self.f_cooling_is_y = np.nan_to_num(1.0 / float(np.sum(is_cdd_by))) * np.sum(is_cdd_cy)
            self.f_cooling_is_y = 1
        except ZeroDivisionError:
            self.f_heat_is_y = 1
            self.f_cooling_is_y = 1

        # ========
        # Technology specific profiles
        # ========


        # --Heating technologies

        # Flatten list of all potential heating technologies
        is_space_heating_tech_lists = list(tech_lists.values())
        all_techs_is_space_heating = [item for sublist in is_space_heating_tech_lists for item in sublist]

        # Apply correction factor for weekend_effect for space heating load profile
        is_fuel_shape_heating_yd = is_fuel_shape_heating_yd * assumptions.is_weekend_f
        is_fuel_shape_heating_yd_weighted = load_profile.abs_to_rel(is_fuel_shape_heating_yd)

        # - Direct electric heating
        # Remove tech from all space heating techs
        all_techs_is_space_heating = basic_functions.remove_element_from_list(
            all_techs_is_space_heating, 'secondary_heater_electricity')

        is_profile_elec_heater_yh = load_profile.calc_yh(
            is_fuel_shape_heating_yd_weighted,
            rs_profile_elec_heater_y_dh,
            model_yeardays)

        self.is_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=tech_lists['secondary_heating_electricity'],
            enduses=['is_space_heating'],
            sectors=sectors['is_sectors'],
            shape_yd=is_fuel_shape_heating_yd_weighted,
            shape_yh=is_profile_elec_heater_yh)

        # Use direct heating from residential sector
        '''is_fuel_shape_any_tech_non_electric, _ = ss_get_sector_enduse_shape(
            tech_lp['ss_all_tech_shapes_dh'],
            is_fuel_shape_heating_yd_weighted,
            'ss_space_heating',
            assumptions.model_yeardays_nrs)'''

        # Add flat load profiles for non-electric heating technologies
        self.is_load_profiles.add_lp(
            unique_identifier=uuid.uuid4(),
            technologies=all_techs_is_space_heating,
            enduses=['is_space_heating'],
            sectors=sectors['is_sectors'],
            shape_yd=is_fuel_shape_heating_yd_weighted,
            shape_yh=flat_shape_yh)

        # Apply correction factor for weekend_effect to flat load profile for industry
        flat_shape_yd = flat_shape_yd * assumptions.is_weekend_f
        flat_shape_yd_weighted = load_profile.abs_to_rel(flat_shape_yd)

        # ========
        # Enduse specific profiles
        # ========
        for enduse in all_enduses['is_enduses']:
            if enduse == "is_space_heating":
                pass # Do not create non regional stock because temp dependent
            else:
                for sector in sectors['is_sectors']:

                    tech_list = helpers.get_nested_dict_key(
                        assumptions.is_fuel_tech_p_by[enduse][sector])

                    self.is_load_profiles.add_lp(
                        unique_identifier=uuid.uuid4(),
                        technologies=tech_list,
                        enduses=[enduse],
                        shape_yd=flat_shape_yd_weighted,
                        shape_yh=flat_shape_yh,
                        sectors=[sector])

def get_shape_peak_yd_factor(demand_yd):
    """From yd shape calculate maximum relative yearly service demand
    which is provided in a day

    Arguments
    ----------
    demand_yd : shape
        Demand for energy service for every day in year

    Return
    ------
    max_factor_yd : float
        yd maximum factor

    Note
    -----
    If the shape is taken from heat and cooling demand the assumption is made that
    HDD and CDD are directly proportional to fuel usage
    """
    # Total yearly demand
    tot_demand_y = np.sum(demand_yd)

    # Maximum daily demand
    max_demand_d = np.max(demand_yd)

    max_factor_yd = max_demand_d / tot_demand_y

    return max_factor_yd

def get_fuel_shape_heating_hp_yh(tech_lp_y_dh, tech_stock, rs_hdd_cy, model_yeardays):
    """Convert daily shapes to houly based on load for heatpump

    This is for non-peak.

    Arguments
    ---------
    tech_lp_y_dh : dict
        Technology load profiles
    tech_stock : object
        Technology stock
    rs_hdd_cy : array
        Heating Degree Days (model_yeardays_nrs, 1)
    model_yeardays : array
        Modelled year days

    Returns
    -------
    shape_yh : array
        Yearly shape to calculate hourly load (total sum == 1)
    shape_y_dh : array
        Shape of fuel shape for every day in a year (total sum = nr_of_days)

    Note
    ----
    -  An average heat pump efficiency is calculated for the whole day
       depending on hourly temperatures.

    -  See XY in documentation for source of heat pumps
    """
    shape_yh_hp = np.zeros((365, 24), dtype=float)
    shape_y_dh = np.zeros((365, 24), dtype=float)

    tech_eff = tech_stock.get_tech_attr(
        'rs_space_heating',
        'heat_pumps_electricity',
        'eff_cy')

    # Convert daily service demand to fuel (fuel = Heat demand / efficiency)
    # As only the shape is of interest, the HDD
    # can be used as an indicator for fuel use (which correlates) directly
    hp_daily_fuel = rs_hdd_cy[:, np.newaxis] / tech_eff

    # Distribute daily according to fuel load curves of heat pumps
    shape_yh_hp = hp_daily_fuel * tech_lp_y_dh

    # Convert absolute hourly fuel demand to relative fuel demand within a year
    shape_yh = load_profile.abs_to_rel(shape_yh_hp)

    # Convert for every day the shape to absolute shape (tot sum for a full year == 365)
    _shape_y_dh_sum_rows = np.sum(shape_yh_hp, axis=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        shape_y_dh = shape_yh_hp / _shape_y_dh_sum_rows[:, np.newaxis]
    shape_y_dh[np.isnan(shape_y_dh)] = 0

    # Select only modelled days
    return shape_yh[[model_yeardays]]

def get_shape_cooling_yh(tech_shape, cooling_shape):
    """Convert daily shape to hourly

    Arguments
    ---------
    tech_shape : dict
        Technology shape
    cooling_shape : array
        Cooling profile

    Returns
    -------
    shape_yd_cooling_tech : array
        Shape of cooling devices

    Note
    ----
    The daily cooling demand (calculated with cdd) is distributed within the day
    fuel demand curve from:

    - **Residential**: Taken from *Denholm, P., Ong, S., & Booten, C. (2012).
        Using Utility Load Data to Estimate Demand for Space Cooling and
        Potential for Shiftable Loads, (May), 23.
        Retrieved from http://www.nrel.gov/docs/fy12osti/54509.pdf*

    - **Service**: *Knight, Dunn, Environments Carbon and Cooling in
        Uk Office Environments*
    """
    shape_yd_cooling_tech = tech_shape * cooling_shape[:, np.newaxis]

    return shape_yd_cooling_tech

def ss_get_sector_enduse_shape(tech_lps, heating_lp_yd, enduse, model_yeardays_nrs):
    """Read generic shape for all technologies in a service sector enduse

    Arguments
    ---------
    tech_lps : array
        Technology load profiles
    heating_lp_yd : array
        Daily (yd) service demand shape for heat (percentage of yearly
        heat demand for every day)
    enduse : str
        Enduse where technology is used
    model_yeardays_nrs : int
        Number of modelled yeardays

    Returns
    -------
    shape_boilers_yh : array
        Shape how yearly fuel can be distributed to hourly (yh) (total sum == 1)
    shape_boilers_y_dh : array
        Shape of distribution of fuel within every day of a year (total sum == nr_of_days)
    """
    shape_yh_generic_tech = np.zeros((model_yeardays_nrs, 24), dtype=float)

    if enduse not in tech_lps:
        pass
    else:
        shape_y_dh_generic_tech = tech_lps[enduse]['shape_non_peak_y_dh']
        shape_yh_generic_tech = heating_lp_yd[:, np.newaxis] * shape_y_dh_generic_tech

    return shape_yh_generic_tech, shape_y_dh_generic_tech

def change_temp_climate(
        temp_data,
        yeardays_month_days,
        strategy_variables,
        base_yr,
        curr_yr
    ):
    """Change temperature data for every year depending
    on simple climate change assumptions

    Arguments
    ---------
    temp_data : dict
        Data
    yeardays_month_days : dict
        Month containing all yeardays
    strategy_variables : dict
        Assumption on temperature change
    base_yr : int
        Base year
    curr_yr : int
        Current year

    Returns
    -------
    temp_climate_change : dict
        Adapted temperatures for all weather stations depending on climate change assumptions
    """
    temp_climate_change = np.zeros((365, 24), dtype=float)

    # Iterate every month
    for yearday_month, month_yeardays in yeardays_month_days.items():
        month_str = basic_functions.get_month_from_int(yearday_month + 1)
        param_name_month = "climate_change_temp_d__{}".format(month_str)

        # Calculate monthly change in temperature
        lin_diff_factor = diffusion_technologies.linear_diff(
            base_yr=base_yr,
            curr_yr=curr_yr,
            value_start=0,
            value_end=strategy_variables[param_name_month]['scenario_value'],
            yr_until_changed=strategy_variables['climate_change_temp_diff_yr_until_changed']['scenario_value'])

        temp_climate_change[month_yeardays] = temp_data[month_yeardays] + lin_diff_factor

    return temp_climate_change

def insert_peak_dh_shape(
        peak_day,
        shape_y_dh,
        shape_peak_dh
    ):
    """Insert peak specific load profile of a technology

    Arguments
    ---------
    peak_day : int
        Peak day nr
    shape_y_dh : array
        Shape of technology for every day (total sum = 365)
    tech_lp_tech : dict
        Technolgy specific load profiles for different day types

    Returns
    -------
    shape_y_dh_inserted : array
        Array where on peak day the peak shape is inserted
    """
    peak_day_tech_dh = shape_peak_dh

    shape_y_dh_inserted = np.copy(shape_y_dh)

    shape_y_dh_inserted[peak_day] = peak_day_tech_dh

    #assert np.sum(shape_y_dh_inserted) == 365
    return shape_y_dh_inserted
