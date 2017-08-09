"""Residential model"""
# pylint: disable=I0011,C0321,C0301,C0103,C0325,no-member
import numpy as np
import energy_demand.region as reg
import energy_demand.submodule_residential as submodule_residential
import energy_demand.submodule_service as submodule_service
import energy_demand.submodule_industry as submodule_industry
import energy_demand.submodule_transport as submodule_transport
from energy_demand.scripts_shape_handling import load_factors as load_factors

class EnergyModel(object):
    """Class of a country containing all regions as self.attributes

    The main class of the residential model. For every region, a Region object needs to be generated.

    Parameters
    ----------
    regions : list
        Dictionary containign the name of the Region (unique identifier)
    data : dict
        Main data dictionary

    Notes
    -----
    this class has as many attributes as regions (for evry rgion an attribute)
    """
    def __init__(self, region_names, data):
        """Constructor of the class which holds all regions of a country
        """
        print("..start main energy demand function")

        self.curr_yr = data['base_sim_param']['curr_yr']

        # Create object for every region and add into list
        self.regions = self.create_regions(region_names, data)

        # --------------------
        # Residential SubModel
        # --------------------
        self.rs_submodel = self.residential_submodel(data, data['rs_all_enduses'], data['rs_sectors'])

        # --------------------
        # Service SubModel
        # --------------------
        self.ss_submodel = self.service_submodel(data, data['ss_all_enduses'], data['ss_sectors'])

        # --------------------
        # Industry SubModel
        # --------------------
        self.is_submodel = self.industry_submodel(data, data['is_all_enduses'], data['is_sectors'])

        # --------------------
        # Transport SubModel
        # --------------------
        self.ts_submodel = self.other_submodels()

        # ---------------------------------------------------------------------
        # Functions to summarise data for all Regions in the EnergyModel class
        #  ---------------------------------------------------------------------
        # Sum according to weekend, working day

        # Sum across all regions, all enduse and sectors
        self.sum_uk_fueltypes_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.ss_submodel, self.rs_submodel, self.is_submodel, self.ts_submodel], 'sum', 'non_peak')

        self.all_submodels_sum_uk_specfuelype_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.ss_submodel, self.rs_submodel, self.is_submodel, self.ts_submodel], 'no_sum', 'non_peak')
        self.rs_sum_uk_specfuelype_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.rs_submodel], 'no_sum', 'non_peak')
        self.ss_sum_uk_specfuelype_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.ss_submodel], 'no_sum', 'non_peak')
        self.is_sum_uk_specfuelype_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.is_submodel], 'no_sum', 'non_peak')
        self.ts_sum_uk_specfuelype_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.ts_submodel], 'no_sum', 'non_peak')

        self.rs_tot_fuels_all_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.rs_submodel], 'no_sum', 'non_peak')
        self.ss_tot_fuels_all_enduses_y = self.sum_regions('enduse_fuel_yh', data['nr_of_fueltypes'], [self.ss_submodel], 'no_sum', 'non_peak')

        # Sum across all regions for enduse
        self.all_models_tot_fuel_y_enduse_specific_h = self.sum_enduse_all_regions('enduse_fuel_yh', [self.rs_submodel, self.ss_submodel, self.is_submodel, self.ts_submodel])

        self.rs_tot_fuel_y_enduse_specific_h = self.sum_enduse_all_regions('enduse_fuel_yh', [self.rs_submodel])
        self.ss_tot_fuel_enduse_specific_h = self.sum_enduse_all_regions('enduse_fuel_yh', [self.ss_submodel])


        # Sum across all regions, enduses for peak hour

        # NEW
        self.peak_all_models_all_enduses_fueltype = self.sum_regions('enduse_fuel_peak_dh', data['nr_of_fueltypes'], [self.rs_submodel, self.ss_submodel, self.is_submodel, self.ts_submodel], 'no_sum', 'peak_dh')
        print("......PEAK SUMMING")
        print(np.sum(self.peak_all_models_all_enduses_fueltype[2]))

        self.rs_tot_fuel_y_max_allenduse_fueltyp = self.sum_regions('enduse_fuel_peak_h', data['nr_of_fueltypes'], [self.rs_submodel], 'no_sum', 'peak_h')
        self.ss_tot_fuel_y_max_allenduse_fueltyp = self.sum_regions('enduse_fuel_peak_h', data['nr_of_fueltypes'], [self.ss_submodel], 'no_sum', 'peak_h')

        # Functions for load calculations
        # ---------------------------
        self.rs_fuels_peak_h = self.sum_regions('enduse_fuel_peak_h', data['nr_of_fueltypes'], [self.rs_submodel], 'no_sum', 'peak_h')
        self.ss_fuels_peak_h = self.sum_regions('enduse_fuel_peak_h', data['nr_of_fueltypes'], [self.ss_submodel], 'no_sum', 'peak_h')

        # Across all enduses calc_load_factor_h
        self.rs_reg_load_factor_h = load_factors.calc_load_factor_h(data, self.rs_tot_fuels_all_enduses_y, self.rs_fuels_peak_h)
        self.ss_reg_load_factor_h = load_factors.calc_load_factor_h(data, self.ss_tot_fuels_all_enduses_y, self.ss_fuels_peak_h)

        # SUMMARISE FOR EVERY REGION AND ENDSE
        #self.tot_country_fuel_y_load_max_h = self.peak_loads_per_fueltype(data, self.regions, 'rs_reg_load_factor_h')

    def get_regional_yh(self, nr_of_fueltypes, region_name):
        """Get fuel for all fueltype for yh for specific region (all submodels)

        Parameters
        ----------
        region_name : str
            Name of region to get attributes
        attributes : str
            Attributes to read out
        """
        region_fuel_yh = np.zeros((nr_of_fueltypes, 365, 24))
        sector_models = [self.rs_submodel, self.ss_submodel, self.is_submodel, self.ts_submodel]

        for sector_model in sector_models:
            for region_submodel in sector_model:
                if region_submodel.region_name == region_name:
                    region_fuel_yh += getattr(region_submodel.enduse_object, 'enduse_fuel_yh')

        return region_fuel_yh

    def get_fuel_region_all_models_yh(self, data, region_name_to_get, sector_models, attribute_to_get):
        """Summarise fuel yh for a certain region
        """
        tot_fuels_all_enduse_yh = np.zeros((data['nr_of_fueltypes'], 365, 24))

        for sector_model in sector_models:
            sector_model_objects = getattr(self, sector_model)
            for model_object in sector_model_objects:
                if model_object.region_name == region_name_to_get:
                    tot_fuels_all_enduse_yh += getattr(model_object.enduse_object, attribute_to_get)

        return tot_fuels_all_enduse_yh

    def other_submodels(self):
        """Other submodel
        """
        print("..other submodel start")
        submodule_list = []

        # Iterate regions, sectors and enduses
        for region_object in self.regions:

            # Create submodule
            submodule = submodule_transport.OtherModel(
                region_object,
                'generic_transport_enduse'
            )

            # Add to list
            submodule_list.append(submodule)

        return submodule_list

    def industry_submodel(self, data, enduses, sectors):
        """Industry subsector model
        """
        print("..industry submodel start")
        submodule_list = []

        # Iterate regions, sectors and enduses
        for region_object in self.regions:
            for sector in sectors:
                for enduse in enduses:

                    # Create submodule
                    submodule = submodule_industry.IndustryModel(
                        data,
                        region_object,
                        enduse,
                        sector=sector
                        )

                    # Add to list
                    submodule_list.append(submodule)

        return submodule_list

    def residential_submodel(self, data, enduses, sectors):
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
        print("..residential submodel start")
        submodule_list = []

        # Iterate regions and enduses
        for region_object in self.regions:
            for sector in sectors:
                for enduse in enduses:

                    # Create submodule
                    submodel_object = submodule_residential.ResidentialModel(
                        data,
                        region_object,
                        enduse,
                        sector
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
        print("..service submodel start")
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

    @classmethod
    def create_regions(cls, region_names, data):
        """Create all regions and add them in a list

        Parameters
        ----------
        regions : list
            The name of the Region (unique identifier)
        """
        regions = []

        # Iterate all regions
        for region_name in region_names:
            print("...creating region: '{}'  ".format(region_name))
            # Generate region object
            region_object = reg.Region(
                region_name=region_name,
                data=data
                )

            # Add region to list
            regions.append(region_object)

        return regions

    @classmethod
    def sum_enduse_all_regions(cls, attribute_to_get, sector_models):
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
                if region_enduse_object.enduse not in enduse_dict:
                    enduse_dict[region_enduse_object.enduse] = 0

                # Summarise enduse attribute
                enduse_dict[region_enduse_object.enduse] += np.sum(getattr(region_enduse_object.enduse_object, attribute_to_get))

        return enduse_dict

    def sum_regions(self, attribute_to_get, nr_of_fueltypes, sector_models, crit, crit2):
        """Collect hourly data from all regions and sum across all fuel types and enduses

        Parameters
        ----------
        attribute_to_get : 
        data

        Returns
        -------
        """
        if crit2 == 'peak_h':
            fuels = np.zeros((nr_of_fueltypes, ))
        if crit2 == 'non_peak':
            fuels = np.zeros((nr_of_fueltypes, 365, 24))
        if crit2 == 'peak_dh':
            fuels = np.zeros((nr_of_fueltypes, 24))

        for sector_model in sector_models:
            for model_object in sector_model:
                fuels += getattr(model_object.enduse_object, attribute_to_get)

        if crit == 'no_sum':
            fuels = fuels
        if crit == 'sum':
            fuels = np.sum(fuels)

        return fuels
