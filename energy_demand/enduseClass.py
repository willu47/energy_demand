"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103,C0325,no-member
import sys
import numpy as np
import energy_demand.main_functions as mf
import unittest
import copy
assertions = unittest.TestCase('__init__')


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
    enduse : str
        Enduse given in a string
    enduse_fuel : array
        Fuel data for the region the endu
    fuel_shape_heating : array
        Service shape for space heating (yh)
    enduse_peak_yd_factor : float
        Peak yd factor of enduse

    Info
    ----
    Every enduse can only have on shape independently of the fueltype

    `self.enduse_fuel_new_fuel` is always overwritten in the cascade of fuel calculations

    Problem: Not all enduses have technologies assigned. Therfore peaks are derived from techstock in case there are technologies,
    otherwise enduse load shapes are used.
    """
    def __init__(self, reg_name, data, enduse, enduse_fuel, tech_stock, heating_factor_y, cooling_factor_y, fuel_shape_heating, enduse_peak_yd_factor):
        self.enduse = enduse
        self.enduse_specific_fuel_switches_crit = self.get_enduse_fuel_switches(data['assumptions']['resid_fuel_switches']) # Get fuel switches in enduse
        self.enduse_specific_service_switch_crit = self.get_enduse_service_switches(data['assumptions']['service_switch_enduse_crit'])
        self.enduse_fuel = enduse_fuel[enduse]

        # Get technologies of enduse depending on assumptions on fuel switches or service switches
        if self.enduse_specific_fuel_switches_crit:
            print("...Fuel switch yes")
            self.technologies_enduse = self.get_technologies_fuel_switch(data['assumptions']['fuel_enduse_tech_p_by']) # Get all technologies of enduse
        elif self.enduse_specific_service_switch_crit:
            print("...Service switch")
            self.technologies_enduse = self.get_technologies_service_switch(data['assumptions']['service_tech_by_p'][self.enduse]) # Get all technologies of enduse
        else:
            # If no fuel switch and no service switch, read out base year technologies
            self.technologies_enduse = self.get_technologies_from_fuel_definition(data['assumptions']['fuel_enduse_tech_p_by'][self.enduse])


        # --------
        # Testing
        # --------
        if self.enduse_specific_fuel_switches_crit and self.enduse_specific_service_switch_crit:
            sys.exit("Error: Can't define service switch and fuel switch for enduse '{}' {}   {}".format(self.enduse, self.enduse_specific_fuel_switches_crit, self.enduse_specific_service_switch_crit))
        if self.enduse not in data['shapes_resid_yd'] and self.technologies_enduse == []:
            sys.exit("Error: The enduse is not defined with technologies and no generic yd shape is provided for the enduse '{}' ".format(self.enduse))

        # -------------------------------
        # Yearly fuel calculation cascade
        # --------------------------------
        self.enduse_fuel_new_fuel = copy.deepcopy(self.enduse_fuel)
        print("Fuel train A: " + str(np.sum(self.enduse_fuel_new_fuel)))

        # Change fuel consumption based on climate change induced temperature differences
        self.temp_correction_hdd_cdd(cooling_factor_y, heating_factor_y)
        print("Fuel train B: " + str(np.sum(self.enduse_fuel_new_fuel)))

        # Calcualte smart meter induced general savings
        self.smart_meter_eff_gain(data['data_ext'], data['assumptions'])
        print("Fuel train C: " + str(np.sum(self.enduse_fuel_new_fuel)))

        # Enduse specific consumption change in % (due e.g. to other efficiciency gains). No technology considered
        self.enduse_specific_change(data['data_ext'], data['assumptions'])
        print("Fuel train D: " + str(np.sum(self.enduse_fuel_new_fuel)))

        # Calculate new fuel demands after scenario drivers
        self.enduse_building_stock_driver(data, reg_name)
        print("Fuel train E: " + str(np.sum(self.enduse_fuel_new_fuel)))

        # Calculate demand with changing elasticity (elasticity maybe on household level with floor area)
        self.enduse_elasticity(data['data_ext'], data['assumptions'])
        print("Fuel train F: " + str(np.sum(self.enduse_fuel_new_fuel)))


        # ----------------------------------
        # Hourly fuel calcualtions cascade
        # ----------------------------------
        # Check if enduse is defined with technologies
        if self.technologies_enduse != []:
            print("Enduse {} is defined.... ".format(self.enduse) + str(self.technologies_enduse))

            # Get corret energy service shape of enduse
            if self.enduse == 'resid_space_heating' or self.enduse == 'service_space_heating': #in data['assumptions']['enduse_resid_space_heating']: # Residential space heating
                service_shape_yh = fuel_shape_heating
            '''elif self.enduse in data['assumptions']['enduse_resid_cooking']: # -- COOKING (# SCRAP)
                service_shape_yh_all_fueltypes = self.enduse_y_to_d(self.enduse_fuel_new_fuel, data['shapes_resid_yd'][self.enduse]['shape_non_peak_yd'])
                service_shape_yh = np.zeros((365, 24))
                for fuel_fueltype in service_shape_yh_all_fueltypes:
                    service_shape_yh += fuel_fueltype
                service_shape_yh = (1 / np.sum(service_shape_yh)) * service_shape_yh
            #elif self.enduse == 'resid_cooling':
            #    service_shape_yh =
            # else:
            '''
            print("inid")
            # Calculate energy service (across all fueltypes for base year)
            tot_service_h_by, service_tech = mf.calc_regional_service_demand(service_shape_yh, data['assumptions']['fuel_enduse_tech_p_by'][self.enduse], self.enduse_fuel_new_fuel, tech_stock)
            #print("Service Sum -1: " + str(np.sum(tot_service_h_by)))
            #for tech in service_tech:
            #    print("tech: " + str(tech) + "  " + str(np.sum(service_tech[tech])))

            '''summe = 0
            for tech in service_tech:
                summe += np.sum(service_tech[tech])
                print("Tech: " + str(tech) + str("  ") + str(np.sum(service_tech[tech])))

            print("Service Sum 0:   " + str(summe))
            print("TOTSUM:          " + str(np.sum(tot_service_h_by)))
            '''
            for tech in service_tech:
                print("tech: " + str(tech) + "  " + str(np.sum(service_tech[tech])))

            # ----------------
            # Service Switches
            # ----------------
            if self.enduse_specific_service_switch_crit:
                service_tech = self.switch_tech_service(data, tot_service_h_by)

            print("---------------")
            for tech in service_tech:
                print("astertech: " + str(tech) + "  " + str(np.sum(service_tech[tech])))

            # ----------------
            # Fuel Switches
            # ----------------
            if self.enduse_specific_fuel_switches_crit:
                service_tech = self.switch_tech_fuel(data['data_ext'], data['assumptions'], tot_service_h_by, service_tech)

            #summe = 0
            #for tech in service_tech:
            #    summe += np.sum(service_tech[tech])
            #print("Service Sum 1: " + str(summe))
            for tech in service_tech:
                print("outside: " + str(tech) + "  " + str(np.sum(service_tech[tech])))

            # -----------------------
            # Convert Service to Fuel
            # -----------------------
            # Convert energy service to fuel, Convert service to fuel for current year (y)
            self.enduse_service_to_fuel_fueltype_y(service_tech, tech_stock)
            print("Fuel train G: " + str(np.sum(self.enduse_fuel_new_fuel)))

            # Convert service to fuel for each technology depending on technological efficiences in current year
            enduse_fuel_tech = self.enduse_service_to_fuel_per_tech(service_tech, tech_stock)
            print("Fuel train H: " + str(np.sum(self.enduse_fuel_new_fuel)))

            summe = 0
            for tech in enduse_fuel_tech:
                summe += np.sum(service_tech[tech])
            print("TOTAL FUEL TO REDISRIBUTE " + str(summe))

            # --------
            # NON-PEAK
            # --------
            # Iterate technologies in enduse and assign technology specific shape for respective fuels
            self.enduse_fuel_yd = self.calc_enduse_fuel_tech_yd(enduse_fuel_tech, self.technologies_enduse, tech_stock)
            self.enduse_fuel_yh = self.calc_enduse_fuel_tech_yh(enduse_fuel_tech, self.technologies_enduse, tech_stock)
            #self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh)# Get maximum hour demand per fueltype
            print("Ssadf" + str(self.enduse_fuel_yd.shape))
            print("SUMME YH " + str(np.sum(self.enduse_fuel_yd)))
            print("SUMME YH " + str(np.sum(self.enduse_fuel_yh)))
            print("d YH " + str(np.sum(self.enduse_fuel_yd[0].shape)))
            print("d YH " + str(np.sum(self.enduse_fuel_yh[0].shape)))
            '''# --------
            # PEAK
            # --------
            #enduse_fuel_tech  enduse_fuel_new_fuel
            #self.enduse_fuel_peak_yd = self.calc_enduse_fuel_peak_yd_factor(self.enduse_fuel_new_fuel, enduse_peak_yd_factor)
            ##self.enduse_fuel_peak_yd = self.calc_enduse_fuel_tech_peak_yd_factor(data['lu_fueltype'], enduse_fuel_tech, enduse_peak_yd_factor, tech_stock)

            # Iterate technologies in enduse and assign technology specific shape for peak for respective fuels
            #self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_tech_yh(enduse_fuel_tech, self.technologies_enduse, tech_stock)
            self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_tech_yh(self.enduse_fuel_peak_yd, self.technologies_enduse, tech_stock)
            self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh) # Get maximum hour demand per fueltype
            '''

            # --------
            # PEAK (Peak is not defined by yd factor so far but read out from real data!) #TODO
            # --------
            # Iterate technologies in enduse and assign technology specific shape for peak for respective fuels
            self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_tech_yh(enduse_fuel_tech, self.technologies_enduse, tech_stock)
            self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh) # Get maximum hour demand per fueltype

        else: # No technologies specified in enduse
            print("enduse is not defined with technologies: " + str(self.enduse))

            # --Peak yd (peak day) (same for enduse for all technologies)
            self.enduse_fuel_peak_yd = self.calc_enduse_fuel_peak_yd_factor(self.enduse_fuel, enduse_peak_yd_factor)

            # --------
            # NON-PEAK
            # --------
            self.enduse_fuel_yd = self.enduse_y_to_d(self.enduse_fuel_new_fuel, data['shapes_resid_yd'][self.enduse]['shape_non_peak_yd'])
            self.enduse_fuel_yh = self.enduse_d_to_h(self.enduse_fuel_yd, data['shapes_resid_dh'][self.enduse]['shape_non_peak_h'])

            # --------
            # PEAK
            # --------
            self.enduse_fuel_peak_yh = self.calc_enduse_fuel_peak_yh(self.enduse_fuel_peak_yd, data['shapes_resid_dh'][enduse]['shape_peak_dh'])
            self.enduse_fuel_peak_h = self.get_peak_from_yh(self.enduse_fuel_peak_yh)

        # Testing
        np.testing.assert_almost_equal(np.sum(self.enduse_fuel_yd), np.sum(self.enduse_fuel_yh), decimal=2, err_msg='', verbose=True)

    def get_technologies_from_fuel_definition(self, fuel_enduse_tech_p_by):
        """Get all defined technologies from defined fuel shares in base year

        Parameters
        ----------
        fuel_enduse_tech_p_by : dict
            Fuel definition assumptions of base year

        Return
        ------
        technologies : list
            All technologies (no technolgy is added twice)
        """
        technologies = []
        for fueltype in fuel_enduse_tech_p_by:
            for tech in fuel_enduse_tech_p_by[fueltype].keys():
                if tech not in technologies:
                    technologies.append(tech)
        
        return technologies
    
    
    def switch_tech_service(self, data, tot_service_h_by):
        """Scenaric service switches

        All diminishing technologies are proportionally to base year share diminished.

        Paramters
        ---------
        data : dict
            Data
        tot_service_h_by : array
            Hourly service of all technologies
        tech_stock : object
            Technology stock

        Returns
        -------
        service_tech_cy : dict
            Current year fuel for every technology (e.g. fueltype 1: 'techA': fuel) for every hour
        """
        print("...Service switch is implemented")
        service_tech_cy_p = {}
        service_tech_cy = {}

        # Calculate diffusion of service for technology with increased service
        service_tech_increase_cy_p = self.get_service_diffusion(data, data['assumptions']['tech_increased_service'][self.enduse])

        # Add shares to output dict
        for tech_increase in service_tech_increase_cy_p:
            service_tech_cy_p[tech_increase] = service_tech_increase_cy_p[tech_increase]

        # Calculate proportional share of technologies with decreasing service of base year (distribution in base year)
        service_tech_decrease_by_rel = mf.get_service_rel_tech_decrease_by(data['assumptions']['tech_decreased_share'][self.enduse], data['assumptions']['service_tech_by_p'][self.enduse])

        # Add shares to output dict
        for tech_decrease in service_tech_decrease_by_rel:
            service_tech_cy_p[tech_decrease] = data['assumptions']['service_tech_by_p'][self.enduse][tech_decrease]

        # Iterate service switches for increase tech
        for tech_increase in service_tech_increase_cy_p:
            # Difference in service up to current year
            diff_service_increase = service_tech_increase_cy_p[tech_increase] - data['assumptions']['service_tech_by_p'][self.enduse][tech_increase]

            # Substract service gain proportionaly to all technologies which are lowered and substract from other technologies
            for tech_decrease in service_tech_decrease_by_rel:
                service_tech_cy_p[tech_decrease] -= service_tech_decrease_by_rel[tech_decrease] * diff_service_increase

        # Add all technologies with unchanged service in the future
        for tech_constant in data['assumptions']['tech_constant_share'][self.enduse]:
            service_tech_cy_p[tech_constant] = data['assumptions']['service_tech_by_p'][self.enduse][tech_constant]

        # Multiply share of each tech with hourly service
        for tech in service_tech_cy_p:
            service_tech_absolute = tot_service_h_by * service_tech_cy_p[tech]  # Total yearly hourly service * share of enduse
            service_tech_cy[tech] = service_tech_absolute

        return service_tech_cy

    def get_service_diffusion(self, data, tech_increased_service):
        """Calculate energy service fraction of technologies with increased service

        Parameters
        ----------
        data : dict
            Data
        tech_increased_service : dict
            All technologies per enduse with increased future service share

        Returns
        -------
        service_tech_cy_p : dict
            Share of service per technology of current year
        """
        service_tech_cy_p = {}

        for tech_installed in tech_increased_service:

            # Get service for current year based on sigmoid diffusion
            service_tech_cy_p[tech_installed] = mf.sigmoid_function(
                data['data_ext']['glob_var']['curr_yr'],
                data['assumptions']['sigm_parameters_tech'][self.enduse][tech_installed]['l_parameter'],
                data['assumptions']['sigm_parameters_tech'][self.enduse][tech_installed]['midpoint'],
                data['assumptions']['sigm_parameters_tech'][self.enduse][tech_installed]['steepness']
            )

        return service_tech_cy_p

    def get_enduse_fuel_switches(self, fuelswitches):
        """Test whether there is a fuelswitch for this enduse
        """
        fuel_switches_enduse = []

        for fuelswitch in fuelswitches:
            if fuelswitch['enduse'] == self.enduse:
                fuel_switches_enduse.append(fuelswitch)

        if fuel_switches_enduse != []:
            return True
        else:
            return False

    def get_enduse_service_switches(self, service_switch_crit):
        """Test wheter there are defined service switches for this enduse
        """
        #if self.enduse in service_tech_by_p:
        try:
            if service_switch_crit[self.enduse]:
                return True
            else:
                return False
        except: # If the enduse is not defined
            return False

    def get_peak_from_yh(self, enduse_fuel_peak_yh):
        """Iterate yearly fuels and select day with most fuel
        """
        peak_fueltype_h = np.zeros((enduse_fuel_peak_yh.shape[0]))

        for fueltype, fuel_yh in enumerate(enduse_fuel_peak_yh):
            max_fuel_h = np.max(fuel_yh) # Get hour with maximum fuel_yh
            peak_fueltype_h[fueltype] = max_fuel_h # add
        return peak_fueltype_h

    def calc_enduse_fuel_peak_tech_yh(self, enduse_fuel_tech, technologies_enduse, tech_stock):
        """Calculate peak demand

        The daily peak is assumed to be the same in an enduse for all technologies

        From daily to hourly with hourly specific peak shape

        The peak is calculated for every fueltype (fueltype specfici)
        """

        # TODO HYBRID: 
        peak_day = 100 # Define peak day

        enduse_fuel_peak_yh = np.zeros((self.enduse_fuel_new_fuel.shape[0], 365, 24))

        for tech in technologies_enduse:
            fuel_tech_peak_dh = enduse_fuel_tech[tech] * tech_stock.get_tech_attribute(tech, 'shape_peak_dh') # Multiply fuel with shape_peak_dh

            fueltypes_tech_p = tech_stock.get_tech_attribute(tech, 'fuel_types_share_yd') # Get fueltype of tech HYBRID DONE

            for fueltype, fueltype_share_d in enumerate(fueltypes_tech_p):
                fuel_fueltype_tech_peak_dh = fuel_tech_peak_dh * fueltype_share_d[peak_day]
                enduse_fuel_peak_yh[fueltype] += fuel_fueltype_tech_peak_dh # Add fuel of day

        return enduse_fuel_peak_yh

    def get_technologies_fuel_switch(self, fuel_enduse_tech_p_by):
        """Iterate assumptions about technologes in enduses of base year for each enduse
        """
        # Get all technologies of enduse
        technologies_enduse = []
        for fueltype in fuel_enduse_tech_p_by[self.enduse]:
            for tech in fuel_enduse_tech_p_by[self.enduse][fueltype]:
                technologies_enduse.append(tech)

        return technologies_enduse

    def get_technologies_service_switch(self, enduse_tech_shares):
        """Iterate assumptions about services and get technologies
        """
        # Get all technologies of enduse
        technologies_enduse = enduse_tech_shares.keys()
        return technologies_enduse

    def calc_enduse_fuel_tech_yd(self, enduse_fuel_tech, technologies_enduse, tech_stock):
        """Iterate fuels for each technology and assign shape d
        """
        fuels_fueltype_d = np.zeros((self.enduse_fuel_new_fuel.shape[0], 365))
        control_sum = 0

        for tech in technologies_enduse:

            # Multiply fuel with shape_yd
            fuel_tech_yd = enduse_fuel_tech[tech] * tech_stock.get_tech_attribute(tech, 'shape_yd')

            # Testing
            np.testing.assert_array_almost_equal(np.sum(fuel_tech_yd), np.sum(enduse_fuel_tech[tech]), decimal=3, err_msg="Error NR XXX")

            fueltype_tech_share_yd = tech_stock.get_tech_attribute(tech, 'fuel_types_share_yd') # Get fueltype of tech HYBRID DONE check

            for fueltype_hybrid, fuel_shares_dh in enumerate(fueltype_tech_share_yd):
                fuel_per_fueltype_dh = fuel_tech_yd * fuel_shares_dh
                fuels_fueltype_d[fueltype_hybrid] += fuel_per_fueltype_dh

                control_sum += np.sum(fuel_per_fueltype_dh)
                #print("new fuel " + str(np.sum(fuel_per_fueltype_dh)))
                #print(np.sum(fuels_fueltype_d))
                #print(control_sum)

        # Assert --> If this assert is done, then we need to substract the fuel from yearly data and run function:  enduse_service_to_fuel_fueltype_y
        #np.testing.assert_array_almost_equal(np.sum(fuels_fueltype_d), np.sum(control_sum), decimal=2, err_msg="Error: The y to h fuel did not work")

        np.testing.assert_array_almost_equal(sum(enduse_fuel_tech.values()), np.sum(control_sum), decimal=2, err_msg="Error: The y to h fuel did not work")

        return fuels_fueltype_d

    def calc_enduse_fuel_tech_yh(self, enduse_fuel_tech, technologies_enduse, tech_stock):
        """Iterate fuels for each technology and assign shape yh
        """
        fuels_fueltype_yh = np.zeros((self.enduse_fuel_new_fuel.shape[0], 365, 24))
        control_sum = 0

        for tech in technologies_enduse:
            '''fuel_tech = enduse_fuel_tech[tech] # Get fuel of technology
            fuel_tech_yh = fuel_tech * tech_stock.get_tech_attribute(tech, 'shape_yh') # Multiply fuel with shape_h
            fueltype_tech = tech_stock.get_tech_attribute(tech, 'fuel_type') # Get fueltype of tech
            fuels_fueltype_yh[fueltype_tech] += fuel_tech_yh # Add fuel
            control_sum += fuel_tech_yh
            '''

            # NEW
            fuel_tech = enduse_fuel_tech[tech] # Get fuel of technology
            fueltype_tech_share_yh = tech_stock.get_tech_attribute(tech, 'fueltypes_p_cy') #fueltypes_fraction_yh') # Get fueltype of tech HYBRID DONE fueltypes_p_cy

            for fueltype_hybrid, fuel_tech_share in enumerate(fueltype_tech_share_yh):
                # Shape of fuel of technology #TODO: For every fueltype
                fuel_tech_yh = tech_stock.get_tech_attribute(tech, 'shape_yh') * fuel_tech #SO FAR FOR ALL FUELTYPES THE SAME

                fuels_fueltype_yh[fueltype_hybrid] += fuel_tech_share * fuel_tech_yh # Share of fuel of fueltype_hybrid * fuel
                control_sum += fuel_tech_share * fuel_tech_yh

        # Assert --> If this assert is done, then we need to substract the fuel from yearly data and run function:  enduse_service_to_fuel_fueltype_y
        np.testing.assert_array_almost_equal(np.sum(fuels_fueltype_yh), np.sum(control_sum), decimal=2, err_msg="Error: The y to h fuel did not work")
        return fuels_fueltype_yh

    def switch_tech_fuel(self, data_ext, assumptions, tot_service_h_by, service_tech):
        """Scenaric fuel switches

        Based on assumptions about shares of fuels which are switched per enduse to specific
        technologies, the installed technologies are used to calculate the new service demand
        after switching fuel shares.

        Parameters
        ----------
        data_ext : dict
            Data
        assumptions : dict
            Assumptions
        tot_service_h_by : dict
            Service for every hour
        service_tech : dict
            Service for every fueltype and technology

        Returns
        -------
        service_tech_after_switch : dict
            Containing all service for each technology on a hourly basis
        """
        print("... fuel_switch is implemented")
        # Make copy to calculate fuel percentages within fueltype after switch
        service_tech_after_switch = copy.deepcopy(service_tech)

        # Iterate all technologies which are installed in fuel switches
        for tech_installed in assumptions['installed_tech'][self.enduse]:
            #print("-----------Tech_installed:  "  + str(tech_installed))

            # Read out sigmoid diffusion of energy service demand of this technology for the current year
            diffusion_cy = mf.sigmoid_function(data_ext['glob_var']['curr_yr'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['l_parameter'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['midpoint'], assumptions['sigm_parameters_tech'][self.enduse][tech_installed]['steepness'])
            #print("diffusion_cy  " + str(diffusion_cy))

            # Get difference in hourly service based on diffusion of installed technology
            service_tech_installed_cy = (diffusion_cy * tot_service_h_by) - service_tech[tech_installed]

            # Get service for current year for technologies
            #print("service_tech_installed_cy: " + str(np.sum(service_tech_installed_cy)))
            service_tech_after_switch[tech_installed] += service_tech_installed_cy

            # Remove fuel of replaced energy service demand proportinally to heat demand in base year
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
                        break # switch is found

                # Get all technologies which are installed
                technologies_in_fueltype = assumptions['fuel_enduse_tech_p_by'][self.enduse][fueltype].keys()

                # Iterate all technologies in within the fueltype and calculate reduction per technology
                for technology_replaced in technologies_in_fueltype:

                    # Share of heat demand for technology in fueltype (share of heat demand within fueltype * reduction in servide demand)
                    service_demand_tech = assumptions['service_fueltype_tech_p'][self.enduse][fueltype][technology_replaced] * reduction_service_fueltype

                    # Substract technology specific servide demand
                    #print("service_demand_tech: " + str(np.sum(service_demand_tech)))
                    service_tech_after_switch[technology_replaced] -= service_demand_tech

        return service_tech_after_switch

    def enduse_service_to_fuel_fueltype_y(self, service_tech, tech_stock):
        """Convert energy service to yearly fuel

        For every technology the service is taken and converted to fuel based on efficiency of current year

        Inputs
        ------
        service_tech : dict
            Service per fueltype and technology
        tech_stock : object
            Technological stock

        Info
        -----
        Fuel = Energy service / efficiency
        """
        # Initialise with all fuetlypes
        enduse_fuels = np.zeros((self.enduse_fuel_new_fuel.shape))

        # Convert service to fuel
        for tech in service_tech:
            print("---------")
            print("SERVICE TO CONVERT: {}  ".format(tech) + str(np.sum(service_tech[tech])))
            '''
            fuel_tech = np.divide(service_tech[tech], tech_stock.get_tech_attribute(tech, 'eff_cy'))
            fueltype = tech_stock.get_tech_attribute(tech, 'fuel_type')
            enduse_fuels[fueltype] += np.sum(fuel_tech)
            print("Convert service to fuel: " + str(tech) + str("  ") + str(np.sum(service_tech[tech])) + str("  ") + str(np.sum(fuel_tech)))
            '''
            # Calculate fuels (divide by efficiency)
            fuel_tech = np.divide(service_tech[tech], tech_stock.get_tech_attribute(tech, 'eff_cy'))
            print("fuel_tech: " + str(np.sum(fuel_tech)))
            fueltype_share_yh = tech_stock.get_tech_attribute(tech, 'fueltypes_p_cy')

            for fueltype, _ in enumerate(fueltype_share_yh):
                fuel_fueltype = fueltype_share_yh[fueltype] * fuel_tech
                print("-- " + str(np.sum(fuel_fueltype)))
                enduse_fuels[fueltype] += np.sum(fuel_fueltype) # Share of fuel of fueltype_hybrid * fuel 

        setattr(self, 'enduse_fuel_new_fuel', enduse_fuels)

    def enduse_service_to_fuel_per_tech(self, service_tech, tech_stock):
        """Calculate percent of fuel for each technology within fueltype considering current efficiencies

        Parameters
        ----------
        service_tech : dict
            Assumptions of share of fuel of base year
        tech_stock : object
            Technology stock

        Returns
        -------
        fuel_tech : dict
            Fuels per technology (the fueltype is given through technology)

        Info
        -----
        Fuel = Energy service / efficiency
        """
        fuel_tech = {} # Initialise with all fuetlypes

        # Convert service to fuel
        for tech in service_tech:
            fuel = np.divide(service_tech[tech], tech_stock.get_tech_attribute(tech, 'eff_cy'))
            fuel_tech[tech] = np.sum(fuel) #DDD Alle Fuels zusammengefasst unspezifisch

        return fuel_tech

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
        percent_ey = assumptions['enduse_overall_change_ey'][self.enduse] # Percent of fuel consumption in end year
        percent_by = 1.0 # Percent of fuel consumption in base year (always 100 % per definition)
        diff_fuel_consump = percent_ey - percent_by # Percent of fuel consumption difference
        diffusion_choice = assumptions['other_enduse_mode_info']['diff_method'] # Diffusion choice

        if diff_fuel_consump != 0: # If change in fuel consumption
            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0])) # fueltypes, days, hours

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
        new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0]))

        if self.enduse == 'resid_space_heating':
            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                new_fuels[fueltype] = fuel * heating_factor_y
            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

        elif self.enduse == 'cooling':
            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                new_fuels[fueltype] = fuel * cooling_factor_y
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

            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0])) #fueltypes, days, hours

            # End use elasticity
            elasticity_enduse = assumptions['resid_elasticities'][self.enduse]

            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):

                if fuel != 0: # if fuel exists
                    fuelprice_by = data_ext['fuel_price'][data_ext['glob_var']['base_yr']][fueltype] # Fuel price by
                    fuelprice_cy = data_ext['fuel_price'][data_ext['glob_var']['curr_yr']][fueltype] # Fuel price ey
                    new_fuels[fueltype] = mf.apply_elasticity(fuel, elasticity_enduse, fuelprice_by, fuelprice_cy)
                else:
                    new_fuels[fueltype] = fuel

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
            new_fuels = np.zeros((self.enduse_fuel_new_fuel.shape[0])) #fueltypes, fuel

            # Sigmoid diffusion up to current year
            sigm_factor = mf.sigmoid_diffusion(data_ext['glob_var']['base_yr'], data_ext['glob_var']['curr_yr'], data_ext['glob_var']['end_yr'], assumptions['sig_midpoint'], assumptions['sig_steeppness'])

            # Smart Meter penetration (percentage of people having smart meters)
            penetration_by = assumptions['smart_meter_p_by']
            penetration_cy = assumptions['smart_meter_p_by'] + (sigm_factor * (assumptions['smart_meter_p_ey'] - assumptions['smart_meter_p_by']))

            for fueltype, fuel in enumerate(self.enduse_fuel_new_fuel):
                saved_fuel = fuel * (penetration_by - penetration_cy) * assumptions['general_savings_smart_meter'][self.enduse] # Saved fuel
                new_fuels[fueltype] = fuel - saved_fuel # New fuel

            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def enduse_building_stock_driver(self, data, reg_name):
        """The fuel data for every end use are multiplied with respective scenario driver

        If no building specific scenario driver is found, the identical fuel is returned.

        The HDD is calculated seperately!

        Parameters
        ----------
        data : dict
            Data
        reg_name : str
            Region
        
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
        if hasattr(data['dw_stock'][reg_name][data['data_ext']['glob_var']['base_yr']], self.enduse) and data['data_ext']['glob_var']['curr_yr'] != data['data_ext']['glob_var']['base_yr']:

            # Scenariodriver of building stock base year and new stock
            by_driver = getattr(data['dw_stock'][reg_name][data['data_ext']['glob_var']['base_yr']], self.enduse) # Base year building stock
            cy_driver = getattr(data['dw_stock'][reg_name][data['data_ext']['glob_var']['curr_yr']], self.enduse) # Current building stock

            # base year / current (checked) (as in chapter 3.1.2 EQ E-2)
            factor_driver = np.divide(cy_driver, by_driver) # TODO: FROZEN Here not effecieicny but scenario parameters

            new_fuels = new_fuels * factor_driver

            setattr(self, 'enduse_fuel_new_fuel', new_fuels)

    def enduse_y_to_d(self, fuels, enduse_shape_yd):
        """Generate array with fuels for every day

        Parameters
        ----------
        fuels : array
            Yearly fuel data
        enduse_shape_yd : array
            Shape of enduse yd

        Returns
        -------
        fuels_d : array
            Hourly fuel data (365, 1)

        """
        fuels_d = np.zeros((fuels.shape[0], 365))

        for k, fuel in enumerate(fuels):
            fuels_d[k] = enduse_shape_yd * fuel
        
        #print("fuelsdd")
        #print(fuels)
        #print(np.sum(fuels_d))
        #assert np.sum(fuels) == np.sum(fuels_d)
        np.testing.assert_almost_equal(np.sum(fuels), np.sum(fuels_d), decimal=3, err_msg='The distribution of dwelling types went wrong', verbose=True)
        return fuels_d

    def enduse_d_to_h(self, fuels, enduse_shape_dh):
        """Disaggregate yearly fuel data to every day in the year

        Parameters
        ----------
        self : self
            Data from constructor
        enduse_shape_dh : array
            Shape of dh of every day (365, 24)

        Returns
        -------
        fuels_h : array
            Hourly fuel data [fueltypes, days, hours]

        Notes
        -----
        """
        fuels_h = np.zeros((fuels.shape[0], 365, 24))

        # Iterate fueltypes and day and multiply daily fuel data with daily shape
        for k, fuel in enumerate(fuels):
            for day in range(365):
                fuels_h[k][day] = enduse_shape_dh[day] * fuel[day]

        assertions.assertAlmostEqual(np.sum(fuels), np.sum(fuels_h), places=2, msg="The function Day to h tranfsormation failed", delta=None)

        return fuels_h

    '''def calc_enduse_fuel_tech_peak_yd_factor(self, fueltypes, tech_fuels, factor_d, tech_stock):
        """Disaggregate yearly absolute fuel data for every technology to the peak day.

        Parameters
        ----------
        tech_fuels : dict
            Fuels per technology

        Returns
        -------
        fuels_d_peak : array
            Hourly absolute fuel data

        Example
        -----
        Input: 20 FUEL * 0.004 [0.4%] --> new fuel

        """
        fuels_d_peak = np.zeros((len(tech_fuels), len(fueltypes), 1))

        for tech in tech_fuels:
            fueltype_tech = tech_stock.get_tech_attribute(tech, 'fuel_type')
            fuel_tech = tech_fuels[tech]
            fuels_d_peak[fueltype_tech] += factor_d * fuel_tech
            fuels_d_peak[tech][fueltype_tech] += factor_d * fuel_tech

        return fuels_d_peak
    '''

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
        fuels_d_peak = np.zeros((len(fuels)))

        for fueltype, fueltype_year_data in enumerate(fuels):
            '''print("Fuetlype: " + str(fueltype))
            print(factor_d)
            print(fueltype_year_data.shape)
            print(fueltype_year_data[0])
            print("--")
            print(fueltype_year_data)
            a = factor_d * fueltype_year_data # BIG CHANGE[0]
            print("aa.aa")
            print(a)
            '''
            fuels_d_peak[fueltype] = factor_d * fueltype_year_data
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
