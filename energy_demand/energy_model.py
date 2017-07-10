"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103,C0325,no-member
import unittest
import numpy as np
import energy_demand.region as reg
import energy_demand.submodule_residential as submodule_residential
import energy_demand.submodule_service as submodule_service
from energy_demand.scripts_shape_handling import load_factors as load_factors
ASSERTIONS = unittest.TestCase('__init__')

def model_main_function(data):
    """Main function of residential model

    This function is executed in the wrapper.

    Parameters
    ----------
    data : dict
        Contains all data not provided externally

    Returns
    -------
    energ_demand_object : object

    """
    fuel_in = test_function_fuel_sum(data) #SCRAP_ TEST FUEL SUM

    # Add all region instances as an attribute (region name) into the class `EnergyModel`
    energ_demand_object = EnergyModel(
        reg_names=data['lu_reg'],
        data=data,
    )

    # ----------------------------
    # Summing
    # ----------------------------
    fueltot = energ_demand_object.sum_uk_fueltypes_enduses_y # Total fuel of country

    print("================================================")
    print("Fuel input:          " + str(fuel_in))
    print("Fuel output:         " + str(fueltot))
    print("FUEL DIFFERENCE:     " + str(fueltot - fuel_in))
    print("================================================")
    return energ_demand_object

class EnergyModel(object):
    """Class of a country containing all regions as self.attributes

    The main class of the residential model. For every region, a Region object needs to be generated.

    Parameters
    ----------
    reg_names : list
        Dictionary containign the name of the Region (unique identifier)
    data : dict
        Main data dictionary

    Notes
    -----
    this class has as many attributes as regions (for evry rgion an attribute)
    """
    def __init__(self, reg_names, data):
        """Constructor of the class which holds all regions of a country
        """
        self.curr_yr = data['curr_yr']

        # Create object for every region and add into list
        self.regions = self.create_regions(reg_names, data)

        # --Residential SubModel
        self.rs_submodel = self.residential_submodel(data, data['rs_all_enduses'])

        # --Service SubModel
        self.ss_submodel = self.service_submodel(data, data['ss_all_enduses'], data['all_service_sectors'])

        # --Industry SubModel
        self.is_submodel = self.industry_submodel(data)

        # --Other SubModels


        # ---------------------------------------------------------------------
        # Functions to summarise data for all Regions in the EnergyModel class
        #  ---------------------------------------------------------------------

        # Sum across all regions, all enduse and sectors
        self.sum_uk_fueltypes_enduses_y = self.sum_regions('enduse_fuel_yh', data, [self.ss_submodel, self.rs_submodel], 'sum', 'non_peak')

        self.rs_tot_fuels_all_enduses_y = self.sum_regions('enduse_fuel_yh', data, [self.rs_submodel], 'no_sum', 'non_peak')
        self.ss_tot_fuels_all_enduses_y = self.sum_regions('enduse_fuel_yh', data, [self.ss_submodel], 'no_sum', 'non_peak')

        # Sum across all regions for enduse
        self.rs_tot_fuel_y_enduse_specific_h = self.sum_enduse_all_regions('enduse_fuel_yh', [self.rs_submodel])
        self.ss_tot_fuel_enduse_specific_h = self.sum_enduse_all_regions('enduse_fuel_yh', [self.ss_submodel])


        # Sum across all regions, enduses for peak hour
        self.rs_tot_fuel_y_max_allenduse_fueltyp = self.sum_regions('enduse_fuel_peak_h', data, [self.rs_submodel], 'no_sum', 'peak_h')
        self.ss_tot_fuel_y_max_allenduse_fueltyp = self.sum_regions('enduse_fuel_peak_h', data, [self.ss_submodel], 'no_sum', 'peak_h')

        # Functions for load calculations
        # ---------------------------
        self.rs_fuels_peak_h = self.sum_regions('enduse_fuel_peak_h', data, [self.rs_submodel], 'no_sum', 'peak_h')
        self.ss_fuels_peak_h = self.sum_regions('enduse_fuel_peak_h', data, [self.ss_submodel], 'no_sum', 'peak_h')

        # ACross all enduses calc_load_factor_h
        self.rs_reg_load_factor_h = load_factors.calc_load_factor_h(data, self.rs_tot_fuels_all_enduses_y, self.rs_fuels_peak_h)
        self.ss_reg_load_factor_h = load_factors.calc_load_factor_h(data, self.ss_tot_fuels_all_enduses_y, self.ss_fuels_peak_h)

        # SUMMARISE FOR EVERY REGION AND ENDSE
        #self.tot_country_fuel_y_load_max_h = self.peak_loads_per_fueltype(data, self.regions, 'rs_reg_load_factor_h')

    def industry_submodel(self, data):

        pass

    def residential_submodel(self, data, enduses):
        """Create the residential submodules (per enduse and region) and add them to list

        Parameters
        ----------
        data : dict
            Data container
        enduses : list
            All residential enduses

        Returns
        -------
        submodule_list : list
            List with submodules
        """
        submodule_list = []

        # Iterate regions and enduses
        for region_object in self.regions:
            for enduse in enduses:

                # Create submodule
                submodel_object = submodule_residential.ResidentialModel(
                    data,
                    region_object,
                    enduse
                    )

                submodule_list.append(submodel_object)

        return submodule_list

    def service_submodel(self, data, enduses, sectors):
        """Create the service submodules per enduse, sector and region and add to list

        Parameters
        ----------
        data : dict
            Data container
        enduses : list
            All residential enduses
        sectors : list
            Service sectors

        Returns
        -------
        submodule_list : list
            List with submodules
        """
        submodule_list = []

        # Iterate regions, sectors and enduses
        for region_object in self.regions:
            for sector in sectors:
                for enduse in enduses:

                    # Create submodule
                    submodule = submodule_service.ServiceModel(
                        data,
                        region_object,
                        enduse,
                        sector
                        )

                    # Add to list
                    submodule_list.append(submodule)

        return submodule_list

    def create_regions(self, reg_names, data):
        """Create all regions and add them in a list

        Parameters
        ----------
        reg_names : list
            The name of the Region (unique identifier)
        """
        regions = []

        # Iterate all regions
        for reg_name in reg_names:

            # Generate region objects
            region_object = reg.Region(
                reg_name=reg_name,
                data=data
                )

            # Add regions to list
            regions.append(region_object)

        return regions

    def sum_enduse_all_regions(self, attribute_to_get, sector_models):
        """Summarise an enduse attribute across all regions

        Parameters
        ----------
        attribute_to_get : string
            Enduse attribute to summarise
        sector_models : List
            List with sector models

        Return
        ------
        enduse_dict : dict
            Summarise enduses across all regions
        """
        enduse_dict = {}

        for sector_model_enduse in sector_models: # Iterate sector models
            for region_enduse_object in sector_model_enduse: # Iterate enduse

                # Get regional enduse object
                if region_enduse_object.enduse_name not in enduse_dict:
                    enduse_dict[region_enduse_object.enduse_name] = 0

                # Summarise enduse attribute
                enduse_dict[region_enduse_object.enduse_name] += np.sum(getattr(region_enduse_object.enduse_object, attribute_to_get))

        return enduse_dict

    def sum_regions(self, attribute_to_get, data, sector_models, crit, crit2):
        """Collect hourly data from all regions and sum across all fuel types and enduses
        """
        if crit2 == 'peak_h':
            tot_fuels_all_enduse = np.zeros((data['nr_of_fueltypes'], ))
        if crit2 == 'non_peak':
            tot_fuels_all_enduse = np.zeros((data['nr_of_fueltypes'], 365, 24))

        for sector_model in sector_models:
            for model_object in sector_model:
                tot_fuels_all_enduse += getattr(model_object.enduse_object, attribute_to_get)

        if crit == 'no_sum':
            tot_fuels_all_enduse = tot_fuels_all_enduse
        if crit == 'sum':
            tot_fuels_all_enduse = np.sum(tot_fuels_all_enduse)

        return tot_fuels_all_enduse

    def peak_loads_per_fueltype_NEW(self, data, regions, attribute_to_get):
        """Get peak loads for fueltype per maximum h
        """
        peak_loads_fueltype_max_h = np.zeros((data['nr_of_fueltypes']))

        for reg_object in regions:

            # Get fuel data of region
            load_max_h = getattr(reg_object, attribute_to_get)

            for fueltype, load_max_h in enumerate(load_max_h):
                peak_loads_fueltype_max_h[fueltype] += load_max_h

        return peak_loads_fueltype_max_h







# ------------- Testing functions
def test_function_fuel_sum(data):
    """ Sum raw disaggregated fuel data """
    fuel_in = 0
    for region in data['rs_fueldata_disagg']:
        for enduse in data['rs_fueldata_disagg'][region]:
            fuel_in += np.sum(data['rs_fueldata_disagg'][region][enduse])

    for region in data['ss_fueldata_disagg']:
        for sector in data['ss_fueldata_disagg'][region]:
            for enduse in data['ss_fueldata_disagg'][region][sector]:
                fuel_in += np.sum(data['ss_fueldata_disagg'][region][sector][enduse])

    return fuel_in
