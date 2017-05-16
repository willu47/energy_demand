"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103, C0325
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import energy_demand.technological_stock_functions as tf
import energy_demand.main_functions as mf
import energy_demand.technological_stock as ts
import copy
from datetime import date

class Region(object):
    """Region Class for the residential model

    The main class of the residential model. For every region, a Region object needs to be generated.

    A. In Region the shape of individ technologies get assigned to technology stock

    Parameters
    ----------
    reg_name : str
        Unique identifyer of region
    data : dict
        Dictionary containing data
    data_ext : dict
        Dictionary containing all data provided specifically for scenario run and from wrapper.abs
    """
    def __init__(self, reg_name, data, data_ext):
        """Constructor of Region Class
        """
        self.reg_name = reg_name
        self.longitude = data_ext['region_coordinates'][self.reg_name]['longitude']
        self.latitude = data_ext['region_coordinates'][self.reg_name]['latitude']
        self.enduses_fuel = data['fueldata_disagg'][reg_name]

        # Get closest weather station and temperatures
        _closest_weater_station_id = mf.search_cosest_weater_station(self.longitude, self.latitude, data['weather_stations'])

        # Weather data
        self.temp_by = data['temperature_data'][_closest_weater_station_id][data_ext['glob_var']['base_yr']]
        self.temp_cy = data['temperature_data'][_closest_weater_station_id][data_ext['glob_var']['curr_yr']]

        # Create region specific technological stock
        self.tech_stock = ts.ResidTechStock(data, data_ext, self.temp_cy, data_ext['glob_var']['curr_yr'])

        # Calculate HDD and CDD for calculating heating and cooling service demand
        self.hdd_by = self.get_reg_hdd(data, data_ext, self.temp_by, data_ext['glob_var']['base_yr'])
        self.hdd_cy = self.get_reg_hdd(data, data_ext, self.temp_cy, data_ext['glob_var']['curr_yr'])
        self.cdd_by = self.get_reg_cdd(data, data_ext, self.temp_by, data_ext['glob_var']['base_yr'])
        self.cdd_cy = self.get_reg_cdd(data, data_ext, self.temp_cy, data_ext['glob_var']['curr_yr'])

        # YD Factors (factor to calculate max daily demand from yearly demand)
        self.reg_peak_yd_heating_factor = self.get_shape_peak_yd_factor(self.hdd_cy)
        self.reg_peak_yd_cooling_factor = self.get_shape_peak_yd_factor(self.cdd_cy)

        # Climate change correction factors (Assumption: Demand for heat correlates directly with fuel)
        self.heating_factor_y = np.nan_to_num(np.divide(1, np.sum(self.hdd_by))) * np.sum(self.hdd_cy)
        self.cooling_factor_y = np.nan_to_num(np.divide(1, np.sum(self.cdd_by))) * np.sum(self.cdd_cy)

        # Heating and cooling yd shapes
        self.heating_shape_yd = np.nan_to_num(np.divide(1.0, np.sum(self.hdd_cy))) * self.hdd_cy
        self.cooling_shape_yd = np.nan_to_num(np.divide(1.0, np.sum(self.cdd_cy))) * self.cdd_cy

        # -- NON-PEAK: Shapes for different enduses, technologies and fueltypes
        self.fuel_shape_boilers_yh = self.shape_heating_boilers_yh(data, data_ext, self.heating_shape_yd) # Heating, boiler, non-peak
        self.fuel_shape_hp_yh = self.shape_heating_hp_yh(data, data_ext, self.tech_stock, self.hdd_cy) # Heating, heat pumps, non-peak
        self.fuel_shape_cooling_yh = self.shape_cooling_yh(data, self.cooling_shape_yd) # Cooling, linear tech (such as boilers)

        # -- PEAK

        # Assign shapes to technologies in technological stock for enduses with technologies
        self.tech_stock = self.assign_shapes_to_tech_stock(
            data['tech_lu'],
            data['assumptions']
            )

        # Set attributs of all enduses to the Region Class
        self.create_enduses(data['resid_enduses'], data, data_ext)

        # --------------------
        # -- summing functions
        # --------------------
        # Sum final 'yearly' fuels (summarised over all enduses)
        self.fuels_new = self.tot_all_enduses_y(data, 'enduse_fuel_yh') #self.enduse_fuel_yh

        #self.fuels_new_enduse_specific_y = self.enduse_specific_y(data, 'enduse_fuel_new_fuel')
        self.fuels_new_enduse_specific_h = self.enduse_specific_h(data)

        # Get peak energy demand for all enduses for every fueltype
        self.max_fuel_peak = self.max_fuel_fueltype_allenduses(data, 'enduse_fuel_peak_h')

        # ----
        # PEAK summaries
        # ----
        # Get 'peak demand day' (summarised over all enduses)
        ##self.fuels_peak_d = self.get_calc_enduse_fuel_peak_yd_factor(data)

        # Get 'peak demand h of peak calculations' (summarised over all enduse for each enduse)
        self.fuels_peak_h = self.get_calc_enduse_fuel_peak_h(data, 'enduse_fuel_peak_h')

        # Sum 'daily' demand in region (summarised over all enduses)
        self.fuels_tot_enduses_d = self.tot_all_enduses_d(data, 'enduse_fuel_yd')

        # Sum 'hourly' demand in region for all enduses but fueltype specific (summarised over all enduses)
        self.fuels_tot_enduses_h = self.tot_all_enduses_h(data, 'enduse_fuel_yh')

        # Calculate load factors from peak values
        ##self.reg_load_factor_d = self.load_factor_d(data)
        self.reg_load_factor_h = self.calc_load_factor_h(data, self.fuels_tot_enduses_h, self.fuels_peak_h) #Across all enduses

        # Calculate load factors from non peak values (Does not make sense!)
        ##self.reg_load_factor_d_non_peak = self.load_factor_d_non_peak(data)
        ##self.reg_load_factor_h_non_peak = self.load_factor_h_non_peak(data)

        # Testing
        #np.testing.assert_almost_equal(np.sum(self.fuels_tot_enduses_d), np.sum(self.fuels_tot_enduses_h), err_msg='The Regional disaggregation from d to h is false')

        #test_sum = 0
        #for enduse in self.fuels_new_enduse_specific_y:
        #    test_sum += np.sum(self.fuels_new_enduse_specific_y[enduse])
        #np.testing.assert_almost_equal(np.sum(self.fuels_new), test_sum, err_msg='Summing end use specifid fuels went wrong')

    def get_shape_peak_yd_factor(self, demand_yd):
        """Get percentage of yearly service demand which is provided in a day

        Assumption: HDD & CDD are directly proportional to fuel usage
        """
        total_demand_y = np.sum(demand_yd) # Total year
        max_demand_d = np.max(demand_yd) # Maximum day

        factor_yd = np.divide(1, total_demand_y) * max_demand_d # Factor
        #print("--")
        #print("total_demand_y : " + str(total_demand_y))
        #print("max_demand_d:    " + str(max_demand_d))
        #print("factor_yd:       " + str(max_demand_d))
        return factor_yd

    def assign_shapes_to_tech_stock(self, technologies, assumptions):
        """
        Assign shapes to technological stock for different heating technologies


        Daily shape & hourly shape

        # Assign peak shapes for technologies??
        """
        # Iterate all technologies and check if specific technology has a own shape
        for technology in technologies:

            # Heating boiler technologies
            if technology in assumptions['list_tech_heating_const']:
                self.tech_stock.set_tech_attribute(technology, 'shape_yd', self.heating_shape_yd) # Non peak
                self.tech_stock.set_tech_attribute(technology, 'shape_yh', self.fuel_shape_boilers_yh) # Non peak

            elif technology in assumptions['list_tech_cooling_const']:
                self.tech_stock.set_tech_attribute(technology, 'shape_yh', self.fuel_shape_boilers_yh) # Non peak

            elif technology in assumptions['list_tech_heating_temp_dep']: # Technologies with hourly efficiencies
                self.tech_stock.set_tech_attribute(technology, 'shape_yd', self.heating_shape_yd)
                self.tech_stock.set_tech_attribute(technology, 'shape_yh', self.fuel_shape_hp_yh)

        return self.tech_stock

    def create_enduses(self, enduses, data, data_ext):
        """All enduses are initialised and inserted as an attribute of the Region Class
        """
        # Iterate all enduses
        for enduse in enduses:

            # ---------------------------------------------
            # Enduse specific parameters #TODO: Add cooling
            # ---------------------------------------------
            if enduse in data['assumptions']['enduse_space_heating']: # ['space_heating']:
                enduse_peak_yd_factor = self.reg_peak_yd_heating_factor # Regional yd factor for heat
                #enduse_shape_peak_dh = None # Because peak is taken from technology of endus
            elif enduse in data['assumptions']['enduse_space_cooling']:
                enduse_peak_yd_factor = self.reg_peak_yd_cooling_factor
            else:
                # Get parameter from loaded shape
                enduse_peak_yd_factor = data['shapes_resid_yd'][enduse]['shape_peak_yd_factor']

                #enduse_shape_peak_dh = data['shapes_resid_dh'][self.enduse]['shape_peak_dh'] # dh


            # ---------------------------------------
            # Add residential enduse to region
            # ---------------------------------------
            Region.__setattr__(
                self,
                enduse, # Name of enduse
                EnduseResid(
                    self.reg_name,
                    data,
                    data_ext,
                    enduse,
                    self.enduses_fuel,
                    self.tech_stock,
                    self.heating_factor_y,
                    self.cooling_factor_y,
                    self.fuel_shape_hp_yh,
                    self.fuel_shape_boilers_yh,
                    enduse_peak_yd_factor  # yd factor which is different depending on enduse
                    #enduse_shape_peak_dh #Daily shape of peak day
                    )
                )
            
            # ---------------------------------------
            # Add service enduses to region
            # ---------------------------------------

    def tot_all_enduses_y(self, data, attribute_to_get):
        """Sum all fuel types over all end uses
        """
        #sum_fuels = np.zeros((len(data['fuel_type_lu']), 1)) # Initialise
        sum_fuels = 0

        for enduse in data['resid_enduses']:
            sum_fuels += np.sum(self.__getattr__subclass__(enduse, attribute_to_get))

        return sum_fuels

    def max_fuel_fueltype_allenduses(self, data, attribute_to_get):
        """Sum all fuel types over all end uses
        """
        sum_fuels = np.zeros((len(data['fuel_type_lu']), 1)) # Initialise

        for enduse in data['resid_enduses']:
            for fueltype in data['fuel_type_lu']:
                sum_fuels[fueltype] += self.__getattr__subclass__(enduse, attribute_to_get)[fueltype]

        return sum_fuels

    def get_fuels_enduse_requested(self, enduse):
        """ TEST: READ ENDSE SPECIFID FROM"""
        fuels = self.__getattr__subclass__(enduse, 'enduse_fuel_new_fuel')
        return fuels

    def enduse_specific_y(self, data, attribute_to_get):
        """Sum fuels for every fuel type for each enduse
        """
        sum_fuels_all_enduses = {}
        for enduse in data['resid_enduses']:
            sum_fuels_all_enduses[enduse] = np.zeros((len(data['fuel_type_lu']), 1))

        # Sum data
        for enduse in data['resid_enduses']:
            sum_fuels_all_enduses[enduse] += self.__getattr__subclass__(enduse, attribute_to_get) # Fuel of Enduse
        return sum_fuels_all_enduses

    def enduse_specific_h(self, data):
        """Sum fuels for every fuel type for each enduse
        """
        sum_fuels_all_enduses = {}
        for enduse in data['resid_enduses']:
            sum_fuels_all_enduses[enduse] = np.zeros((len(data['fuel_type_lu']), 365, 24))

        # Sum data
        for enduse in data['resid_enduses']:
            sum_fuels_all_enduses[enduse] += self.__getattr__subclass__(enduse, 'enduse_fuel_yh') # Fuel of Enduse h
        return sum_fuels_all_enduses


    def tot_all_enduses_d(self, data, attribute_to_get):
        """Calculate total daily fuel demand for each fueltype
        """
        sum_fuels_d = np.zeros((len(data['fuel_type_lu']), 365, 1))  # Initialise

        for fueltype in data['fuel_type_lu']:
            for enduse in data['resid_enduses']:
                sum_fuels_d[fueltype] += self.__getattr__subclass__(enduse, attribute_to_get)[fueltype]

        return sum_fuels_d

    def get_calc_enduse_fuel_peak_yd_factor(self, data):
        """Summarise absolute fuel of peak days over all end_uses
        """
        sum_calc_enduse_fuel_peak_yd_factor = np.zeros((len(data['fuel_type_lu']), 1))  # Initialise

        for enduse in data['resid_enduses']:
            sum_calc_enduse_fuel_peak_yd_factor += self.__getattr__subclass__(enduse, 'enduse_peak_yd_factor') # Fuel of Enduse

        return sum_calc_enduse_fuel_peak_yd_factor

    def get_calc_enduse_fuel_peak_h(self, data, attribute_to_get):
        """Summarise peak values of all enduses for every fueltype
        """
        sum_calc_enduse_fuel_peak_yh = np.zeros((len(data['fuel_type_lu']), 1)) # Initialise

        for fueltype in data['fuel_type_lu']:
            for enduse in data['resid_enduses']:
                sum_calc_enduse_fuel_peak_yh[fueltype] += self.__getattr__subclass__(enduse, attribute_to_get)[fueltype] # Fuel of Endus enduse_fuel_peak_dh

        return sum_calc_enduse_fuel_peak_yh

    def tot_all_enduses_h(self, data, attribute_to_get):
        """Calculate total hourly fuel demand for each fueltype
        """
        sum_fuels_h = np.zeros((len(data['fuel_type_lu']), 365, 24)) # Initialise

        for fueltype in data['fuel_type_lu']:
            for enduse in data['resid_enduses']:
                sum_fuels_h[fueltype] += self.__getattr__subclass__(enduse, attribute_to_get)[fueltype]

        # Read out more error information (e.g. RuntimeWarning)
        #np.seterr(all='raise') # If not round, problem....np.around(fuel_end_use_h,10)
        return sum_fuels_h

    def load_factor_d(self, data):
        """Calculate load factor of a day in a year from peak values

        self.fuels_peak_d     :   Fuels for peak day (fueltype, data)
        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data) for full year

        Return
        ------
        lf_d : array
            Array with load factor for every fuel type in %

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        lf_d = np.zeros((len(data['fuel_type_lu']), 1))

        # Get day with maximum demand (in percentage of year)
        peak_d_demand = self.fuels_peak_d

        # Iterate fueltypes to calculate load factors for each fueltype
        for k, fueldata in enumerate(self.fuels_tot_enduses_d):
            average_demand = np.sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days

            if average_demand != 0:
                lf_d[k] = average_demand / peak_d_demand[k] # Calculate load factor

        lf_d = lf_d * 100 # Convert load factor to %
        return lf_d

    def calc_load_factor_h(self, data, fuels_tot_enduses_h, fuels_peak_h):
        """Calculate load factor of a h in a year from peak data (peak hour compared to all hours in a year)

        self.fuels_peak_h     :   Fuels for peak day (fueltype, data)
        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

        Return
        ------
        load_factor_h : array
            Array with load factor for every fuel type [in %]

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        load_factor_h = np.zeros((len(data['fuel_type_lu']), 1))

        # Iterate fueltypes to calculate load factors for each fueltype
        for fueltype, fuels in enumerate(fuels_tot_enduses_h):

            # Maximum fuel of an hour of the peak day
            maximum_h_of_day = fuels_peak_h[fueltype][0]

            #Calculate average in full year
            average_demand_h = np.average(fuels)

            # If there is a maximum day hour
            if maximum_h_of_day != 0:
                load_factor_h[fueltype] = average_demand_h / maximum_h_of_day # Calculate load factor

        # Convert load factor to %
        load_factor_h *= 100

        return load_factor_h

    def load_factor_d_non_peak(self, data):
        """Calculate load factor of a day in a year from non-peak data

        self.fuels_peak_d     :   Fuels for peak day (fueltype, data)
        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

        Return
        ------
        lf_d : array
            Array with load factor for every fuel type in %

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        lf_d = np.zeros((len(data['fuel_type_lu']), 1))

        # Iterate fueltypes to calculate load factors for each fueltype
        for k, fueldata in enumerate(self.fuels_tot_enduses_d):

            average_demand = sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days
            max_demand_d = max(fueldata)

            if  max_demand_d != 0:
                lf_d[k] = average_demand / max_demand_d # Calculate load factor

        lf_d = lf_d * 100 # Convert load factor to %
        return lf_d

    def load_factor_h_non_peak(self, data):
        """Calculate load factor of a h in a year from non-peak data

        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

        Return
        ------
        load_factor_h : array
            Array with load factor for every fuel type [in %]

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        load_factor_h = np.zeros((len(data['fuel_type_lu']), 1)) # Initialise array to store fuel

        # Iterate fueltypes to calculate load factors for each fueltype
        for fueltype, fueldata in enumerate(self.fuels_tot_enduses_h):
 
            '''all_hours = []
            for day_hours in self.fuels_tot_enduses_h[fueltype]:
                for h in day_hours:
                    all_hours.append(h)
            maximum_h_of_day_in_year = max(all_hours)
            '''
            maximum_h_of_day_in_year = self.fuels_peak_h[fueltype]

            average_demand_h = np.sum(fueldata) / (365 * 24) # Averae load = yearly demand / nr of days

            # If there is a maximum day hour
            if maximum_h_of_day_in_year != 0:
                load_factor_h[fueltype] = average_demand_h / maximum_h_of_day_in_year # Calculate load factor

        # Convert load factor to %
        load_factor_h *= 100

        return load_factor_h

    def get_reg_hdd(self, data, data_ext, temperatures, year):
        """Calculate daily shape of heating demand based on calculating HDD for every day

        Based on temperatures of a year, the HDD are calculated for every
        day in a year. Based on the sum of all HDD of all days, the relative
        share of heat used for any day is calculated.

        The Heating Degree Days are calculated based on assumptions of
        the base temperature of the current year.

        Parameters
        ----------
        data : dict
            Base data dict
        data_ext : dict
            External data

        Return
        ------
        hdd_d : array
            Heating degree days for every day in a year (365, 1)

        Info
        -----
        The shape_yd can be calcuated as follows: 1/ np.sum(hdd_d) * hdd_d

        The diffusion is assumed to be sigmoid
        """
        # Calculate base temperature for heating of current year
        t_base_heating_resid_cy = mf.t_base_sigm(year, data['assumptions'], data_ext['glob_var']['base_yr'], data_ext['glob_var']['end_yr'], 't_base_heating_resid')

        # Calculate hdd for every day (365,1)
        hdd_d = mf.calc_hdd(t_base_heating_resid_cy, temperatures)

        # Error testing
        #if np.sum(hdd_d) == 0:
        #    print("No heating degree days means no fuel for heating is necessary")
        #    import sys
        #    sys.exit()

        return hdd_d

    def get_reg_cdd(self, data, data_ext, temperatures, year):
        """Calculate daily shape of cooling demand based on calculating CDD for every day

        Based on temperatures of a year, the CDD are calculated for every
        day in a year. Based on the sum of all CDD of all days, the relative
        share of heat used for any day is calculated.

        The Cooling Degree Days are calculated based on assumptions of
        the base temperature of the current year.

        Parameters
        ----------
        data : dict
            Base data dict
        data_ext : dict
            External data

        Return
        ------
        shape_yd : array
            Fraction of heat for every day. Array-shape: 365, 1

        Info
        -----
        #TODO: TEST
        """
        t_base_cooling_resid = mf.t_base_sigm(year, data['assumptions'], data_ext['glob_var']['base_yr'], data_ext['glob_var']['end_yr'], 't_base_cooling_resid')

        cdd_d = mf.calc_cdd(t_base_cooling_resid, temperatures)

        return cdd_d

    def shape_heating_hp_yh(self, data, data_ext, tech_stock, hdd_cy):
        """Convert daily shapes to houly based on robert sansom daily load for heatpump

        This is for non-peak.

        Parameters
        ---------
        data : dict
            data
        data_ext : dict
            External data
        tech_stock : object
            Technology stock
        hdd_cy : array
            ??


        Returns
        -------
        hp_shape : array
            Daily shape how yearly fuel can be distributed to hourly

        Info
        ----
        The daily heat demand is converted to daily fuel depending on efficiency of heatpumps (assume if 100% heat pumps).
        In a final step the hourly fuel is converted to percentage of yearly fuel demand.

        Furthermore the assumption is made that the shape is the same for all fueltypes.

        The daily fuel demand curve for heat pumps taken from:
        Sansom, R. (2014). Decarbonising low grade heat for low carbon future. Dissertation, Imperial College London.
        """
        shape_y_hp = np.zeros((365, 24))

        list_dates = mf.fullyear_dates(start=date(data_ext['glob_var']['base_yr'], 1, 1), end=date(data_ext['glob_var']['base_yr'], 12, 31))

        for day, date_gasday in enumerate(list_dates):

            # See wether day is weekday or weekend
            weekday = date_gasday.timetuple().tm_wday

            # Take respectve daily fuel curve depending on weekday or weekend from Robert Sansom for heat pumps
            if weekday == 5 or weekday == 6:
                daily_fuel_profile = (data['shapes_resid_heating_heat_pump_dh'][2] / np.sum(data['shapes_resid_heating_heat_pump_dh'][2])) # WkendHourly gas shape. Robert Sansom hp curve
            else:
                daily_fuel_profile = (data['shapes_resid_heating_heat_pump_dh'][1] / np.sum(data['shapes_resid_heating_heat_pump_dh'][1])) # Wkday Hourly gas shape. Robert Sansom hp curve

            # Calculate weighted average daily efficiency of heat pump
            average_eff_d = 0
            for hour, heat_share_h in enumerate(daily_fuel_profile):
                tech_object = getattr(tech_stock, 'heat_pump') #TODO: WHAT IF DIFFERENT HEAT PUMPS?
                average_eff_d += heat_share_h * getattr(tech_object, 'eff_cy')[day][hour] # Hourly heat demand * heat pump efficiency

            # Convert daily service demand to fuel
            hp_daily_fuel = hdd_cy[day] / average_eff_d # Heat demand / efficiency = fuel

            # Distribute fuel of day according to fuel load curve by Robert Sansom
            shape_y_hp[day] = hp_daily_fuel * daily_fuel_profile

        # Convert absolute hourly fuel demand to relative fuel demand within a year
        hp_shape = np.divide(1, np.sum(shape_y_hp)) * shape_y_hp

        return hp_shape

    def shape_cooling_yh(self, data, cooling_shape):
        """Convert daily shape to hourly based on robert sansom daily load for boilers

        This is for non-peak.

        Every the day same

        Taken from Denholm, P., Ong, S., & Booten, C. (2012). Using Utility Load Data to 
        Estimate Demand for Space Cooling and Potential for Shiftable Loads, 
        (May), 23. Retrieved from http://www.nrel.gov/docs/fy12osti/54509.pdf

        Parameters
        ---------
        data : dict
            data
        data_ext : dict
            External data

        Returns
        -------
         : array


        Info
        ----
        Furthermore the assumption is made that the shape is the same for all fueltypes.

        The daily heat demand (calculated with hdd) is distributed within the day
        fuel demand curve for boilers from:

        """
        shape_yd_boilers = np.zeros((365, 24))

        for day in range(365):

            # Shape of cooling * daily cooling demand
            shape_yd_boilers[day] = data['shapes_resid_cooling_dh'] * cooling_shape[day]

        return shape_yd_boilers


    def shape_heating_boilers_yh(self, data, data_ext, heating_shape):
        """Convert daily shape to hourly based on robert sansom daily load for boilers

        This is for non-peak.

        Parameters
        ---------
        data : dict
            data
        data_ext : dict
            External data
        heating_shape : array
            Daily service demand shape for heat (percentage of yearly heat demand for every day)

        Returns
        -------
        shape_yd_boilers : array
            Daily shape how yearly fuel can be distributed to hourly

        Info
        ----
        The assumption is made that boilers have constant efficiency for every hour in a year.
        Therefore the fuel demand correlates directly with the heat service demand.

        Furthermore the assumption is made that the shape is the same for all fueltypes.

        The daily heat demand (calculated with hdd) is distributed within the day
        fuel demand curve for boilers from:

        Sansom, R. (2014). Decarbonising low grade heat for low carbon future. Dissertation, Imperial College London.
        """
        shape_yd_boilers = np.zeros((365, 24))

        list_dates = mf.fullyear_dates(start=date(data_ext['glob_var']['base_yr'], 1, 1), end=date(data_ext['glob_var']['base_yr'], 12, 31))

        for day, date_gasday in enumerate(list_dates):

            # See wether day is weekday or weekend
            weekday = date_gasday.timetuple().tm_wday

            # Take respectve daily fuel curve depending on weekday or weekend
            if weekday == 5 or weekday == 6:

                # Wkend Hourly gas shape. Robert Sansom boiler curve
                shape_yd_boilers[day] = heating_shape[day] * (data['shapes_resid_heating_boilers'][2] / np.sum(data['shapes_resid_heating_boilers'][2]))
            else:
                # Wkday Hourly gas shape. Robert Sansom boiler curve
                shape_yd_boilers[day] = heating_shape[day] * (data['shapes_resid_heating_boilers'][1] / np.sum(data['shapes_resid_heating_boilers'][1]))

        # Testing
        #assert np.sum(shape_yd_boilers) == 1, "Error in shape_heating_boilers_yh: The sum of hourly shape is not 1: {}".format(np.sum(shape_yd_boilers))
        np.testing.assert_almost_equal(np.sum(shape_yd_boilers), 1, err_msg=  "Error in shape_heating_boilers_yh: The sum of hourly shape is not 1: {}".format(np.sum(shape_yd_boilers)))
        return shape_yd_boilers

    def __getattr__(self, attr): #TODO: Maybe can be removed
        """Get method of own object
        """
        return self.attr

    def __getattr__subclass__(self, attr_main_class, attr_sub_class):
        """Get the attribute of a subclass"""
        object_class = getattr(self, attr_main_class)
        object_subclass = getattr(object_class, attr_sub_class)
        return object_subclass

    def plot_stacked_regional_end_use(self, nr_of_day_to_plot, fueltype, yearday, reg_name):
        """Plots stacked end_use for a region

        #TODO: Make that end_uses can be sorted, improve legend...

        0: 0-1
        1: 1-2
        2:

        #TODO: For nice plot make that 24 --> shift averaged 30 into middle of bins.
        """

        fig, ax = plt.subplots() #fig is needed
        nr_hours_to_plot = nr_of_day_to_plot * 24 #WHY 2?

        day_start_plot = yearday
        day_end_plot = (yearday + nr_of_day_to_plot)

        x = range(nr_hours_to_plot)

        legend_entries = []

        # Initialise (number of enduses, number of hours to plot)
        Y_init = np.zeros((len(self.enduses_fuel), nr_hours_to_plot))

        # Iterate enduse
        for k, enduse in enumerate(self.enduses_fuel):
            legend_entries.append(enduse)
            sum_fuels_h = self.__getattr__subclass__(enduse, 'enduses_fuel_h') #np.around(fuel_end_use_h,10)

            #fueldata_enduse = np.zeros((nr_hours_to_plot, ))
            list_all_h = []

            #Get data of a fueltype
            for _, fuel_data in enumerate(sum_fuels_h[fueltype][day_start_plot:day_end_plot]):

                for h in fuel_data:
                    list_all_h.append(h)

            Y_init[k] = list_all_h

        #color_list = ["green", "red", "#6E5160"]

        sp = ax.stackplot(x, Y_init)
        proxy = [mpl.patches.Rectangle((0, 0), 0, 0, facecolor=pol.get_facecolor()[0]) for pol in sp]

        ax.legend(proxy, legend_entries)

        #ticks x axis
        ticks_x = range(24)
        plt.xticks(ticks_x)

        #plt.xticks(range(3), ['A', 'Big', 'Cat'], color='red')
        plt.axis('tight')

        plt.xlabel("Hours")
        plt.ylabel("Energy demand in GWh")
        plt.title("Stacked energy demand for region{}".format(reg_name))

        #from matplotlib.patches import Rectangle
        #legend_boxes = []
        #for i in color_list:
        #    box = Rectangle((0, 0), 1, 1, fc=i)
        #    legend_boxes.append(box)
        #ax.legend(legend_boxes, legend_entries)

        #ax.stackplot(x, Y_init)
        plt.show()


def plot_stacked_regional_end_use(self, nr_of_day_to_plot, fueltype, yearday, reg_name):
    """Plots stacked end_use for a region

    #TODO: Make that end_uses can be sorted, improve legend...

    0: 0-1
    1: 1-2
    2:

    #TODO: For nice plot make that 24 --> shift averaged 30 into middle of bins.
    """

    fig, ax = plt.subplots() #fig is needed
    nr_hours_to_plot = nr_of_day_to_plot * 24 #WHY 2?

    day_start_plot = yearday
    day_end_plot = (yearday + nr_of_day_to_plot)

    x = range(nr_hours_to_plot)

    legend_entries = []

    # Initialise (number of enduses, number of hours to plot)
    Y_init = np.zeros((len(self.enduse_fuel), nr_hours_to_plot))

    # Iterate enduse
    for k, enduse in enumerate(self.enduse_fuel):
        legend_entries.append(enduse)
        sum_fuels_h = self.__getattr__subclass__(enduse, 'enduse_fuel_yh') #np.around(fuel_end_use_h,10)

        #fueldata_enduse = np.zeros((nr_hours_to_plot, ))
        list_all_h = []

        #Get data of a fueltype
        for _, fuel_data in enumerate(sum_fuels_h[fueltype][day_start_plot:day_end_plot]):

            for h in fuel_data:
                list_all_h.append(h)

        Y_init[k] = list_all_h

    #color_list = ["green", "red", "#6E5160"]

    sp = ax.stackplot(x, Y_init)
    proxy = [mpl.patches.Rectangle((0, 0), 0, 0, facecolor=pol.get_facecolor()[0]) for pol in sp]

    ax.legend(proxy, legend_entries)

    #ticks x axis
    ticks_x = range(24)
    plt.xticks(ticks_x)

    #plt.xticks(range(3), ['A', 'Big', 'Cat'], color='red')
    plt.axis('tight')

    plt.xlabel("Hours")
    plt.ylabel("Energy demand in GWh")
    plt.title("Stacked energy demand for region{}".format(reg_name))

    #from matplotlib.patches import Rectangle
    #legend_boxes = []
    #for i in color_list:
    #    box = Rectangle((0, 0), 1, 1, fc=i)
    #    legend_boxes.append(box)
    #ax.legend(legend_boxes, legend_entries)

    #ax.stackplot(x, Y_init)
    plt.show()

def residential_model_main_function(data, data_ext):
    """Main function of residential model

    This function is executed in the wrapper.

    Parameters
    ----------
    data : dict
        Contains all data not provided externally
    data_ext : dict
        All data provided externally

    Returns
    -------
    resid_object : object
        Object containing all regions as attributes for the residential model
    """
    fuel_in = test_function_fuel_sum(data) #SCRAP_ TEST FUEL SUM

    # Add all region instances as an attribute (region name) into the class `CountryResidentialModel`
    resid_object = CountryResidentialModel(data['lu_reg'], data, data_ext) #Add Coordinates

    print("READ OUT SPECIFIC ENDUSE FOR A REGION")
    #print(resid_object.get_specific_enduse_region('Wales', 'space_heating'))


    # ----------------------------
    # Attributes of whole country
    # ----------------------------
    fueltot = resid_object.tot_country_fuel # Total fuel of country
    country_enduses = resid_object.tot_country_fuel_enduse_specific_h # Total fuel of country for each enduse
    #TODO get tot_fuel_for_ever_enduse

    #TEST total fuel after run
    print("TEST MAIN START:" + str(fuel_in))
    print("Total Fuel after run: " + str(fueltot))
    print("DIFF: " + str(fueltot - fuel_in))

    return resid_object

class EnduseResid(object):
    """Class of an end use of the residential sector

    End use class for residential model. For every region, a different
    instance is generated.

    Parameters
    ----------
    reg_name : int
        The ID of the region. The actual region name is stored in `lu_reg`
    data : dict
        Dictionary containing data
    data_ext : dict
        Dictionary containing all data provided specifically for scenario run and from wrapper
    enduse : str
        Enduse given in a string
    enduse_fuel : array
        Fuel data for the region the endu

    enduse_peak_yd_factor : float
        Peak yd factor of enduse

    Info
    ----------
    Every enduse can only have on shape independently of the fueltype

    Problem: Not all enduses have technologies assigned. Therfore peaks are derived from techstock in case there are technologies,
    otherwise enduse load shapes are used.

    #TODO: The technology switch also needs to be done for peak!
    #TODO: (Check if always function below takes result from function above)
    """
    def __init__(self, reg_name, data, data_ext, enduse, enduse_fuel, tech_stock, heating_factor_y, cooling_factor_y, fuel_shape_hp_yh, fuel_shape_boilers_yh, enduse_peak_yd_factor): #, enduse_shape_peak_dh):
        self.reg_name = reg_name
        self.enduse = enduse
        self.technologies_enduse = self.get_technologies_in_enduse(data) # Get all technologies of enduse
        self.enduse_specific_fuel_switches_crit = self.get_enduse_fuel_switches(data) # Get fuel switches in enduse
        self.enduse_fuel = enduse_fuel[enduse] # Fuels for base year
        print("AA: " + str(tech_stock))
        # --------------------------
        # YEARLY FUELS
        # --------------------------
        # Fuels with applied changes (always overwritten in treatment train)
        self.enduse_fuel_new_fuel = copy.deepcopy(self.enduse_fuel)

        # Change fuel consumption based on climate change induced temperature differences
        self.temp_correction_hdd_cdd(cooling_factor_y, heating_factor_y)

        # Calcualte smart meter induced general savings
        self.smart_meter_eff_gain(data_ext, data['assumptions'])

        # Enduse specific consumption change in % (due e.g. to other efficiciency gains). No technology considered
        self.enduse_specific_change(data_ext, data['assumptions'])

        # Calculate new fuel demands after scenario drivers
        self.enduse_building_stock_driver(data, data_ext)

        # Calculate demand with changing elasticity (elasticity maybe on household level with floor area)
        self.enduse_elasticity(data_ext, data['assumptions'])

        #print("Fuel train A: " + str(self.enduse_fuel_new_fuel))

        # --------------------------
        # HOURLY FUELS
        # --------------------------

        # If enduse has technologies
        if self.technologies_enduse != []: # and self.enduse_specific_fuel_switches_crit:

            # Get corret service shape of enduse (for every enduse fuel switch need to define one)
            if self.enduse in data['assumptions']['enduse_space_heating']: #== 'space_heating':
                    service_y_h_shape = fuel_shape_boilers_yh # y_h_service_distribution in base year
            #elif self.enduse == 'cooling':
            #    service_y_h_shape =
            # else:

            # Calculate energy service for base year (NEEDS TO CALCULATE WITH BASE YEAR FUELS) TODO: CHECK
            service_fueltype_tech_after_switch = self.enduse_fuel_to_service(self.enduse_fuel_new_fuel, data_ext, data['assumptions'], tech_stock, service_y_h_shape)

            # If fuel switch is implemented
            if self.enduse_specific_fuel_switches_crit:
                self.enduse_switches_service_to_fuel(service_fueltype_tech_after_switch, tech_stock, self.enduse_fuel_new_fuel) # Convert service to fuel for current year (y) #Update self.enduse_fuel_new_fuel (ACTUALY NOT NECESSARY BECAUSE FUEL IS DONE BELOW)
                #print("Fuel train E: " + str(self.enduse_fuel_new_fuel))
                ###enduse_fuel_after_switch_p = self.enduse_switches_service_to_fuel_p(service_fueltype_tech_after_switch, tech_stock, self.enduse_fuel_new_fuel) # Convert service to fuel within each fueltype and assign percentage of fuel (e.g. 0.2 gastech1, 0.8 gastech2)
            else:
                # print("NO switches implemented")
                pass

            # Convert service to fuel for each technology
            enduse_fuel_after_switch_per_tech = self.enduse_service_to_fuel_per_tech(service_fueltype_tech_after_switch, tech_stock)

            # --------
            # NON-PEAK
            # --------
            # Iterate technologies in enduse and assign technology specific shape for respective fuels
            self.enduse_fuel_yd = self.calc_enduse_fuel_tech_yd(enduse_fuel_after_switch_per_tech, self.technologies_enduse, tech_stock)
            self.enduse_fuel_yh = self.calc_enduse_fuel_tech_yh(enduse_fuel_after_switch_per_tech, self.technologies_enduse, tech_stock)
            #self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh)# Get maximum hour demand per fueltype

            #print("2average:  +" + str(np.average(self.enduse_fuel_yh)))
            #print("2max:  +" + str(np.average(self.enduse_fuel_yh)))
            #print("2LOOOD:  " + str(np.average(self.enduse_fuel_yh) / np.max(self.enduse_fuel_yh)))

            # --------
            # PEAK
            # --------
            # Iterate technologies in enduse and assign technology specific shape for peak for respective fuels
            self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_tech_yh(enduse_fuel_after_switch_per_tech, self.technologies_enduse, tech_stock)
            self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh) # Get maximum hour demand per fueltype

        else: # No technologies specified in enduse
            print("TEST: " + str(self.enduse))

            # --Peak yd (peak day) (same for enduse for all technologies)
            self.enduse_fuel_peak_yd_factor = self.calc_enduse_fuel_peak_yd_factor(self.enduse_fuel, enduse_peak_yd_factor)

            # --------
            # NON-PEAK
            # --------
            self.enduse_fuel_yd = self.enduse_y_to_d(self.enduse_fuel_new_fuel, data['shapes_resid_yd'][self.enduse]['shape_non_peak_yd'])
            self.enduse_fuel_yh = self.enduse_d_to_h(self.enduse_fuel_yd, data['shapes_resid_dh'][self.enduse]['shape_non_peak_h']) #READ LOAD FROM THIS?

            # --------
            # PEAK
            # --------
            enduse_shape_peak_dh = data['shapes_resid_dh'][enduse]['shape_peak_dh']
            self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_yh(self.enduse_fuel_peak_yd_factor, enduse_shape_peak_dh)
            self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh) # Get maximum hour demand per fueltype

        # Testing
        np.testing.assert_almost_equal(np.sum(self.enduse_fuel_yd), np.sum(self.enduse_fuel_yh), decimal=5, err_msg='', verbose=True)

    def get_enduse_fuel_switches(self, data):
        """See wheter there is a fuelswitch for this enduse
        """
        fuel_switches_enduse = []

        for fuelswitch in data['assumptions']['resid_fuel_switches']:
            if fuelswitch['enduse'] == self.enduse:
                fuel_switches_enduse.append(fuelswitch)

        if fuel_switches_enduse != []:
            print("Fuel switches for this enduse: " + str(fuel_switches_enduse))
            return True
        else:
            return False

    def get_peak_from_yh(self, enduse_fuel_peak_yh):
        """Iterate yearly fuels and select day with most fuel
        """
        peak_fueltype_h = np.zeros((enduse_fuel_peak_yh.shape[0], 1))

        for fueltype, fuel_yh in enumerate(enduse_fuel_peak_yh):
            max_fuel_h = np.max(fuel_yh) # Get hour with maximum fuel_yh
            peak_fueltype_h[fueltype] = max_fuel_h # add

        return peak_fueltype_h

    def calc_enduse_fuel_peak_tech_yh(self, enduse_fuel_after_switch_per_tech, technologies_enduse, tech_stock):
        """Calculate peak demand. the daily peak is assumed to be the same in an enduse for all technologies

        From daily to hourly with hourly specific peak shape

        The peak is calculated for every fueltype (fueltype specfici)
        """
        enduse_fuel_peak_yh = np.zeros((self.enduse_fuel_new_fuel.shape[0], 365, 24)) #, 1 self.enduse_fuel_new_fuel.shape[0]

        for tech in technologies_enduse:
            fuel_tech = enduse_fuel_after_switch_per_tech[tech] # Get fuel of technology
            fuel_tech_peak_dh = fuel_tech * tech_stock.get_technology_attribute(tech, 'shape_peak_dh') # Multiply fuel with shape_peak_dh
            fueltype_tech = tech_stock.get_technology_attribute(tech, 'fuel_type') # Get fueltype of tech
            enduse_fuel_peak_yh[fueltype_tech] += fuel_tech_peak_dh # Add fuel of day

        return enduse_fuel_peak_yh

    def get_technologies_in_enduse(self, data):
        """Iterate assumptions about technologes in enduses of base year for each enduse
        """
        # Get all technologies of enduse
        technologies_enduse = []
        for fueltype in data['assumptions']['fuel_enduse_tech_p_by'][self.enduse]:
            for tech in data['assumptions']['fuel_enduse_tech_p_by'][self.enduse][fueltype]:
                technologies_enduse.append(tech)
        return technologies_enduse

    def calc_enduse_fuel_tech_yd(self, enduse_fuel_after_switch_per_tech, technologies_enduse, tech_stock):
        """ITerate fuels for each technology and assign shape d
        """
        fuels_fueltype_d = np.zeros((self.enduse_fuel_new_fuel.shape[0], 365, 1)) #, 1 self.enduse_fuel_new_fuel.shape[0]

        for tech in technologies_enduse:
            fuel_tech = enduse_fuel_after_switch_per_tech[tech] # Get fuel of technology
            fuel_tech_d = fuel_tech * tech_stock.get_technology_attribute(tech, 'shape_yd') # Multiply fuel with shape_h
            ####print("TEchnology: " + str(tech) + "   " + str(fuel_tech_d)) PINGU
            fueltype_tech = tech_stock.get_technology_attribute(tech, 'fuel_type') # Get fueltype of tech
            fuels_fueltype_d[fueltype_tech] += fuel_tech_d #np.sum(fuel_tech_d) # Add fuel of day

        # Assert --> If this assert is done, then we need to substract the fuel from yearly data and run function:  enduse_switches_service_to_fuel
        #np.testing.assert_array_almost_equal(np.sum(fuels_fueltype_d), np.sum(self.enduse_fuel_new_fuel), decimal=5, err_msg="Error: The y to h fuel did not work")

        return fuels_fueltype_d

    def calc_enduse_fuel_tech_yh(self, enduse_fuel_after_switch_per_tech, technologies_enduse, tech_stock):
        """ITerate fuels for each technology and assign shape h
        """
        fuels_fueltype_h = np.zeros((len(self.enduse_fuel_new_fuel), 365, 24))

        for tech in technologies_enduse:
            fuel_tech = enduse_fuel_after_switch_per_tech[tech] # Get fuel of technology
            fuel_tech_h = fuel_tech * tech_stock.get_technology_attribute(tech, 'shape_yh') # Multiply fuel with shape_h
            fueltype_tech = tech_stock.get_technology_attribute(tech, 'fuel_type') # Get fueltype of tech
            fuels_fueltype_h[fueltype_tech] += fuel_tech_h # Add fuel

        # Assert --> If this assert is done, then we need to substract the fuel from yearly data and run function:  enduse_switches_service_to_fuel
        #np.testing.assert_array_almost_equal(np.sum(fuels_fueltype_h), np.sum(self.enduse_fuel_new_fuel), decimal=5, err_msg="Error: The y to h fuel did not work")

        return fuels_fueltype_h

    def enduse_fuel_to_service(self, fuels, data_ext, assumptions, tech_stock, service_y_h_shape):
        """Convert fuels to services with efficiencies for base year

        SWITHCES OF SERVICE DEMAND CALCLATED BASED ON BASE YEAR

        1. Convert to service demand

        Switches according to diffusion but based on base year service demna --> servie is switched
        #TODO: fuel_shape_boilers_yh only for heating so far! fuel_shape_boilers_yh --> service_SHAPE_Y_H

        """
        print("techsss_")
        print(tech_stock)
        # Calculate total regional service demand (across all fueltypes) (base year)
        tot_service_h_by, service_fueltype_tech = mf.calc_regional_service_demand(
            service_y_h_shape,
            assumptions['fuel_enduse_tech_p_by'][self.enduse],
            fuels, #self.enduse_fuel_spec_change,
            tech_stock
        )

        # If no fuel switches
        if not self.enduse_specific_fuel_switches_crit:
            print("No fuel switches implemented for enduse: {}".format(self.enduse))
            return service_fueltype_tech
        else:
            # Make copy to calculate fuel percentages within fueltype after switch
            service_fueltype_tech_after_switch = copy.deepcopy(service_fueltype_tech)

            # Iterate all technologies which are installed in fuel switches
            for tech_installed in assumptions['installed_tech'][self.enduse]:
                tech_installed_fueltype = tech_stock.get_technology_attribute(tech_installed, 'fuel_type')

                # Read out sigmoid diffusion of energy service demand of this technology for the current year
                diffusion_cy = mf.sigmoid_function(data_ext['glob_var']['curr_yr'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['l_parameter'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['midpoint'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['steepness'])

                # Get service for current year based on diffusion
                service_tech_installed_cy = diffusion_cy * tot_service_h_by # Share of service demand & total service demand

                # Get service for current year for technologies
                service_fueltype_tech_after_switch[tech_installed_fueltype][tech_installed] += service_tech_installed_cy

                # ---------------------------------------------------------------------------------------------------
                # 3. Remove fuel of replaced energy service demand proportinally to heat demand in base year
                # ---------------------------------------------------------------------------------------------------
                tot_service_switched_tech_installed = 0 # Total replaced service across different fueltypes
                fueltypes_replaced = [] # List with fueltypes where fuel is replaced

                # Iterate fuelswitches and read out the shares of fuel which is switched with the installed technology
                for fuelswitch in assumptions['resid_fuel_switches']:
                    if fuelswitch['enduse'] == self.enduse and fuelswitch['technology_install'] == tech_installed:

                        # Store replaced fueltype
                        fueltypes_replaced.append(fuelswitch['enduse_fueltype_replace'])

                        # Share of service demand per fueltype * fraction of fuel switched
                        tot_service_switched_tech_installed += assumptions['service_fueltype_p'][self.enduse][fuelswitch['enduse_fueltype_replace']] * fuelswitch['share_fuel_consumption_switched']

                #print("Service demand which is switched with this technology: " + str(tot_service_switched_tech_installed))

                # Iterate all fueltypes which are affected in the technology installed
                for fueltype in fueltypes_replaced:

                    # Find fuel switch where this fueltype is replaced
                    for fuelswitch in assumptions['resid_fuel_switches']:
                        if fuelswitch['enduse'] == self.enduse and fuelswitch['technology_install'] == tech_installed and fuelswitch['enduse_fueltype_replace'] == fueltype:

                            # share of total service of fueltype * share of replaced fuel
                            relative_share = assumptions['service_fueltype_p'][self.enduse][fueltype] * fuelswitch['share_fuel_consumption_switched']

                            # Service reduced for this fueltype (service technology cy sigmoid diff *  % of heat demand within fueltype)
                            if tot_service_switched_tech_installed == 0:
                                reduction_service_fueltype = 0
                            else:
                                reduction_service_fueltype = service_tech_installed_cy * (np.divide(1.0, tot_service_switched_tech_installed) * relative_share)

                            print("--------dd--diffusion_cy " + str(diffusion_cy))

                            break # switch is found

                    # Get all technologies which are installed
                    technologies_in_fueltype = assumptions['fuel_enduse_tech_p_by'][self.enduse][fueltype].keys()

                    # Iterate all technologies in within the fueltype and calculate reduction per technology
                    for technology_replaced in technologies_in_fueltype:
                        #print("-------------heat demand within fueltype of technology: " + str(technology_replaced))

                        # Share of heat demand for technology in fueltype (share of heat demand within fueltype * reduction in servide demand)
                        service_demand_tech = assumptions['service_fueltype_tech_p'][self.enduse][fueltype][technology_replaced] * reduction_service_fueltype

                        # Substract technology specific servide demand
                        service_fueltype_tech_after_switch[fueltype][technology_replaced] -= service_demand_tech

            return service_fueltype_tech_after_switch

    def enduse_switches_service_to_fuel(self, service_fueltype_tech, tech_stock, enduse_fuel_spec_change):
        """Calculate fuel for every fueltype based on serice per technology

        """
        # Initialise with all fuetlypes
        fuels_per_fueltype = np.zeros((enduse_fuel_spec_change.shape))

        # Convert service to fuel
        for fueltype in service_fueltype_tech:
            for tech in service_fueltype_tech[fueltype]:
                fuel = service_fueltype_tech[fueltype][tech] / tech_stock.get_technology_attribute(tech, 'eff_cy')
                fuels_per_fueltype[fueltype] += np.sum(fuel)

        setattr(self, 'enduse_fuel_new_fuel', fuels_per_fueltype)

    '''def enduse_switches_service_to_fuel_p(self, service_fueltype_tech, tech_stock, enduse_fuel_spec_change):
        """Calculate percent of fuel for each technology within fueltype
        """
        # Convert service to fuel for each technology NEW
        fuel_fueltype_tech_p = mf.convert_service_tech_to_fuel_p(service_fueltype_tech, tech_stock)
        return fuel_fueltype_tech_p
    '''
    def enduse_service_to_fuel_per_tech(self, service_fueltype_tech, tech_stock):
        """Calculate percent of fuel for each technology within fueltype
        """
        # Initialise with all fuetlypes
        fuel_fueltype_tech = {}

        # Convert service to fuel
        for fueltype in service_fueltype_tech:

            for tech in service_fueltype_tech[fueltype]:
                fuel = service_fueltype_tech[fueltype][tech] / tech_stock.get_technology_attribute(tech, 'eff_cy')
                fuel_fueltype_tech[tech] = np.sum(fuel)

        return fuel_fueltype_tech

    def enduse_specific_change(self, data_ext, assumptions):
        """Calculates fuel based on assumed overall enduse specific fuel consumption changes

        Because for enduses where no technology stock is defined (and may consist of many different)
        technologies, a linear diffusion is suggested to best represent multiple
        sigmoid efficiency improvements of individual technologies.

        The changes are assumed across all fueltypes.

        Parameters
        ----------
        data_ext : dict
            Data

        assumptions : dict
            assumptions

        Returns
        -------
        out_dict : dict
            Dictionary containing new fuel demands for `enduse`

        Notes
        -----
        Either a sigmoid standard diffusion or linear diffusion can be implemented. Linear is suggested.
        """
        percent_ey = assumptions['enduse_overall_change_ey'][self.enduse]  # Percent of fuel consumption in end year
        percent_by = 1.0                                                   # Percent of fuel consumption in base year (always 100 % per definition)
        diff_fuel_consump = percent_ey - percent_by                        # Percent of fuel consumption difference
        diffusion_choice = assumptions['other_enduse_mode_info']['diff_method'] # Diffusion choice

        if diff_fuel_consump != 0: # If change in fuel consumption
            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0], 1)) #fueltypes, days, hours

            # Lineare diffusion up to cy
            if diffusion_choice == 'linear':
                lin_diff_factor = mf.linear_diff(
                    data_ext['glob_var']['base_yr'],
                    data_ext['glob_var']['curr_yr'],
                    percent_by,
                    percent_ey,
                    len(data_ext['glob_var']['sim_period'])
                )
                change_cy = diff_fuel_consump * abs(lin_diff_factor)

            # Sigmoid diffusion up to cy
            elif diffusion_choice == 'sigmoid':
                sig_diff_factor = mf.sigmoid_diffusion(data_ext['glob_var']['base_yr'], data_ext['glob_var']['curr_yr'], data_ext['glob_var']['end_yr'], assumptions['other_enduse_mode_info']['sigmoid']['sig_midpoint'], assumptions['other_enduse_mode_info']['sigmoid']['sig_steeppness'])
                change_cy = diff_fuel_consump * sig_diff_factor

            # Calculate new fuel consumption percentage
            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                new_fuels[fueltype] = fuel * (1 + change_cy)

            # Set attr
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def temp_correction_hdd_cdd(self, cooling_factor_y, heating_factor_y):
        """Change fuel demand for heat and cooling service depending on
        changes in HDD and CDD within a region

        It is assumed that fuel consumption correlates directly with
        changes in HDD or CDD. This is plausible as today's share of heatpumps
        is only marginal.

        Ignore technology mix and efficiencies. This will be taken into consideration with other steps

        Returns
        -------
        setattr

        Notes
        ----
        `cooling_factor_y` and `heating_factor_y` are based on the sum over the year. Therfore
        it is assumed that fuel correlates directly with HDD or CDD
        """
        new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0], 1))

        if self.enduse == 'space_heating':
            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                new_fuels[fueltype] = fuel * heating_factor_y

            # Setattr
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

        elif self.enduse == 'cooling':
            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                new_fuels[fueltype] = fuel * cooling_factor_y

            # Setattr
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def enduse_elasticity(self, data_ext, assumptions):
        """Adapts yearls fuel use depending on elasticity

        # TODO: MAYBE ALSO USE BUILDING STOCK TO SEE HOW ELASTICITY CHANGES WITH FLOOR AREA
        Maybe implement resid_elasticities with floor area

        # TODO: Non-linear elasticity. Then for cy the elasticity needs to be calculated

        Info
        ----------
        Every enduse can only have on shape independently of the fueltype
        """
        if data_ext['glob_var']['curr_yr'] != data_ext['glob_var']['base_yr']: # if not base year

            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0], 1)) #fueltypes, days, hours

            # End use elasticity
            elasticity_enduse = assumptions['resid_elasticities'][self.enduse]
            #elasticity_enduse_cy = nonlinear_def...

            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):

                if fuel != 0: # if fuel exists
                    fuelprice_by = data_ext['fuel_price'][data_ext['glob_var']['base_yr']][fueltype] # Fuel price by
                    fuelprice_cy = data_ext['fuel_price'][data_ext['glob_var']['curr_yr']][fueltype] # Fuel price ey
                    new_fuels[fueltype] = mf.apply_elasticity(fuel, elasticity_enduse, fuelprice_by, fuelprice_cy)
                else:
                    new_fuels[fueltype] = fuel

            # Set attr
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def smart_meter_eff_gain(self, data_ext, assumptions):
        """Calculate fuel savings depending on smart meter penetration

        The smart meter penetration is assumed with a sigmoid diffusion.

        In the assumptions the maximum penetration and also the
        generally fuel savings for each enduse can be defined.

        Parameters
        ----------
        data_ext : dict
            External data
        assumptions : dict
            assumptions

        Returns
        -------
        new_fuels : array
            Fuels which are adapted according to smart meter penetration
        """
        if self.enduse in assumptions['general_savings_smart_meter']:
            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0], 1)) #fueltypes, fuel

            # Sigmoid diffusion up to current year
            sigm_factor = mf.sigmoid_diffusion(data_ext['glob_var']['base_yr'], data_ext['glob_var']['curr_yr'], data_ext['glob_var']['end_yr'], assumptions['sig_midpoint'], assumptions['sig_steeppness'])

            # Smart Meter penetration (percentage of people having smart meters)
            penetration_by = assumptions['smart_meter_p_by']
            penetration_cy = assumptions['smart_meter_p_by'] + (sigm_factor * (assumptions['smart_meter_p_ey'] - assumptions['smart_meter_p_by']))

            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):

                # Saved fuel
                saved_fuel = fuel * (penetration_by - penetration_cy) * assumptions['general_savings_smart_meter'][self.enduse]
                #print("saved fuel--" + str(penetration_cy) + "-------" + str(self.enduse) + "------" + str(sigm_factor) + "--------" + str(np.sum(saved_fuel)))

                # New fuel
                new_fuels[fueltype] = fuel - saved_fuel

            # Set attr
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def enduse_building_stock_driver(self, data, data_ext):
        """The fuel data for every end use are multiplied with respective scenario driver

        If no building specific scenario driver is found, the identical fuel is returned.

        The HDD is calculated seperately!

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuels_h : array
            Hourly fuel data [fueltypes, days, hours]

        Notes
        -----
        This is the energy end use used for disaggregating to daily and hourly
        """
        new_fuels = copy.deepcopy(self.enduse_fuel_new_fuel)

        # Test if enduse has a building related scenario driver
        if hasattr(data['dw_stock'][self.reg_name][data_ext['glob_var']['base_yr']], self.enduse) and data_ext['glob_var']['curr_yr'] != data_ext['glob_var']['base_yr']:

            # Scenariodriver of building stock base year and new stock
            by_driver = getattr(data['dw_stock'][self.reg_name][data_ext['glob_var']['base_yr']], self.enduse) # Base year building stock
            cy_driver = getattr(data['dw_stock'][self.reg_name][data_ext['glob_var']['curr_yr']], self.enduse) # Current building stock

            # base year / current (checked) (as in chapter 3.1.2 EQ E-2)
            factor_driver = cy_driver / by_driver # TODO: FROZEN Here not effecieicny but scenario parameters

            new_fuels = new_fuels * factor_driver
            #return new_fuels * factor_driver
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)


    def enduse_y_to_d(self, fuels, enduse_shape):
        """Generate array with fuels for every day
        """
        fuels_d = np.zeros((fuels.shape[0], 365, 1))

        for k, fuels in enumerate(fuels):
            fuels_d[k] = enduse_shape * fuels # a two dim array with load shapes in first row
        return fuels_d

    def enduse_d_to_h(self, fuels, enduse_shape):
        """Disaggregate yearly fuel data to every day in the year

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuels_h : array
            Hourly fuel data [fueltypes, days, hours]

        Notes
        -----
        """
        fuels_h = np.zeros((fuels.shape[0], 365, 24)) #fueltypes, days, hours

        # Iterate fueltypes and day and multiply daily fuel data with daily shape
        for k, fuel in enumerate(fuels):
            for day in range(365):
                fuels_h[k][day] = enduse_shape[day] * fuel[day]

        return fuels_h

    def calc_enduse_fuel_peak_yd_factor(self, fuels, factor_d):
        """Disaggregate yearly absolute fuel data to the peak day.

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuels_d_peak : array
            Hourly absolute fuel data

        Example
        -----
        Input: 20 FUEL * 0.004 [0.4%] --> new fuel

        """
        fuels_d_peak = np.zeros((len(fuels), 1))

        for fueltype, fueltype_year_data in enumerate(fuels):
            fuels_d_peak[fueltype] = factor_d * fueltype_year_data[0]

        return fuels_d_peak

    def calc_enduse_fuel_peak_yh(self, fuels, shape_peak_dh):
        """Disaggregate daily peak day fuel data to the peak hours.

        Parameters
        ----------
        self : self
            Data from constructor

        shape_peak_dh : dict
            Peak shape for enduse (here not iteration over technology shapes)

        Returns
        -------
        fuels_h_peak : array
            Hourly fuel data [fueltypes, peakday, peak_hours]

        Notes
        -----
        """
        fuels_h_peak = np.zeros((fuels.shape[0], 1, 24)) #fueltypes  days, hours

        # Iterate fueltypes and day and multiply daily fuel data with daily shape
        for fueltype, fuel_data in enumerate(fuels):
            fuels_h_peak[fueltype] = shape_peak_dh * fuel_data

        return fuels_h_peak

class CountryResidentialModel(object):
    """Class of a country containing all regions as self.attributes

    The main class of the residential model. For every region, a Region object needs to be generated.

    Parameters
    ----------
    reg_names : list
        Dictionary containign the name of the Region (unique identifier)
    data : dict
        Main data dictionary
    data_ext : dict
        Main external data

    Notes
    -----
    this class has as many attributes as regions (for evry rgion an attribute)
    """
    def __init__(self, reg_names, data, data_ext):
        """Constructor of the class which holds all regions of a country
        """
        # Create object for every region
        self.create_regions(reg_names, data, data_ext)




        # Functions to summarise data for all Regions in the CountryResidentialModel class
        self.tot_country_fuel = self.get_overall_sum(reg_names)
        self.tot_country_fuel_enduse_specific_h = self.get_sum_for_each_enduse_h(data, reg_names) #yearly fuel
        self.tot_country_fuel_load_max_h = self.peak_loads_per_fueltype(data, reg_names, 'reg_load_factor_h')
        
        self.tot_country_fuel_max_allenduse_fueltyp = self.peak_loads_per_fueltype(data, reg_names, 'max_fuel_peak')

        #prnt("..")

        # TESTER: READ OUT Specific ENDUSE for a REGION
        #print("AA: " + str(self.get_specific_enduse_region('Wales', 'space_heating')))

        # ----- Testing
        n = 0
        for i in self.tot_country_fuel_enduse_specific_h:
            n += self.tot_country_fuel_enduse_specific_h[i]
        #print("============================ddddddddddd= " + str(self.tot_country_fuel))

        # TESTING
        test_sum = 0
        for enduse in self.tot_country_fuel_enduse_specific_h:
            test_sum += self.tot_country_fuel_enduse_specific_h[enduse]
        np.testing.assert_almost_equal(np.sum(self.tot_country_fuel), test_sum, decimal=5, err_msg='', verbose=True)

    def create_regions(self, reg_names, data, data_ext):
        """Create all regions and add them as attributes based on region name to the CountryResidentialModel Class

        Parameters
        ----------
        reg_names : list
            The name of the Region (unique identifier)
        """
        for reg_name in reg_names:
            CountryResidentialModel.__setattr__(
                self,
                str(reg_name),
                Region(
                    reg_name,
                    data,
                    data_ext
                )
            )

    def get_specific_enduse_region(self, spec_region, spec_enduse):
        _a = getattr(self, spec_region)
        enduse_fuels = _a.get_fuels_enduse_requested(spec_enduse)
        return enduse_fuels

    def get_overall_sum(self, reg_names):
        """Collect hourly data from all regions and sum across all fuel types and enduses
        """
        tot_sum = 0
        for reg_name in reg_names:
            reg_object = getattr(self, str(reg_name)) # Get region

            # Get fuel data of region #Sum hourly demand # could also be read out as houly
            tot_sum += np.sum(getattr(reg_object, 'fuels_tot_enduses_h'))

        return tot_sum

    def get_sum_for_each_enduse_h(self, data, reg_names):
        """Collect end_use specific hourly data from all regions and sum across all fuel types

        out: {enduse: sum(all_fuel_types)}

        """
        tot_h = np.zeros((365, 24))

        tot_sum_enduses = {}
        for enduse in data['resid_enduses']:
            tot_sum_enduses[enduse] = 0

        for reg_name in reg_names:
            reg_object = getattr(self, str(reg_name)) # Get region

            # Get fuel data of region
            enduse_fuels_reg = getattr(reg_object, 'fuels_new_enduse_specific_h')

            for enduse in enduse_fuels_reg:
                tot_sum_enduses[enduse] += np.sum(enduse_fuels_reg[enduse]) # sum across fuels

            #for enduse in enduse_fuels_reg:
            #    tot_h += enduse_fuels_reg[enduse]
        return tot_sum_enduses
        #return tot_h



    def peak_loads_per_fueltype(self, data, reg_names, attribute_to_get):
        """Get peak loads for fueltype per maximum h
        """
        peak_loads_fueltype_max_h = np.zeros((len(data['lu_fueltype']), 1))

        for reg_name in reg_names:
            reg_object = getattr(self, str(reg_name)) # Get region

            # Get fuel data of region
            load_max_h = getattr(reg_object, attribute_to_get)

            for fueltype, load_max_h in enumerate(load_max_h):
                peak_loads_fueltype_max_h[fueltype] += load_max_h

        return peak_loads_fueltype_max_h








# ------------- Testing functions
def test_function_fuel_sum(data):
    """ Sum raw disaggregated fuel data """
    fuel_in = 0
    for reg in data['fueldata_disagg']:
        for enduse in data['fueldata_disagg'][reg]:
            fuel_in += np.sum(data['fueldata_disagg'][reg][enduse])
    return fuel_in
