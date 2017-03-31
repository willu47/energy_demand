"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103, C0325

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import energy_demand.technological_stock_functions as tf
import energy_demand.main_functions as mf
import energy_demand.technological_stock as ts
import logging

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
    # TESTING
    fuel_in = 0
    for reg in data['fueldata_disagg']:
        for enduse in data['fueldata_disagg'][reg]:
            fuel_in += np.sum(data['fueldata_disagg'][reg][enduse])
    print("TEST MAIN START:" + str(fuel_in))

    # Generate technological stock
    data['tech_stock_by'] = ts.ResidTechStock(data, data_ext, data_ext['glob_var']['base_year']) # Generate technological stock for base year
    data['tech_stock_cy'] = ts.ResidTechStock(data, data_ext, data_ext['glob_var']['current_yr']) # Generate technological stock for current year


    # Add all region instances as an attribute (region name) into a Country class
    resid_object = Country_residential_model(data['reg_lu'], data, data_ext)

    # Total fuel of country
    fueltot = resid_object.tot_country_fuel

    # Total fuel of country for each enduse
    country_enduses = resid_object.tot_country_fuel_enduse_specific
    print("country_enduses")
    print(country_enduses)

    #TODO get tot_fuel_for_ever_enduse

    #TEST total fuel after run
    print("TEST MAIN START:" + str(fuel_in))
    print("Total Fuel after run: " + str(fueltot))
    print("DIFF: " + str(fueltot - fuel_in))

    return resid_object

class EndUseClassResid(object): #OBJECT OR REGION? --> MAKE REGION IS e.g. data is loaded from parent class
    """Class of an end use category of the residential sector

    End use class for residential model. For every region, a different
    instance is generated.

    Parameters
    ----------
    reg_id : int
        The ID of the region. The actual region name is stored in `reg_lu`
    data : dict
        Dictionary containing data
    data_ext : dict
        Dictionary containing all data provided specifically for scenario run and from wrapper
    enduse : str
        Enduse given in a string
    reg_fuel : array
        Fuel data for the region the endu

    Info
    ----------
    Every enduse can only have on shape independently of the fueltype

    """
    def __init__(self, reg_id, data, data_ext, enduse, reg_fuel):

        # Call parent data
        #super().__init__(reg_id, data, data_ext)

        # --General data, fueldata, technological stock
        self.reg_id = reg_id                                        # Region
        self.enduse = enduse                                        # EndUse Name
        self.current_yr = data_ext['glob_var']['current_yr']        # from parent class
        self.base_year = data_ext['glob_var']['base_year']          # from parent class
        self.data = data                                            # from parent class
        self.data_ext = data_ext                                    # from parent class
        self.assumptions = data['assumptions']                      # Assumptions from regions
        self.reg_fuel = reg_fuel[enduse]                            # Regional base fuel data
        self.tech_stock_by = data['tech_stock_by']                  # Technological stock base_data['tech_stock_by']
        self.tech_stock_cy = data['tech_stock_cy']                  # Technological stock base_data['tech_stock_by']

        # --Load shapes
        self.enduse_shape_d = data['dict_shp_enduse_d_resid'][enduse]['shape_d_non_peak']  # shape_d
        self.enduse_shape_h = data['dict_shp_enduse_h_resid'][enduse]['shape_h_non_peak']  # shape_h
        self.enduse_shape_peak_d = data['dict_shp_enduse_d_resid'][enduse]['shape_d_peak'] # shape_d peak (Factor to calc one day)
        self.enduse_shape_peak_h = data['dict_shp_enduse_h_resid'][enduse]['shape_h_peak'] # shape_h peak

        print("INITIAL FUEL " + str(enduse))
        print(self.reg_fuel)

        # --Yearly fuel data (Check if always function below takes result from function above)
        self.reg_fuel_eff_gains = self.enduse_eff_gains()                # General efficiency gains of technology over time
        print("reg_fuel_eff_gains: " + str(self.reg_fuel_eff_gains))

        self.reg_fuel_after_switch = self.enduse_fuel_switches()         # Calculate fuel switches
        #print("reg_fuel_after_switch: " + str(self.reg_fuel_after_switch))

        self.reg_fuel_after_elasticity = self.enduse_elasticity()        # Calculate demand with changing elasticity (elasticity maybe on household level with floor area)
        print("reg_fuel_after_elasticity: " + str(self.reg_fuel_after_elasticity))

        self.reg_fuelscen_driver = self.enduse_scenario_driver()         # Calculate new fuel demands after scenario drivers TODO: THIS IS LAST MUTATION IN PROCESS... (all disaggreagtion function refer to this)
        #print("reg_fuelscen_driver: " + str(self.reg_fuelscen_driver))
        #print(self.reg_fuelscen_driver)

        # --Daily fuel data
        self.reg_fuel_d = self.enduse_y_to_d()                           # Disaggregate yearly demand for every day

        # --Hourly fuel data
        self.enduse_fuel_h = self.enduse_d_to_h()                        # Disaggregate daily demand to hourly demand

        # --Peak data
        self.enduse_fuel_peak_d = self.enduse_peak_d()                   # Calculate peak day
        #print("enduse_fuel_peak_d")
        #print(self.enduse_fuel_peak_d)
        self.enduse_fuel_peak_h = self.enduse_peak_h()                   # Calculate peak hour

        # Testing
        np.testing.assert_almost_equal(np.sum(self.reg_fuel_d), np.sum(self.enduse_fuel_h), decimal=5, err_msg='', verbose=True)
        #np.testing.assert_almost_equal(a,b) #np.testing.assert_almost_equal(self.reg_fuel_d, self.enduse_fuel_h, decimal=5, err_msg='', verbose=True)

    def enduse_elasticity(self):
        """Adapts yearls fuel use depending on elasticity

        # TODO: MAYBE ALSO USE BUILDING STOCK TO SEE HOW ELASTICITY CHANGES WITH FLOOR AREA
        Maybe implement resid_elasticities with floor area

        # TODO: Non-linear elasticity. Then for cy the elasticity needs to be calculated

        Info
        ----------
        Every enduse can only have on shape independently of the fueltype

        """
        try:
            if self.current_yr == self.base_year:
                return self.reg_fuel_after_switch
            else:
                new_fuels = np.zeros((self.reg_fuel_after_switch.shape[0], 1)) #fueltypes, days, hours

                # End use elasticity
                elasticity_enduse = self.assumptions['resid_elasticities'][self.enduse]
                #elasticity_enduse_cy = nonlinear_def...

                for fueltype, fuel in enumerate(self.reg_fuel_after_switch):

                    if fuel != 0: # if fuel exists
                        fuelprice_by = self.data_ext['fuel_price'][self.base_year][fueltype] # Fuel price by
                        fuelprice_cy = self.data_ext['fuel_price'][self.current_yr][fueltype] # Fuel price ey

                        new_fuels[fueltype] = mf.apply_elasticity(fuel, elasticity_enduse, fuelprice_by, fuelprice_cy)
                    else:
                        new_fuels[fueltype] = fuel
                #print("enduse:  " + str(self.enduse))
                ##print(elasticity_enduse)
                #print(self.reg_fuel_after_switch)
                #print("....")
                #print(new_fuels)
                return new_fuels

        except Exception as err:
            print("ERROR: " + str(err.args))
            prnt("..")
            #logging.info("--")
            #logging.exception('I .Raised error in enduse_elasticity. Check if for every provided enduse an elasticity is provided')

    def enduse_eff_gains(self):
        """Adapts yearly fuel demand depending on technology mix within each fueltype (e.g. boiler_elcA to boiler_elecB)

        This function implements technology switch within each enduse

        (Does not consider share of fuel which is switched)

        Steps:
            1. Get technological fraction of each enduse
            2. Get efficiencies of base and current year
            3. Overall efficiency of all technologies is used

        Returns
        -------
        out_dict : dict
            Dictionary containing new fuel demands for `enduse`

        Notes
        -----
        In this function the change in fuel is calculated for the enduse
        only based on the change in the fraction of technology (technology stock)
        composition.

        It does not consider fuel switches (e.g. % of fuel which is replaced) for
        an enduse but only calculated within each fuel type.

        # Will maybe be on household level
        """
        if self.current_yr != self.base_year:
            print("calc ulate efficiencies")
            out_dict = np.zeros((self.reg_fuel.shape[0], 1))

            # Get technologies and share of technologies for each fueltype and enduse
            tech_frac_by = getattr(self.tech_stock_by, 'tech_frac_by')
            tech_frac_cy = getattr(self.tech_stock_cy, 'tech_frac_cy')
            print("tech_frac_by: " + str(tech_frac_by))
            print("tech_frac_cy: " + str(tech_frac_cy))
            print(self.enduse)

            # Iterate fuels
            for fueltype, fueldata in enumerate(self.reg_fuel):
                print("tech_frac_by[self.enduse][fueltype]")
                print(tech_frac_by[self.enduse][fueltype])
                print("--")
                print(tech_frac_cy[self.enduse][fueltype])

                # Iterate technologies and average efficiencies relative to distribution for base year
                overall_eff_by = 0
                for technology in tech_frac_by[self.enduse][fueltype]:
                    print("Technology: " + str(tech_frac_by[self.enduse][fueltype][technology] * getattr(self.tech_stock_by, technology)))
                    # Overall efficiency: Share of technology * efficiency of base year technology
                    overall_eff_by += tech_frac_by[self.enduse][fueltype][technology] * getattr(self.tech_stock_by, technology)

                # Iterate technologies and average efficiencies relative to distribution for current year
                overall_eff_cy = 0
                for technology in tech_frac_cy[self.enduse][fueltype]:
                    #print("Technology: " + str(technology) + str("   ") + str(tech_frac_cy[self.enduse][fueltype][technology] * getattr(self.tech_stock_cy, technology)))
                    # Overall efficiency: Share of technology * efficiency of base year technology
                    overall_eff_cy += tech_frac_cy[self.enduse][fueltype][technology] * getattr(self.tech_stock_cy, technology)

                # Calc new demand considering efficiency change
                if overall_eff_cy != 0: # Do not copy any values
                    print("overall_eff_by: " + str(overall_eff_by))
                    print("overall_eff_cy: " + str(overall_eff_cy))
                    print("WWW: " + str(overall_eff_by / overall_eff_cy))
                    out_dict[fueltype] = fueldata * (overall_eff_by / overall_eff_cy) # FROZEN old tech eff / new tech eff
                else:
                    out_dict[fueltype] = fueldata

            return out_dict
        else:
            return self.reg_fuel

    def enduse_fuel_switches(self):
        """Calculates absolute fuel changes from assumptions about switches in changes of fuel percentages
        It also considers technological efficiency changes of replaced and old technologies.

        Replace fuel percentages (sigmoid fasion) with a technology

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
        Take as fuel input fuels after efficincy gains
        """
        # Share of fuel types for each end use
        fuel_p_by = self.assumptions['fuel_type_p_by'][self.enduse] # Base year
        fuel_p_ey = self.assumptions['fuel_type_p_ey'][self.enduse] # End year    #Maximum change in % of fueltype up to endyear

        # Test whether share of fuel types stays identical
        if np.array_equal(fuel_p_by, fuel_p_ey) or self.current_yr == self.base_year: # no fuel switches
            #return self.reg_fuel
            return self.reg_fuel_eff_gains
        else:
            fuel_switch_array = np.copy((self.reg_fuel)) # Out_dict initialisation

            # Assumptions about which technology is installed and replaced
            tech_install = self.assumptions['tech_install'][self.enduse] # Technology which is installed (new technology for switched fuel share)
            tech_install_fueltype = self.assumptions['technology_fueltype'][tech_install]

            #TODO: Either a specific technology in an enduse is defind which is replaced or the average of all technologies is taken?
            eff_install = getattr(self.tech_stock_cy, tech_install) # efficiency of installed technology in current year

            tech_replacement_dict = self.assumptions['tech_replacement_dict'][self.enduse] # Dict with current technologes which are to be replaced

            #print("SWITHC INFO  " + str(self.enduse))
            #print(tech_install_fueltype)
            #print(tech_install)
            #print(eff_install)
            #print("tech_replacement_dict")
            #print(tech_replacement_dict)

            #print("fuel_p_by " + str(fuel_p_by))
            #print("fuel_p_ey " + str(fuel_p_ey))

            # Calculate percentage differences over full simulation period
            #fuel_diff = fuel_p_ey[:, 1] - fuel_p_by[:, 1] # difference in percentage (ID gets wasted because it is substracted)
            #print("fuel_diff: " + str(fuel_diff))

            # Calculate fraction of share of fuels which is switched until current year (sigmoid diffusion)
            fuel_p_cy = fuel_p_ey[:, 1] * mf.sigmoid_diffusion(self.data_ext['glob_var']['base_year'], self.current_yr, self.data_ext['glob_var']['end_yr'], self.assumptions['sig_midpoint'], self.assumptions['sig_steeppness'])
            ##print("fuel_p_cy:" + str(fuel_p_cy))
            #print("self.reg_fuel_eff_gains:" + str(self.reg_fuel_eff_gains))
            #print(self.reg_fuel)
            #print(fuel_p_cy)

            # Calculate differences in absolute fuel amounts
            absolute_fuel_diff = self.reg_fuel_eff_gains[:, 0] * fuel_p_cy # Multiply fuel demands by percentage changes
            #print("absolute_fuel_diff: " + str(absolute_fuel_diff))
            #print("Technology which is installed:           " + str(tech_install))
            #print("Efficiency of technology to be installed " + str(eff_install))
            #print("Current Year:" + str(self.current_yr))

            for fuel_type, fuel_diff in enumerate(absolute_fuel_diff):
                #print("Fueltype: " + str(fuel_type))
                #print("fuel_diff: " + str(fuel_diff))

                # Only if there is a positive fuel difference
                if fuel_diff > 0:
                    tech_replace = tech_replacement_dict[fuel_type] # Technology which is replaced (read from technology replacement dict)
                    eff_tech_remove = getattr(self.tech_stock_cy, tech_replace)  # Get efficiency of technology to be replaced

                    # Amount of switched fuel * (efficiency of new technology / efficiency of old technology)
                    fuel_consid_eff = fuel_diff * (eff_tech_remove / eff_install) #FROZEN
                    #print("Technology fuel factor difference: " + str(eff_tech_remove) + "   " + str(eff_install) + "  " + str(eff_install / eff_tech_remove))

                    # Substract replaced fuel
                    fuel_switch_array[int(fuel_type)] = fuel_switch_array[int(fuel_type)] - fuel_diff # substract acutal fuel share

                    # Add new fuel
                    fuel_switch_array[tech_install_fueltype] += fuel_consid_eff # Add new calculated fuel amount

            #print("Old Fuel: " + str(self.reg_fuel_eff_gains))
            #print("--")
            ##print("New Fuel: " + str(fuel_switch_array))
            #prnt("..")
            return fuel_switch_array

    def enduse_scenario_driver(self):
        """The fuel data for every end use are multiplied with respective scenario driver

        If no building specific scenario driver is found, the identical fuel is returned.

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
        print(self.data['dw_stock'])
        # Test if enduse has a building related scenario driver
        if hasattr(self.data['dw_stock'][self.reg_id][self.base_year], self.enduse) and self.current_yr != self.base_year:

            # Scenariodriver of building stock base year and new stock
            by_driver = getattr(self.data['dw_stock'][self.reg_id][self.base_year], self.enduse) # Base year building stock
            cy_driver = getattr(self.data['dw_stock'][self.reg_id][self.current_yr], self.enduse) # Current building stock
            print("...")
            print(self.enduse)
            print(by_driver)
            print(cy_driver)
            print(self.reg_fuel_after_elasticity)
            factor_driver =  cy_driver / by_driver # FROZEN Here not effecieicny but scenario parameters!   base year / current (checked) (as in chapter 3.1.2 EQ E-2)
            return self.reg_fuel_after_elasticity * factor_driver

        else: # This fuel is not changed by building related scenario driver
            print("this enduse has not driver or is base year: " + str(self.enduse))
            return self.reg_fuel_after_elasticity

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
        fuels_d_peak = np.zeros((len(self.reg_fuel), 1))
        #print("...ddd")
        #print(self.enduse)
        #print(self.reg_fuelscen_driver)
        #print("---")
        #print(self.enduse_shape_peak_d)

        # Iterate yearday and
        for k, fueltype_year_data in enumerate(self.reg_fuelscen_driver):
            fuels_d_peak[k] = self.enduse_shape_peak_d * fueltype_year_data[0]
            #print("elf.enduse_shape_peak_d * fueltype_year_data[0]")
            #print(self.enduse_shape_peak_d * fueltype_year_data[0])

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
                fuels_h_peak[k][day] = self.enduse_shape_peak_h * fuel_data[day]

        return fuels_h_peak

class Country_residential_model(object):
    """Class of a country containing all regions for the different enduses

    The main class of the residential model. For every region, a Region object needs to be generated.

    Parameters
    ----------
    reg_id : int
        The ID of the region. The actual region name is stored in `reg_lu`

    Notes
    -----
    this class has as many attributes as regions (for evry rgion an attribute)
    """
    def __init__(self, sub_reg_names, data, data_ext):
        """Constructor of the class which holds all regions of a country"""
        self.data = data
        self.data_ext = data_ext
        self.sub_reg_names = sub_reg_names

        self.create_regions() #: create object for every region
        self.tot_country_fuel = self.get_overall_sum()
        self.tot_country_fuel_enduse_specific = self.get_sum_for_each_enduse()

        n = 0
        for i in self.tot_country_fuel_enduse_specific:
            n += self.tot_country_fuel_enduse_specific[i]
        #print("============================ddddddddddd= " + str(self.tot_country_fuel))
        #print("===========================ddddddddddd== " + str(n))
        # TESTING
        test_sum = 0
        for enduse in self.tot_country_fuel_enduse_specific:
            test_sum += self.tot_country_fuel_enduse_specific[enduse]
        np.testing.assert_almost_equal(np.sum(self.tot_country_fuel), test_sum, decimal=5, err_msg='', verbose=True)


    def create_regions(self):
        """Create all regions and add them as attributes based on region name to this class"""
        for reg_name in self.sub_reg_names:
            reg_object = Region(reg_name, self.data, self.data_ext) # Region object
            Country_residential_model.__setattr__(self, str(reg_name), reg_object) # Create an atribute for every regions ()

    def get_overall_sum(self):
        """Collect hourly data from all regions and sum across all fuel types and enduses"""
        tot_sum = 0
        for reg_id in self.data['reg_lu']:
            reg_object = getattr(self, str(reg_id)) # Get region

            # Get fuel data of region #Sum hourly demand # could also be read out as houly
            tot_sum += np.sum(getattr(reg_object, 'fuels_tot_enduses_h'))

        return tot_sum

    def get_sum_for_each_enduse(self):
        """Collect end_use specific hourly data from all regions and sum across all fuel types

        out: {enduse: sum(all_fuel_types)}

        """

        tot_sum_enduses = {}
        for enduse in self.data['resid_enduses']:
            tot_sum_enduses[enduse] = 0

        for reg_id in self.data['reg_lu']:
            reg_object = getattr(self, str(reg_id)) # Get region

            # Get fuel data of region
            enduse_fuels_reg = getattr(reg_object, 'fuels_new_enduse_specific')
            for enduse in enduse_fuels_reg:
                tot_sum_enduses[enduse] += np.sum(enduse_fuels_reg[enduse]) # sum across fuels

        return tot_sum_enduses

class Region(object):
    """Class of a region for the residential model

    The main class of the residential model. For every region, a Region object needs to be generated.

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
        """Constructor or Region
        # All calculatiosn are basd on driver_fuel_fuel_data #TODO
        #TODO: ITERATE OVER RESID ENDUSE DICT AND NOT FUELS
        """
        self.reg_id = reg_id                                        # ID of region
        self.data = data                                            # data
        self.data_ext = data_ext                                    # external data
        self.assumptions = data['assumptions']
        self.current_yr = data_ext['glob_var']['current_yr']        # Current year
        self.reg_fuel = data['fueldata_disagg'][reg_id]             # Fuel array of region (used to extract all end_uses)

        # Set attributs of all enduses
        self.create_enduse_objects()

        # Sum final 'yearly' fuels (summarised over all enduses)
        self.fuels_new = self.tot_all_enduses_y()
        self.fuels_new_enduse_specific = self.enduse_specific_y() #each enduse individually
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%YEAR: " + str(self.current_yr) + "  data  " + str(np.sum(self.fuels_new)))
        f = 0
        for i in self.fuels_new_enduse_specific:
            f += np.sum(self.fuels_new_enduse_specific[i])
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%YEAR22: " + str(self.current_yr) + "  data  " + str(f))
        #prnt(".l.")

        # Get 'peak demand day' (summarised over all enduses)
        self.fuels_peak_d = self.get_enduse_peak_d()

        # Get 'peak demand h' (summarised over all enduses)
        self.fuels_peak_h = self.get_enduse_peak_h()

        # Sum 'daily' demand in region (summarised over all enduses)
        self.fuels_tot_enduses_d = self.tot_all_enduses_d()

        # Sum 'hourly' demand in region (summarised over all enduses)
        self.fuels_tot_enduses_h = self.tot_all_enduses_h()

        # Calculate load factors from peak values
        self.reg_load_factor_d = self.load_factor_d()
        self.reg_load_factor_h = self.load_factor_h()

        # Calculate load factors from non peak values
        self.reg_load_factor_d_non_peak = self.load_factor_d_non_peak()
        self.reg_load_factor_h_non_peak = self.load_factor_h_non_peak()

        # Plot stacked end_uses
        #start_plot = mf.convert_date_to_yearday(2015, 1, 1) #regular day
        #fueltype_to_plot, nr_days_to_plot = 2, 1
        #self.plot_stacked_regional_end_use(nr_days_to_plot, fueltype_to_plot, start_plot, self.reg_id) #days, fueltype

        # Testing
        np.testing.assert_almost_equal(np.sum(self.fuels_tot_enduses_d), np.sum(self.fuels_tot_enduses_h), err_msg='The Regional disaggregation from d to h is false')

        test_sum = 0
        for enduse in self.fuels_new_enduse_specific:
            test_sum += np.sum(self.fuels_new_enduse_specific[enduse])
        np.testing.assert_almost_equal(np.sum(self.fuels_new), test_sum, err_msg='Summing end use specifid fuels went wrong')
        # TODO: add some more

    def create_enduse_objects(self):
        """All enduses are initialised and inserted as an attribute of the Region Class"""

        # Iterate enduses
        for enduse in self.data['resid_enduses']:
            enduse_obj = EndUseClassResid(self.reg_id, self.data, self.data_ext, enduse, self.reg_fuel) # Enduse object
            Region.__setattr__(self, enduse, enduse_obj) # Set attribute

    def tot_all_enduses_y(self):
        """Sum all fuel types over all end uses"""
        sum_fuels = np.zeros((len(self.data['fuel_type_lu']), 1)) # Initialise

        for enduse in self.data['resid_enduses']:
            sum_fuels += self.__getattr__subclass__(enduse, 'reg_fuelscen_driver') # Fuel of Enduse

        return sum_fuels

    def enduse_specific_y(self):
        """Sum fuels for every fuel type for each enduse"""

        # Initialise
        sum_fuels_all_enduses = {}
        for enduse in self.data['resid_enduses']:
            sum_fuels_all_enduses[enduse] = np.zeros((len(self.data['fuel_type_lu']), 1))

        # Sum data
        for enduse in self.data['resid_enduses']:
            sum_fuels_all_enduses[enduse] += self.__getattr__subclass__(enduse, 'reg_fuelscen_driver') # Fuel of Enduse
        return sum_fuels_all_enduses

    def tot_all_enduses_d(self):
        """Calculate total daily fuel demand for each fueltype"""
        sum_fuels_d = np.zeros((len(self.data['fuel_type_lu']), 365))  # Initialise

        for enduse in self.data['resid_enduses']:
            sum_fuels_d += self.__getattr__subclass__(enduse, 'reg_fuel_d')

        return sum_fuels_d

    def get_enduse_peak_d(self):
        """Summarise absolute fuel of peak days over all end_uses"""
        sum_enduse_peak_d = np.zeros((len(self.data['fuel_type_lu']), 1))  # Initialise

        for enduse in self.data['resid_enduses']:
            sum_enduse_peak_d += self.__getattr__subclass__(enduse, 'enduse_fuel_peak_d') # Fuel of Enduse

        return sum_enduse_peak_d

    def get_enduse_peak_h(self):
        """Summarise peak value of all end_uses"""
        sum_enduse_peak_h = np.zeros((len(self.data['fuel_type_lu']), 1, 24)) # Initialise

        for enduse in self.data['resid_enduses']:
            sum_enduse_peak_h += self.__getattr__subclass__(enduse, 'enduse_fuel_peak_h') # Fuel of Enduse

        return sum_enduse_peak_h

    def tot_all_enduses_h(self):
        """Calculate total hourly fuel demand for each fueltype"""
        sum_fuels_h = np.zeros((len(self.data['fuel_type_lu']), 365, 24)) # Initialise

        for enduse in self.data['resid_enduses']:
            sum_fuels_h += self.__getattr__subclass__(enduse, 'enduse_fuel_h') #np.around(fuel_end_use_h,10)

        # Read out more error information (e.g. RuntimeWarning)
        #np.seterr(all='raise') # If not round, problem....np.around(fuel_end_use_h,10)
        return sum_fuels_h

    def load_factor_d(self):
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
        lf_d = np.zeros((len(self.data['fuel_type_lu']), 1))

        # Get day with maximum demand (in percentage of year)
        peak_d_demand = self.fuels_peak_d

        # Iterate fueltypes to calculate load factors for each fueltype
        for k, fueldata in enumerate(self.fuels_tot_enduses_d):
            average_demand = np.sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days

            if average_demand != 0:
                lf_d[k] = average_demand / peak_d_demand[k] # Calculate load factor

        lf_d = lf_d * 100 # Convert load factor to %
        return lf_d

    def load_factor_h(self):
        """Calculate load factor of a h in a year from peak data (peak hour compared to all hours in a year)

        self.fuels_peak_h     :   Fuels for peak day (fueltype, data)
        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

        Return
        ------
        lf_h : array
            Array with load factor for every fuel type [in %]

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        lf_h = np.zeros((len(self.data['fuel_type_lu']), 1)) # Initialise array to store fuel

        # Iterate fueltypes to calculate load factors for each fueltype
        for fueltype, fueldata in enumerate(self.fuels_tot_enduses_h):

            # Maximum fuel of an hour of the peak day
            maximum_h_of_day = np.amax(self.fuels_peak_h[fueltype])

            #Calculate average in full year
            all_hours = []
            for day_hours in self.fuels_tot_enduses_h[fueltype]:
                for h in day_hours:
                    all_hours.append(h)
            average_demand_h = sum(all_hours) / (365 * 24) # Averae load = yearly demand / nr of days

            # If there is a maximum day hour
            if maximum_h_of_day != 0:
                average_demand_h = np.sum(fueldata) / (365 * 24) # Averae load = yearly demand / nr of days
                lf_h[fueltype] = average_demand_h / maximum_h_of_day # Calculate load factor

        lf_h = lf_h * 100 # Convert load factor to %

        return lf_h

    def load_factor_d_non_peak(self):
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
        lf_d = np.zeros((len(self.data['fuel_type_lu']), 1))

        # Iterate fueltypes to calculate load factors for each fueltype
        for k, fueldata in enumerate(self.fuels_tot_enduses_d):

            average_demand = sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days
            max_demand_d = max(fueldata)

            if  max_demand_d != 0:
                lf_d[k] = average_demand / max_demand_d # Calculate load factor

        lf_d = lf_d * 100 # Convert load factor to %
        return lf_d

    def load_factor_h_non_peak(self):
        """Calculate load factor of a h in a year from non-peak data

        self.fuels_peak_h     :   Fuels for peak day (fueltype, data)
        self.fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

        Return
        ------
        lf_h : array
            Array with load factor for every fuel type [in %]

        Info
        -----
        Load factor = average load / maximum load in given time period

        Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
        """
        lf_h = np.zeros((len(self.data['fuel_type_lu']), 1)) # Initialise array to store fuel

        # Iterate fueltypes to calculate load factors for each fueltype
        for fueltype, fueldata in enumerate(self.fuels_tot_enduses_h):

            all_hours = []
            for day_hours in self.fuels_tot_enduses_h[fueltype]:
                for h in day_hours:
                    all_hours.append(h)
            maximum_h_of_day_in_year = max(all_hours)

            average_demand_h = np.sum(fueldata) / (365 * 24) # Averae load = yearly demand / nr of days

            # If there is a maximum day hour
            if maximum_h_of_day_in_year != 0:
                lf_h[fueltype] = average_demand_h / maximum_h_of_day_in_year # Calculate load factor

        lf_h = lf_h * 100 # Convert load factor to %

        return lf_h


    def __getattr__(self, attr):
        """Get method of own object"""
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
        Y_init = np.zeros((len(self.reg_fuel), nr_hours_to_plot))

        # Iterate enduse
        for k, enduse in enumerate(self.reg_fuel):
            legend_entries.append(enduse)
            sum_fuels_h = self.__getattr__subclass__(enduse, 'enduse_fuel_h') #np.around(fuel_end_use_h,10)

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
        Y_init = np.zeros((len(self.reg_fuel), nr_hours_to_plot))

        # Iterate enduse
        for k, enduse in enumerate(self.reg_fuel):
            legend_entries.append(enduse)
            sum_fuels_h = self.__getattr__subclass__(enduse, 'enduse_fuel_h') #np.around(fuel_end_use_h,10)

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