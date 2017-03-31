""" This file contains all assumptions of the energy demand model"""
import numpy as np
import copy
import energy_demand.main_functions as mf
# pylint: disable=I0011,C0321,C0301,C0103, C0325

'''
----------------------
# RESIDENTIAL END_USES
----------------------

The ECUK table serves as the most important national energy demand input.

[y]   Yearly variation
[h]   Shape of each hour in a day
[d]   Shape of each day in a year
[p_h] Peal Shape of heak day in hours
[p_d] Relationship between demand of peak day and demand in a year

ECUK TABLE FUEL DATA                              Shapes
====================                              ==================
                                                  [y] ?? Wheater Generator

heating (Table 3.8)                 -->           [h,p_h] Sansom (2014) which is based on Carbon Trust field data:
                                                  [d,p_d] National Grid (residential data based on CWW):

Water_heating (Table 3.8)                 -->     [d,h,p_d,p_h] HES: Water heating (shapes for all fuels)

Cooking (Table 3.8)                       -->     [d,h,p_d,p_h] HES: Cooking (shapes for all fuels)

Lighting (Table 3.8)                      -->     [d,h,p_d,p_h] HES: Lighting

Appliances (elec) (Table 3.02)
  cold (table 3.8)                        -->     [d,h,p_d,p_h] HES: Cold appliances
  wet (table 3.8)                         -->     [d,h,p_d,p_h] HES: Washing/drying
  consumer_electronics (table 3.8)        -->     [d,h,p_d,p_h] HES: Audiovisual
  home_computing (table 3.8)              -->     [d,h,p_d,p_h] HES: ICT

----------------------
# Service END_USES
----------------------

ECUK TABLE FUEL DATA                              Shapes
====================                              ==================

Carbon Trust data is for sectors and in electricity and gas

For Elec, individual shapes are used to generate shape
For gas, all gas data cross all sectors is used to generate shape
--> For enduse where both elec and gas are used, take shape of dominant fueltype and use same load shape for other fueltypes

ENDUSE
  Catering
  Computing
  Cooling and ventilation
  Hot water
  Heating
  Lighting
  Other

SECTORS                                           SHAPES
  Community, arts and leisure (individ)    -->    Carbon Trust: Community
  Education (individ)                      -->    Carbon Trust: Education
  Retail (individ)                         -->    Carbon Trust: Retail
  Health (individ)                         -->    Carbon Trust: Health
  Offices (individ)                        -->    Carbon Trust: Financial & Government

  Emergency Services (aggr)                -->    Carbon Trust: Manufacturing, other Sectors ?? (or averaged of all?)
  Hospitality (aggr)
  Military (aggr)
  Storage (aggr)

  TODO: Exclude heating from electricity by contrasting winter/summer
  (excl. heating with summer/winter comparison)
  Select individual load shapes for different sectors where possible (only electricity) (excl. heating with summer/winter comparison)
  For sectors where no carbon trail data relates,use aggregated load curves from carbon trust with: Financial, Government, Manufacturing, other Sectors

SHAPES Elec
Calculate electricity shapes for aggregated and individual sectors:
    [h]    Carbon Trust Metering Trial: averaged daily profily for every month (daytype, month, h)
    [p_h]  Carbon Trust Metering Trial: maximum peak day is selected and daily load shape exported
    [d]    Carbon Trust Metering Trial: Use (daytype, month, h) to distribute over year
    [p_d]  Carbon Trust Metering Trial: Select day with most enduse and compare how relateds to synthetically generated year

SHAPES Gas
Calculate gas shapes across all sectors:
    [h]   Carbon Trust Metering Trial: averaged daily profily for every month
    [p_h] Carbon Trust Metering Trial: the maximum peak day is selected and daily load shape exported
    [p_d] National Grid (non-residential data based on CWW)
    [d]   National Grid (non-residential data based on CWW) used to assign load for every day (then multiply with h shape)

USED SHAPES FOR ENDUSES

Catering (e,g) (Table 5.05)                         -->   Use electricity shape (disaggregate other fueltypes with this shape)

Computing (e) (Table 5.05)                          -->   Use electricity shape

Cooling and Ventilation (mainly e) (Table 5.05)     -->   Use electricity shapes and distribute other fueltypes with this shape
                                                    -->   SHAPE?

Hot Water (e,g) (Table 5.05)                        -->   More gas enduse --> Use gas shape across all sectors and distribute also with it elec.

Heating (mainly g) (Table 5.05)                     -->   Use gas load shape accross all sectors and disaggregate other fuels with this load shape

Lighting (e) (Table 5.05)                           -->   Use electricity shapes

Other (e,g) (Table 5.05)                            -->   Use overall electricity and overall gas curve

'''

def load_assumptions(data):
    """All assumptions of the energy demand model are loaded and added to the data

    Returns
    -------
    data : dict
        Data dictionary with added ssumption dict

    Notes
    -----

    #TODO: Implement mock_technology for all sectors where not definied with eff of 1
    """
    assump_dict = {}

    # TODO :Replace with loaded dict in load_data
    dict_fueltype = {
        'solid_fuel': 0,
        'gas': 1,
        'electricity': 2,
        'oil': 3,
        'heat_sold': 4,
        'bioenergy_waste':5,
        'hydrogen': 6,
        'future_fuel': 7
    }

    # ============================================================
    # Weather Assumptions (Checked)
    # ============================================================
    assump_dict['t_base'] = {
        'base_year': 15.5,
        'end_yr': 15.5
    }

    # ============================================================
    # DRIVER ASSUMPTIONS FROM BUILDING STOCK
    # ============================================================
    assump_dict['resid_scen_driver_assumptions'] = {
        'heating': ['floorarea', 'hdd', 'hlc'], #Do not use also pop because otherwise problems that e.g. existing stock + new has smaller scen value than... floorarea already contains pop
        'water_heating': ['pop'],
        'lighting': ['pop', 'floorarea'],
        'cooking': ['pop'],
        'cold': ['pop'],
        'wet': ['pop'],
        'consumer_electronics': ['pop'],
        'home_computing': ['pop'],
    }

    # ============================================================
    # Demand elasticities (Long-term resid_elasticities) # #TODO: Elasticties over time change? Not implemented so far ()
    # https://en.wikipedia.org/wiki/Price_elasticity_of_demand (e.g. -5 is much more sensitive to change than -0.2)
    # ============================================================
    resid_elasticities = {
        'heating': -0.7,
        'water_heating' : 0,
        'water' : 0,
        'cooking' : 0,
        'lighting': 0,
        'cold': 0,
        'wet': 0,
        'consumer_electronics': 0,
        'home_computing': 0,
    }
    assump_dict['resid_elasticities'] = resid_elasticities      # Add dictionaries to assumptions

    # ============================================================
    # Technologies (Residential)
    # ============================================================

    # --Efficiencies (Base year)
    eff_by = {
        # -- heating boiler ECUK Table 3.19
        'back_boiler' : 0.2,
        'combination_boiler' : 0.0,
        'condensing_boiler' : 0.5,
        'condensing_combination_boiler' : 0.0,
        'combination_boiler' : 0.0,

        # -- cooking
        'new_tech_A': 0.05,
        'tech_A' : 0.5,
        'tech_B' : 0.9,
        'tech_C': 0.0,

        # -- lighting
        'halogen_elec': 0.036,                   # Relative derived eff: 80% efficiency gaing to standard lighting blub RElative calculated to be 80% better than standard lighting bulb (180*0.02) / 100
        'standard_lighting_bulb': 0.02,          # Found on wikipedia
        'fluorescent_strip_lightinging': 0.054,  # Relative derived eff: 50% efficiency gaint to halogen (0.036*150) / 100
        'energy_saving_lighting_bulb': 0.034,    # Relative derived eff: 70% efficiency gain to standard lightingbulg
        'LED' : 0.048,                           # 40% savings compared to energy saving lighting bulb

        # -- cold
        'tech_D' : 0.5,
        'tech_E' : 0.5,
        'tech_F': 0.0,

        # -- wet
        'boiler_gas': 0.5,
        'boiler_oil': 0.5,
        'boiler_condensing': 0.5,
        'boiler_biomass': 0.5,

        # -- consumer electronics
        'ASHP': 0.5,
        'HP_ground_source': 0.5,
        'HP_air_source': 0.5,
        'HP_gas': 0.5,

        # -- home_computing
        'micro_CHP_elec': 0.5,
        'micro_CHP_thermal': 0.5
        }
    assump_dict['eff_by'] = eff_by      # Add dictionaries to assumptions

    # --Efficiencies (End year)
    eff_ey = {
        # -- heating boiler ECUK Table 3.19
        'back_boiler' : 0.2,
        'combination_boiler' : 0.0,
        'condensing_boiler' : 0.5,
        'condensing_combination_boiler' : 0.0,
        'combination_boiler' : 0.0,

        # -- cooking
        'new_tech_A': 0.05,
        'tech_A' : 0.5,
        'tech_B' : 0.9,
        'tech_C': 0.0,

        # -- lighting
        'halogen_elec': 0.036,                   # Relative derived eff: 80% efficiency gaing to standard lighting blub RElative calculated to be 80% better than standard lighting bulb (180*0.02) / 100
        'standard_lighting_bulb': 0.02,          # Found on wikipedia
        'fluorescent_strip_lightinging': 0.054,  # Relative derived eff: 50% efficiency gaint to halogen (0.036*150) / 100
        'energy_saving_lighting_bulb': 0.034,    # Relative derived eff: 70% efficiency gain to standard lightingbulg
        'LED' : 0.048,                           # 40% savings compared to energy saving lighting bulb

        # -- cold
        'tech_D' : 0.5,
        'tech_E' : 0.5,
        'tech_F': 0.0,

        # -- wet
        'boiler_gas': 0.5,
        'boiler_oil': 0.5,
        'boiler_condensing': 0.5,
        'boiler_biomass': 0.5,

        # -- consumer electronics
        'ASHP': 0.5,
        'HP_ground_source': 0.5,
        'HP_air_source': 0.5,
        'HP_gas': 0.5,

        # -- home_computing
        'micro_CHP_elec': 0.5,
        'micro_CHP_thermal': 0.5
        }
    assump_dict['eff_ey'] = eff_ey # Add dictionaries to assumptions

    # --Efficiencies (achieved until end year)
    eff_achieved = {
        # -- heating boiler ECUK Table 3.19
        'back_boiler' : 0.0,
        'combination_boiler' : 0.0,
        'condensing_boiler' : 0.0,
        'condensing_combination_boiler' : 0.0,
        'combination_boiler' : 0.0,
        'boiler_A' : 0.5,
        'boiler_B' : 0.3,
        'new_tech_A': 0.1,
        'tech_A' : 0.5,
        'tech_B' : 0.5,
        'tech_C': 0.0,
        'tech_D' : 0.5,
        'tech_E' : 0.5,
        'tech_F': 0.0,
        'boiler_gas': 0.5,
        'boiler_oil': 0.5,
        'boiler_condensing': 0.5,
        'boiler_biomass': 0.5,
        'ASHP': 0.5,
        'HP_ground_source': 0.5,
        'HP_air_source': 0.5,
        'HP_gas': 0.5,
        'micro_CHP_elec': 0.5,
        'micro_CHP_thermal': 0.5,

        # -- lightinging
        'halogen_elec': 0.5,
        'standard_lighting_bulb': 0.5,
        'fluorescent_strip_lightinging': 0.5,
        'energy_saving_lighting_bulb': 0.5,
        'LED' : 0.6
    }
    assump_dict['eff_achieved'] = eff_achieved # Add dictionaries to assumptions

    # Define fueltype of each technology
    technology_fueltype = {
        'LED': dict_fueltype['electricity'],
        'halogen_elec': dict_fueltype['electricity'],
        'standard_lighting_bulb': dict_fueltype['electricity'],
        'fluorescent_strip_lightinging': dict_fueltype['electricity'],
        'energy_saving_lighting_bulb': dict_fueltype['electricity'],
        'LED' : dict_fueltype['electricity']
    }
    assump_dict['technology_fueltype'] = technology_fueltype


    # ---Helper function eff_achieved THIS can be used for scenarios to define how much of the fficiency was achieved
    for i in assump_dict['eff_achieved']:
        assump_dict['eff_achieved'][i] = 1.0

    # Create lookup for technologies (That technologies can be replaced for calculating with arrays) Helper function
    data['tech_lu'] = {}
    for tech_id, tech in enumerate(eff_by, 1000):
        data['tech_lu'][tech] = tech_id

    # ---------------------------------------------------------------------------------------------------------------------
    # Fuel Switches assumptions
    # ---------------------------------------------------------------------------------------------------------------------

    # -- Technology which is installed for the share of fueltype to be replaced
    assump_dict['tech_install'] = {
        'lighting': 'LED',
        'water_heating': 'condensing_boiler'
    }

    # --Technologies which are replaced within enduse and fueltype
    tech_replacement_dict = {
        'lighting':{
            0: '',
            1: '',
            2: 'halogen_elec', # Halogen_elec gets replaced by LED
            3: '',
            4: '',
            5: '',
            6: '',
            7: ''
        },
        'water_heating':{
            0: '',
            1: '',
            2: 'back_boiler', #
            3: '',
            4: '',
            5: '',
            6: '',
            7: ''
        },
    }
    assump_dict['tech_replacement_dict'] = tech_replacement_dict

    # --Share of fuel types for each enduse
    fuel_type_p_by = generate_fuel_type_p_by(data) # Generate fuel distribution of base year for every end_use 
    assump_dict['fuel_type_p_by'] = mf.convert_to_array(fuel_type_p_by)


    # --Reduction fraction of each fuel in each enduse compared to base year. Always positive values (0.2 --> 20% reduction)
    assump_fuel_frac_ey ={
        'lighting': {
            '0' : 0.0,
            '1' : 0.0,
            '2' : 0.3, # electricity for lighting replaced
            '3' : 0.0,
            '4' : 0.0,
            '5' : 0.0,
            '6' : 0.0,
            '7':  0.0
            }
    }

    # Helper function - Replace all enduse from assump_fuel_frac_ey
    fuel_type_p_ey = {}
    for enduse in fuel_type_p_by:
        if enduse not in assump_fuel_frac_ey:
            fuel_type_p_ey[enduse] = fuel_type_p_by[enduse]
        else:
            fuel_type_p_ey[enduse] = assump_fuel_frac_ey[enduse]
    assump_dict['fuel_type_p_ey'] = mf.convert_to_array(fuel_type_p_ey) # Convert to array

    # TODO: Write function to insert fuel switches  
    # TODO: Assert if always 100% #assert p_tech_by['boiler_A'] + p_tech_by['boiler_B'] == 1.0
    #print("end ear")
    #print(assump_dict['fuel_type_p_ey']['lighting'])


    # --------------------------------
    # Technology diffusion assumptions
    # --------------------------------
    assump_dict['sig_midpoint'] = 0
    assump_dict['sig_steeppness'] = 1

    # ----------------------------------
    # Which technologies are used for which end_use and to which share
    # ----------------------------------
    #Share of technology for every enduse and fueltype in base year [in %]
    # Only shares within each fueltype !!!!

    # Create technoogy empties for all enduses
    technologies_enduse_by = {}
    fuel_data = data['data_residential_by_fuel_end_uses']

    for enduse in fuel_data: #TODFO ITERATE ENDUSE NOT UFEL DATA
        technologies_enduse_by[enduse] = {}

        for fueltype in range(len(data['fuel_type_lu'])):
            technologies_enduse_by[enduse][fueltype] = {}

    # Add technological split where known
    technologies_enduse_by['lighting'][2] = {'LED': 0.01, 'halogen_elec': 0.37, 'standard_lighting_bulb': 0.35, 'fluorescent_strip_lightinging': 0.09, 'energy_saving_lighting_bulb': 0.18}
    technologies_enduse_by['water_heating'][2] = {'back_boiler': 0.9, 'condensing_boiler': 0.1}
    assump_dict['technologies_enduse_by'] = technologies_enduse_by # add to dict

    # --Technological split in end_yr  # FOR END YEAR ALWAYS SAME NR OF TECHNOLOGIES AS INITIAL YEAR (TODO: ASSERT IF ALWAYS 100%)
    technologies_enduse_ey = copy.deepcopy(technologies_enduse_by)
    
    technologies_enduse_ey['lighting'][2] = {'LED': 0.01, 'halogen_elec': 0.37, 'standard_lighting_bulb': 0.35, 'fluorescent_strip_lightinging': 0.09, 'energy_saving_lighting_bulb': 0.18}
    technologies_enduse_ey['water_heating'][2] = {'back_boiler': 0.1, 'condensing_boiler': 0.9}

    assump_dict['technologies_enduse_ey'] = technologies_enduse_ey





    # ============================================================
    # Assumptions Residential Dwelling Stock
    # ============================================================

    # Building stock related, assumption of change in floor area up to end_yr (Checked)
    assump_dict['assump_diff_floorarea_pp'] = 0.01 # [%] If e.g. 0.4 --> 40% increase (the one is added in the model)  ASSUMPTION (if minus, check if new buildings are needed)

    # Dwelling type distribution
    assump_dict['assump_dwtype_distr_by'] = {'semi_detached': 0.26, 'terraced': 0.283, 'flat': 0.203, 'detached': 0.166, 'bungalow': 0.088} #base year
    assump_dict['assump_dwtype_distr_ey'] = {'semi_detached': 0.26, 'terraced': 0.283, 'flat': 0.203, 'detached': 0.166, 'bungalow': 0.088} #end year

    # Floor area per dwelling type
    assump_dict['assump_dwtype_floorarea'] = {'semi_detached': 96, 'terraced': 82.5, 'flat': 61, 'detached': 147, 'bungalow': 77}             #TODO MAYBE IMPELEMENT THAT DIFFERENT FOR EVERY YEAR                                               # Average floor area per dwelling type (loaded from CSV)

    # Add assumptions to data dict
    data['assumptions'] = assump_dict
    return data







# ------------- Helper functions
def generate_fuel_type_p_by(data):
    """Assumption helper function to generate percentage fuel distribution for every enduse of base year"""

    fuel_data = data['data_residential_by_fuel_end_uses']
    out_dict = {}

    for enduse in fuel_data:
        out_dict[enduse] = {}

        # sum fueltype
        sum_fueltype = np.sum(fuel_data[enduse])
        if sum_fueltype != 0:
            fuels_in_p = fuel_data[enduse] / sum_fueltype
        else:
            fuels_in_p = fuel_data[enduse] # all zeros

        for fueltype, fuels in enumerate(fuels_in_p):
            out_dict[enduse][fueltype] = float(fuels) # Convert to %

    return out_dict
