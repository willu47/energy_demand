"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103, C0325

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

import energy_demand.technological_stock as ts
import energy_demand.technological_stock_functions as tf
import energy_demand.main_functions as mf

# TODO: Write function to convert array to list and dump it into txt file / or yaml file (np.asarray(a.tolist()))

class Region(object):
    """Class of a region for the residential model

    The main class of the residential model. For every region, a Region Object needs to be generated.

    Parameters
    ----------
    reg_id : int
        The ID of the region. The actual region name is stored in `reg_lu`
    data : dict
        Dictionary containing data
    data_ext : dict
        Dictionary containing all data provided specifically for scenario run and from wrapper.abs

    # TODO: CHECK IF data could be reduced as input (e.g. only provide fuels and not data)
    """
    def __init__(self, reg_id, data, data_ext):
        """Constructor or Region"""
        self.reg_id = reg_id                                        # ID of region
        self.data = data                                            # data
        self.data_ext = data_ext                                    #: external data
        self.assumptions = data['assumptions']                      #: Improve: Assumptions per region
        self.current_year = data_ext['glob_var']['current_year']    #: Current year
        self.reg_fuel = data['fueldata_disagg'][reg_id]             #: Fuel array of region (used to extract all end_uses)

        #self.pop = data_ext['population'][self.current_year][self.reg_id] # Population of current year

        # Create all end uses objects
        self.create_end_use_objects()

        # Sum final fuels of all end_uses
        self.fuels_new = self.tot_all_enduses_y()

        # Get peak demand day
        self.enduse_fuel_peak_d = self.get_enduse_peak_d()

        # Get peak demand h (summarise over all enduses)
        self.enduse_fuel_peak_h = self.get_enduse_peak_h()

        # Sum daily demand
        self.fuels_tot_enduses_d = self.tot_all_enduses_d()

        # Sum hourly demand
        self.fuels_tot_enduses_h = self.tot_all_enduses_h()

        # Testing
        np.testing.assert_almost_equal(np.sum(self.fuels_tot_enduses_d), np.sum(self.fuels_tot_enduses_h), err_msg='The Regional disaggregation from d to h went wrong')

        # Calculate load factors
        self.reg_load_factor_d = self.load_factor_d()
        self.reg_load_factor_h = self.load_factor_h()

        # Plot stacked end_uses
        #self.plot_stacked_regional_end_use(1, 2) #days, fueltype

    def create_end_use_objects(self):
        """Initialises all defined end uses. Adds an object for each end use to the Region class"""
        a = {}
        for enduse in self.reg_fuel:
            a[enduse] = EndUseClassResid(self.reg_id, self.data, self.data_ext, enduse, self.reg_fuel)
        self.end_uses = a
        for _ in self.end_uses:
            vars(self).update(self.end_uses)     # Creat self objects {'key': Value}

    def tot_all_enduses_y(self):
        '''Summen all fuel types over all end uses'''

        # Initialise array to store fuel
        sum_fuels = np.zeros((len(self.data['fuel_type_lu']), 1))

        for enduse in self.reg_fuel:

            # Fuel of Enduse
            sum_fuels += self.__getattr__subclass__(enduse, 'reg_fuelscen_driver')

        return sum_fuels

    def tot_all_enduses_d(self):
        """Calculate total daily fuel demand for each fueltype"""

        # Initialise array to store fuel
        sum_fuels_d = np.zeros((len(self.data['fuel_type_lu']), 365))

        for enduse in self.reg_fuel:
            sum_fuels_d += self.__getattr__subclass__(enduse, 'reg_fuel_d')

        return sum_fuels_d

    def get_enduse_peak_d(self):
        """Summarise peak value of all end_uses"""
        sum_enduse_peak_d = np.zeros((len(self.data['fuel_type_lu']), 1))

        for enduse in self.reg_fuel:

            # Fuel of Enduse
            sum_enduse_peak_d += self.__getattr__subclass__(enduse, 'enduse_fuel_peak_d')

        return sum_enduse_peak_d

    def get_enduse_peak_h(self):
        """Summarise peak value of all end_uses"""
        sum_enduse_peak_h = np.zeros((len(self.data['fuel_type_lu']), 1, 24))

        for enduse in self.reg_fuel:

            # Fuel of Enduse
            sum_enduse_peak_h += self.__getattr__subclass__(enduse, 'enduse_fuel_peak_h')

        return sum_enduse_peak_h

    def tot_all_enduses_h(self):
        """Calculate total hourly fuel demand for each fueltype"""

        # Initialise array to store fuel
        sum_fuels_h = np.zeros((len(self.data['fuel_type_lu']), 365, 24))

        for enduse in self.reg_fuel:
            sum_fuels_h += self.__getattr__subclass__(enduse, 'enduse_fuel_h') #np.around(fuel_end_use_h,10)

        # Read out more error information (e.g. RuntimeWarning)
        #np.seterr(all='raise') # If not round, problem....np.around(fuel_end_use_h,10)
        return sum_fuels_h

    def load_factor_d(self):
        """Calculate load factor of a day in a year
        """
        pass
        '''# Initialise array to store fuel
        lf_y = np.zeros((len(self.data['fuel_type_lu']), 1))

        maximum_d = self.enduse_fuel_peak_d

        # Iterate fueltypes to calculate load factors for each fueltype
        for k, data_fueltype in enumerate(self.fuels_tot_enduses_d):

            # Averae load = yearly demand / nr of days
            average_demand = np.sum(data_fueltype) / 365

            # Calculate load factor
            lf_y[k] = average_demand / maximum_d[k]

        return lf_y
        '''

    def load_factor_h(self):
        """Calculate load factor of a h in a year
        # TODO: PEAK CAlculations are still wrong

        # Note retirmd as [%]...
        """
        # Initialise array to store fuel
        lf_y = np.zeros((len(self.data['fuel_type_lu']), 1))

        # Iterate fueltypes to calculate load factors for each fueltype
        for fueltype, data_fueltype in enumerate(self.fuels_tot_enduses_h):
            #print("FUELTYPE: " + str(fueltype))
            maximum_h_of_day = np.amax(self.enduse_fuel_peak_h[fueltype])

            #print("maximum_h_of_day: " + str(maximum_h_of_day))

            # If there is a maximum day hour
            if maximum_h_of_day != 0:

                # Averae load = yearly demand / nr of days
                average_demand_h = np.sum(data_fueltype) / (365 * 24)
                #print("data_fueltype:    " + str(np.sum(data_fueltype)))
                #print("average_demand_h: " + str(average_demand_h))

                # Calculate load factor
                lf_y[fueltype] = average_demand_h / maximum_h_of_day

        #print("lf_y: " + str(lf_y))
        return lf_y

    def __getattr__(self, attr):
        """ Get method of own object"""
        return self.attr

    def __getattr__subclass__(self, attr_main_class, attr_sub_class):
        """ Returns the attribute of a subclass"""
        object_class = getattr(self, attr_main_class)
        object_subclass = getattr(object_class, attr_sub_class)
        return object_subclass

    def plot_stacked_regional_end_use(self, nr_of_day_to_plot, fueltype):
        """ Plots stacked end_use for a region
        #TODO: Make that end_uses can be sorted, improve legend...
        """

        fig, ax = plt.subplots()
        nr_hours_to_plot = nr_of_day_to_plot * 24

        x = np.arange(nr_hours_to_plot)
        legend_entries = []

        # Initialise (number of enduses, number of hours to plot)
        Y_init = np.zeros((len(self.reg_fuel), nr_hours_to_plot))

        # Iterate enduse
        for k, enduse in enumerate(self.reg_fuel):
            legend_entries.append(enduse)
            sum_fuels_h = self.__getattr__subclass__(enduse, 'enduse_fuel_h') #np.around(fuel_end_use_h,10)
            data_fueltype_enduse = np.zeros((nr_hours_to_plot, ))
            list_all_h = []

            #Get data of a fueltype
            for j, fuel_data in enumerate(sum_fuels_h[fueltype][:nr_of_day_to_plot]):

                for h in fuel_data:
                    list_all_h.append(h)

            Y_init[k] = list_all_h

        color_list = ["green", "red", "#6E5160"]

        sp = ax.stackplot(x,Y_init)
        proxy = [mpl.patches.Rectangle((0,0), 0,0, facecolor=pol.get_facecolor()[0]) for pol in sp]

        ax.legend(proxy, legend_entries)

        plt.axis('tight')

        plt.xlabel("Hours")
        plt.ylabel("Energy demand in kWh")
        plt.title("Stacked energy demand")

        #from matplotlib.patches import Rectangle

        #legend_boxes = []
        #for i in color_list:
        #    box = Rectangle((0, 0), 1, 1, fc=i)
        #    legend_boxes.append(box)
        #ax.legend(legend_boxes, legend_entries)

        #ax.stackplot(x, Y_init)
        plt.show()


class EndUseClassResid(Region):
    """Class of an end use category of the residential sector"""

    def __init__(self, reg_id, data, data_ext, enduse, reg_fuel):

        # --General data, fueldata, technological stock
        self.reg_id = reg_id                                        # Region
        self.enduse = enduse                                        # EndUse Name
        self.current_year = data_ext['glob_var']['current_year']    # from parent class
        self.data = data                                            # from parent class
        self.data_ext = data_ext                                    # from parent class
        self.assumptions = data['assumptions']                      # Assumptions from regions
        self.reg_fuel = reg_fuel[enduse]                            # Regional base fuel data
        self.tech_stock = data['tech_stock']                        # Technological stock

        # --Load shapes
        self.enduse_shape_d = data['dict_shapes_end_use_d'][enduse]['shape_d_non_peak']  # shape_d
        self.enduse_shape_h = data['dict_shapes_end_use_h'][enduse]['shape_h_non_peak']  # shape_h
        self.enduse_shape_peak_d = data['dict_shapes_end_use_d'][enduse]['peak_d_shape'] # shape_d peak (Factor to calc one day)
        self.enduse_shape_peak_h = data['dict_shapes_end_use_h'][enduse]['peak_h_shape'] # shape_h peak

        # --Yearly fuel data
        #self.reg_fuel_eff_gains = self.enduse_eff_gains()                # General efficiency gains of technology over time #TODO
        self.reg_fuel_after_switch = self.enduse_fuel_switches()         # Calculate fuel switches
        self.reg_fuel_after_elasticity = self.enduse_elasticity()        # Calculate demand with changing elasticity (elasticity maybe on household level with floor area)
        self.reg_fuelscen_driver = self.enduse_scenario_driver()         # Calculate new fuel demands after scenario drivers TODO: THIS IS LAST MUTATION IN PROCESS... (all disaggreagtion function refer to this)

        # --Daily fuel data
        self.reg_fuel_d = self.enduse_y_to_d()                           # Disaggregate yearly demand for every day

        # --Hourly fuel data
        self.enduse_fuel_h = self.enduse_d_to_h()                        # Disaggregate daily demand to hourly demand
        self.enduse_fuel_peak_d = self.enduse_peak_d()                   # Calculate peak day
        self.enduse_fuel_peak_h = self.enduse_peak_h()                   # Calculate peak hour

        # Testing
        np.testing.assert_almost_equal(np.sum(self.reg_fuel_d), np.sum(self.enduse_fuel_h), decimal=7, err_msg='', verbose=True)
        #np.testing.assert_almost_equal(a,b) #np.testing.assert_almost_equal(self.reg_fuel_d, self.enduse_fuel_h, decimal=5, err_msg='', verbose=True)

    def enduse_elasticity(self):
        """ Adapts yearls fuel use depending on elasticity

        Maybe implement elasticities with floor area"""
        '''
        new_fuels = np.zeros((self.reg_fuel_after_switch.shape[0], 1)) #fueltypes, days, hours

        # Will maybe be on household level

        fuelprice_by = 100  #Ev. mix aus verschiedenen fueltypes
        fuelprice_cy = 105

        elasticity_enduse = 0.5

        for k, fuel in enumerate(self.reg_fuel_after_switch):
            new_fuels[k] = mf.get_elasticity(fuel, elasticity_enduse, fuelprice_by, fuelprice_cy)
        return new_fuels
        '''
        pass

    def enduse_eff_gains(self):
        """Adapts yearls fuel use depending on efficiency gains of technologies """
        # Will maybe be on household level

        out_dict = np.zeros((self.reg_fuel.shape[0], 1)) #fueltypes, data

        # Get technologies of end_use
        #get_enduse_technologies = data['assumptions']['tech_by_enduse'][self.enduse] #e.g. lightning = {'fueltype': {'tech_A': 0.5, 'tech_B': 0.5}}

        # Get technologies and share of enduse
        tech_and_shares = self.data['assumptions']['technologies_enduse_by'][self.enduse]

        # Iterate fuels
        for k, fuel in self.reg_fuel:

            # Iterate technologies and average efficiencies relative to distribution
            av_efficiency = 0
            for technology in tech_and_shares[k]:
                eff_tech_cy = self.tech_stock['technology']
                tech_cy_share = tech_and_shares[k][technology]
                av_efficiency += tech_cy_share * eff_tech_cy

            # Calc new demand considering efficiency change
            out_dict[k] = av_efficiency * fuel

        return out_dict


    def enduse_fuel_switches(self):
        """Calculates absolute fuel changes from assumptions about switches in changes of fuel percentages
        It also considers technological efficiency changes of replaced and old technologies.

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuel_switch_array : array
            tbd

        Notes
        -----
        """
        # Share of fuel types for each end use
        fuel_p_by = self.assumptions['fuel_type_p_by'][self.enduse] # Base year
        fuel_p_ey = self.assumptions['fuel_type_p_ey'][self.enduse] # End year

        # Test whether share of fuel types stays identical
        if np.array_equal(fuel_p_by, fuel_p_ey):            # no fuel switches
            return self.reg_fuel                            # No Fuel Switches (same perentages)
        else:
            fuel_switch_array = np.copy((self.reg_fuel))    # Out_dict initialisation

            # Assumptions about which technology is installed and replaced
            tech_install = self.assumptions['tech_install'][self.enduse]                   #  Technology which is installed
            eff_replacement = getattr(self.tech_stock, tech_install)

            tech_replacement_dict = self.assumptions['tech_replacement_dict'][self.enduse] #  Dict with current technologes which are to be replaced

            # Calculate percentage differences over full simulation period
            fuel_diff = fuel_p_ey[:, 1] - fuel_p_by[:, 1] # difference in percentage (ID gets wasted because it is substracted)
            #print("fuel_diff: " + str(fuel_diff))

            # Calculate sigmoid diffusion of fuel switches
            fuel_p_cy = fuel_diff * tf.sigmoidefficiency(self.data_ext['glob_var']['base_year'], self.current_year, self.data_ext['glob_var']['end_year'])
            #print("fuel_p_cy:" + str(fuel_p_cy))
            #print(fuel_p_ey[:, 1])
            #print("fuel_p_ey:" + str(fuel_p_ey))
            #print(fuel_p_cy.shape)
            #print("self.reg_fuel: " + str(self.reg_fuel))
            #print(self.reg_fuel.shape)

            # Differences in absolute fuel amounts
            absolute_fuel_diff = self.reg_fuel[0] * fuel_p_cy # Multiply fuel demands by percentage changes
            #print("absolute_fuel_diff: " + str(absolute_fuel_diff))
            #print("Technology which is installed:           " + str(tech_install))
            #print("Efficiency of technology to be installed " + str(eff_replacement))
            #print("Current Year:" + str(self.current_year))

            for fuel_type, fuel_diff in enumerate(absolute_fuel_diff):
                tech_replace = tech_replacement_dict[fuel_type]           # Technology which is replaced (read from technology replacement dict)
                eff_tech_remove = getattr(self.tech_stock, tech_replace)  # Get efficiency of technology to be replaced

                # Fuel factor   #TODO ev. auch umgekehrt
                fuel_factor = eff_tech_remove / eff_replacement
                fuel_consid_eff = fuel_diff * fuel_factor
                #print("Technology fuel factor difference: " + str(eff_tech_remove) + "   " + str(eff_replacement) + "  " + str(fuel_factor))
                #print("fuel_diff: " + str(fuel_diff))
                # Add  fuels (if minus, no technology weighting is necessary)
                if fuel_diff > 0:
                    fuel_switch_array[int(fuel_type)] += fuel_consid_eff # Add Fuel

            #print("Old Fuel: " + str(self.reg_fuel))
            #print("--")
            #print("New Fuel: " + str(fuel_switch_array))
            return fuel_switch_array

    def enduse_scenario_driver(self):
        """The fuel data for every end use are multiplied with respective scenario driver

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
        if self.enduse == 'heating':
            attr_building_stock =  'heating' #'sd_{}'.format('heating')
        else:
            #TODO: add very end_use
            attr_building_stock = 'heating' #'heating'

        # Scenariodriver of building stock base year and new stock
        by_driver = getattr(self.data['reg_building_stock_by'][self.reg_id], attr_building_stock)     # Base year building stock
        cy_driver = getattr(self.data['reg_building_stock_cur_yr'][self.reg_id], attr_building_stock) # Current building stock

        factor_driver = cy_driver / by_driver  #TODO: Or the other way round

        fueldata_scenario_diver = self.reg_fuel_after_switch * factor_driver
        return fueldata_scenario_diver

    def enduse_y_to_d(self):
        """Generate array with fuels for every day"""

        fuels_d = np.zeros((len(self.reg_fuel), 365))

        # Iterate yearday and
        for k, fueltype_year_data in enumerate(self.reg_fuelscen_driver):
            fuels_d[k] = self.enduse_shape_d[:, 0] * fueltype_year_data[0] # enduse_shape_d is  a two dim array with load shapes in first row

        return fuels_d

    def enduse_d_to_h(self):
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
        fuels_h = np.zeros((self.reg_fuel_d.shape[0], 365, 24)) #fueltypes, days, hours

        # Iterate fueltypes and day and multiply daily fuel data with daily shape
        for k, fuel_type_data in enumerate(self.reg_fuel_d):
            for day in range(365):
                fuels_h[k][day] = self.enduse_shape_h[day] * fuel_type_data[day]

        return fuels_h

    def enduse_peak_d(self):
        """Disaggregate yearly fuel data to the peak day.

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuels_d_peak : array
            Hourly fuel data [fueltypes, peak_day, hours]

        Notes
        -----
        """
        fuels_d_peak = np.zeros((len(self.reg_fuel), 1))

        # Iterate yearday and
        for k, fueltype_year_data in enumerate(self.reg_fuelscen_driver):
            #print("AA")
            #print(fueltype_year_data[0])
            #print(self.enduse_shape_peak_d)
            #print(self.enduse_shape_peak_d * fueltype_year_data[0])
            #prnt("..dd")
            fuels_d_peak[k] = self.enduse_shape_peak_d * fueltype_year_data[0] # enduse_shape_d is  a two dim array with load shapes in first row

        return fuels_d_peak

    def enduse_peak_h(self):
        """Disaggregate daily peak day fuel data to the peak hours.

        Parameters
        ----------
        self : self
            Data from constructor

        Returns
        -------
        fuels_h_peak : array
            Hourly fuel data [fueltypes, peakday, peak_hours]

        Notes
        -----
        """
        fuels_h_peak = np.zeros((self.reg_fuel_d.shape[0], 1, 24)) #fueltypes  days, hours

        # Iterate fueltypes and day and multiply daily fuel data with daily shape
        for k, fuel_data in enumerate(self.enduse_fuel_peak_d):
            for day in range(1):
                #print("fuel_data: " + str(fuel_data))
                #print(self.enduse_shape_peak_h)
                #print(self.enduse_shape_peak_h * fuel_data[day])
                #prnt("..")
                fuels_h_peak[k][day] = self.enduse_shape_peak_h * fuel_data[day]

        return fuels_h_peak
