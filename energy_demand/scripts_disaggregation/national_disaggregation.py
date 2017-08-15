""" This File disaggregates total national demand """
import numpy as np
from energy_demand.scripts_shape_handling import hdd_cdd
# pylint: disable=I0011,C0321,C0301,C0103,C0325

'''
============================================
MEthod to derive GVA/POP SERVICE FLOOR AREAS
============================================

1. Step
Get correlation between regional GVA and (regional floor area/reg pop) of every sector of base year
-- Get this correlation for every region and build national correlation

2. Step
Calculate future regional floor area demand based on GVA and pop projection

'''

def disaggregate_base_demand(data):
    """This function disaggregates fuel demand based on region specific parameters
    for the base year

    The residential, service and industry demand is disaggregated according to
    different factors

    Parameters
    ----------
    data : dict
        Contains all data not provided externally

    Returns
    -------
    data : dict
    """
    def sum_fuels_before(fuel):
        """Inner function for testing purposes - sum fuel"""
        tot = 0
        for i in fuel:
            tot += np.sum(fuel[i])
        return tot

    def sum_fuels_after(reg_fuel):
        """Inner function for testing purposes - sum fuel"""
        tot = 0
        for reg in reg_fuel:
            for enduse in reg_fuel[reg]:
                tot += np.sum(reg_fuel[reg][enduse])
        return tot

    # Disaggregate residential submodel data
    data['rs_fueldata_disagg'] = rs_disaggregate(data, data['rs_fuel_raw_data_enduses'])

    # Disaggregate service submodel data
    data['ss_fueldata_disagg'] = ss_disaggregate(data, data['ss_fuel_raw_data_enduses'])

    # Disaggregate industry submodel data
    data['is_fueldata_disagg'] = is_disaggregate(data, data['is_fuel_raw_data_enduses'])

    # Disaggregate transportation sector
    data['ts_fueldata_disagg'] = scrap_ts_disaggregate(data, data['ts_fuel_raw_data_enduses'])
    #data['ag_fueldata_disagg'] = scrap_ag_disaggregate(data, data['ag_fuel_raw_data_enduses']['agriculture'])

    # Check if total fuel is the same before and after aggregation
    test_sum_before = sum_fuels_before(data['rs_fuel_raw_data_enduses'])
    test_sum_after = sum_fuels_after(data['rs_fueldata_disagg'])
    np.testing.assert_almost_equal(test_sum_before, test_sum_after, decimal=2, err_msg="")
    return data

def ss_disaggregate(data, raw_fuel_sectors_enduses):
    """Disaggregate fuel for service submodel (per enduse and sector)
    """
    print("...disaggregate service demand")
    ss_fueldata_disagg = {}

    # ---------------------------------------
    # Calculate heating degree days for regions
    # ---------------------------------------
    ss_hdd_individ_region = hdd_cdd.get_hdd_country(data['lu_reg'], data, 'ss_t_base_heating')

    ss_cdd_individ_region = hdd_cdd.get_cdd_country(data['lu_reg'], data, 'ss_t_base_cooling')

    # ---------------------------------------
    # Overall disaggregation factors per enduse and sector
    # ---------------------------------------
    # Total floor area for every enduse per sector
    national_floorarea_by_sector = {}
    for sector in data['ss_sectors']:
        national_floorarea_by_sector[sector] = 0
        for region in data['lu_reg']:
            national_floorarea_by_sector[sector] += data['ss_sector_floor_area_by'][region][sector]

    f_ss_catering = {}
    f_ss_computing = {}
    f_ss_cooling_ventilation = {}
    f_ss_water_heating = {}
    f_ss_space_heating = {}
    f_ss_lighting = {}
    f_ss_other_electricity = {}
    f_ss_other_gas = {}

    for sector in data['all_sectors']:
        f_ss_catering[sector] = 0   
        f_ss_computing[sector] = 0   
        f_ss_cooling_ventilation[sector] = 0   
        f_ss_water_heating[sector] = 0   
        f_ss_space_heating[sector] = 0   
        f_ss_lighting[sector] = 0   
        f_ss_other_electricity[sector] = 0   
        f_ss_other_gas[sector] = 0   

        for region_name in data['lu_reg']:
            
            # HDD
            reg_hdd = ss_hdd_individ_region[region_name]
            reg_cdd = ss_cdd_individ_region[region_name]
    
            # Floor Area of sector
            reg_floor_area = data['ss_sector_floor_area_by'][region_name][sector]

            # Population
            reg_pop = data['population'][data['base_sim_param']['base_yr']][region_name]

            # National disaggregation factors
            f_ss_catering[sector] += reg_pop
            f_ss_computing[sector] += reg_pop
            f_ss_cooling_ventilation[sector] += reg_pop * reg_cdd
            f_ss_water_heating[sector] += reg_pop
            f_ss_space_heating[sector] += reg_floor_area * reg_hdd
            f_ss_lighting[sector] += reg_floor_area
            f_ss_other_electricity[sector] += reg_pop
            f_ss_other_gas[sector] += reg_pop
            
    # --------------------------------------- 
    # Disaggregate according to enduse
    # ---------------------------------------
    for region_name in data['lu_reg']:
        ss_fueldata_disagg[region_name] = {}
        for sector in data['ss_sectors']:
            ss_fueldata_disagg[region_name][sector] = {}
            for enduse in data['ss_all_enduses']:

                # HDD
                reg_hdd = ss_hdd_individ_region[region_name]
                reg_cdd = ss_cdd_individ_region[region_name]
        
                # Floor Area of sector
                reg_floor_area = data['ss_sector_floor_area_by'][region_name][sector]

                # Population
                reg_pop = data['population'][data['base_sim_param']['base_yr']][region_name]

                if enduse == 'ss_catering':
                    reg_diasg_factor = reg_pop / f_ss_catering[sector]
                elif enduse == 'ss_computing':
                    reg_diasg_factor = reg_pop / f_ss_computing[sector]
                elif enduse == 'ss_cooling_ventilation':
                    reg_diasg_factor = (reg_pop * reg_cdd) / f_ss_cooling_ventilation[sector]
                elif enduse == 'ss_water_heating':
                    reg_diasg_factor = reg_pop / f_ss_water_heating[sector]
                elif enduse == 'ss_space_heating':
                    reg_diasg_factor = (reg_floor_area * reg_hdd) / f_ss_space_heating[sector]
                elif enduse == 'ss_lighting':
                    reg_diasg_factor = reg_floor_area / f_ss_lighting[sector]
                if enduse == 'ss_other_electricity':
                    reg_diasg_factor = reg_pop / f_ss_other_electricity[sector]
                elif enduse == 'ss_other_gas':
                    reg_diasg_factor = reg_pop / f_ss_other_gas[sector]

                # Disaggregate (fuel * factor)
                ss_fueldata_disagg[region_name][sector][enduse] = raw_fuel_sectors_enduses[sector][enduse] * reg_diasg_factor
    
    '''# Iterate regions
    for region_name in data['lu_reg']:
        ss_fueldata_disagg[region_name] = {}

        # Iterate sector
        for sector in data['ss_sectors']:
            ss_fueldata_disagg[region_name][sector] = {}

            # Calculate total national floor area of this sector
            national_floorarea_sector = 0
            for region in data['lu_reg']:
                national_floorarea_sector += sum(data['ss_sector_floor_area_by'][region].values())
            # Calculate total national GVA
            # todo national_GVA = 100

            # Sector specifid info
            reg_floorarea_sector = sum(data['ss_sector_floor_area_by'][region_name].values()) #get from Newcastl

            # Iterate enduse
            for enduse in data['ss_all_enduses']:
                national_fuel_sector_by = raw_fuel_sectors_enduses[sector][enduse]
                #control_sum2 += np.sum(national_fuel_sector_by)
                #print("national_fuel_sector_by: " + str(national_fuel_sector_by))
                # ----------------------
                # Disaggregating factors
                # TODO: IMPROVE. SHOW HOW IS DISAGGREGATED
                # ----------------------
                if enduse == 'ss_space_heating':
                    reg_disaggregation_factor = (1 / national_floorarea_sector) * reg_floorarea_sector
                    #regional_GVA =
                else:
                    # TODO: USE DEPENDING ON ENDUSE OTHER FACTORS SUC HAS GVA OR SIMILAR
                    reg_disaggregation_factor = (1 / national_floorarea_sector) * reg_floorarea_sector
                    #regional_GVA

                #print("reg_disaggregation_factor: " + str(reg_disaggregation_factor))

                # Disaggregated national fuel
                reg_fuel_sector_enduse = reg_disaggregation_factor * national_fuel_sector_by
                #control_sum += np.sum(reg_fuel_sector_enduse)

                ss_fueldata_disagg[region_name][sector][enduse] = reg_fuel_sector_enduse
    '''
    # TESTING Check if total fuel is the same before and after aggregation
    # ---------------
    control_sum1 = 0
    control_sum2 = 0
    for reg in ss_fueldata_disagg:
        for sector in ss_fueldata_disagg[reg]:
            for enduse in ss_fueldata_disagg[reg][sector]:
                control_sum1 += np.sum(ss_fueldata_disagg[reg][sector][enduse])

    for sector in data['ss_sectors']:
        for enduse in data['ss_all_enduses']:
            control_sum2 += np.sum(raw_fuel_sectors_enduses[sector][enduse])

    #The loaded floor area must correspond to provided fuel sectors numers
    np.testing.assert_almost_equal(control_sum1, control_sum2, decimal=2, err_msg="")

    return ss_fueldata_disagg

def scrap_ts_disaggregate(data, fuel_national):
    """Disaggregate transport sector
    """
    fueldata_disagg = {}

    national_floorarea_sector = 0
    for region_name in data['lu_reg']:
        national_floorarea_sector += sum(data['ss_sector_floor_area_by'][region_name].values())

    # Iterate regions
    for region_name in data['lu_reg']:
        fueldata_disagg[region_name] = {}
        reg_floorarea_sector = sum(data['ss_sector_floor_area_by'][region_name].values())
        reg_disaggregation_factor = (1 / national_floorarea_sector) * reg_floorarea_sector

        reg_fuel_sector_enduse = reg_disaggregation_factor * fuel_national

        fueldata_disagg[region_name] = reg_fuel_sector_enduse

    return fueldata_disagg

def scrap_ag_disaggregate(data, fuel_national):
    """TODO: Disaggregate according to area
    """
    fueldata_disagg = {}

    national_floorarea_sector = 0
    for region_name in data['lu_reg']:
        national_floorarea_sector += sum(data['ss_sector_floor_area_by'][region_name].values())

    # Iterate regions
    for region_name in data['lu_reg']:
        fueldata_disagg[region_name] = {}
        reg_floorarea_sector = sum(data['ss_sector_floor_area_by'][region_name].values())
        reg_disaggregation_factor = (1 / national_floorarea_sector) * reg_floorarea_sector

        reg_fuel_sector_enduse = reg_disaggregation_factor * fuel_national

        fueldata_disagg[region_name] = reg_fuel_sector_enduse

    return fueldata_disagg

def is_disaggregate(data, raw_fuel_sectors_enduses):
    """TODO: Disaggregate fuel for sector and enduses with floor
    area and GVA for sectors and enduses (IMPROVE)

    #TODO: DISAGGREGATE WITH OTHER DATA
    """
    is_fueldata_disagg = {}

    national_floorarea_sector = 0
    for region_name in data['lu_reg']:
        national_floorarea_sector += sum(data['ss_sector_floor_area_by'][region_name].values())

    # Iterate regions
    for region_name in data['lu_reg']:
        is_fueldata_disagg[region_name] = {}

        # Iterate sector
        for sector in data['is_sectors']:
            is_fueldata_disagg[region_name][sector] = {}

            # Sector specifid info
            reg_floorarea_sector = sum(data['ss_sector_floor_area_by'][region_name].values())

            # Iterate enduse
            for enduse in data['is_all_enduses']:
                national_fuel_sector_by = raw_fuel_sectors_enduses[sector][enduse]

                #print("national_fuel_sector_by: " + str(national_fuel_sector_by))
                # ----------------------
                # Disaggregating factors
                # TODO: IMPROVE. SHOW HOW IS DISAGGREGATED
                reg_disaggregation_factor = (1 / national_floorarea_sector) * reg_floorarea_sector

                # Disaggregated national fuel
                reg_fuel_sector_enduse = reg_disaggregation_factor * national_fuel_sector_by

                is_fueldata_disagg[region_name][sector][enduse] = reg_fuel_sector_enduse

    return is_fueldata_disagg

def rs_disaggregate(data, rs_national_fuel):
    """Disaggregate residential fuel demand

    Parameters
    ----------
    data : dict
        Data container
    rs_national_fuel : dict
        Fuel per enduse for residential submodel

    Returns
    -------
    rs_fueldata_disagg : dict
        Disaggregated fuel per enduse for every region (fuel[region][enduse])
    Info
    -----
    Used disaggregation factors for residential according to enduse (see Section XY Documentation TODO)
    """
    print("...disagreggate residential demand")

    # ---------------------------------------
    # Calculate heating degree days for regions
    # ---------------------------------------
    rs_hdd_individ_region = hdd_cdd.get_hdd_country(data['lu_reg'], data, 'rs_t_base_heating')
    
    total_pop = sum(data['population'][data['base_sim_param']['base_yr']].values()) # Total population
    # ---------------------------------------
    # Overall disaggregation factors per enduse
    # ---------------------------------------
    f_rs_lighting = 0
    fs_rs_cold = 0
    fs_rs_wet = 0
    fs_rs_consumer_electronics = 0
    fs_rs_home_computing = 0
    fs_rs_cooking = 0
    f_rs_space_heating = 0
    fs_rs_water_heating = 0

    for region_name in data['lu_reg']:

        # HDD
        reg_hdd = rs_hdd_individ_region[region_name]

        # Floor Area across all sectors
        reg_floor_area = data['rs_floorarea'][region_name]

        # Population
        reg_pop = data['population'][data['base_sim_param']['base_yr']][region_name]

        # National dissagregation factors
        f_rs_lighting += reg_floor_area
        fs_rs_cold += reg_pop
        fs_rs_wet += reg_pop
        fs_rs_consumer_electronics += reg_pop
        fs_rs_home_computing += reg_pop
        fs_rs_cooking += reg_pop
        f_rs_space_heating += reg_hdd * reg_floor_area
        fs_rs_water_heating += reg_pop

    # --------------------------------------- 
    # Disaggregate according to enduse
    # ---------------------------------------
    rs_fueldata_disagg = {}
    for region_name in data['lu_reg']:
        rs_fueldata_disagg[region_name] = {}

        reg_pop = data['population'][data['base_sim_param']['base_yr']][region_name]
        reg_hdd = rs_hdd_individ_region[region_name]
        reg_floor_area = data['rs_floorarea'][region_name]

        # Disaggregate fuel depending on end_use
        for enduse in rs_national_fuel:
            if enduse == 'rs_lighting':
                reg_diasg_factor = reg_floor_area / f_rs_lighting
            elif enduse == 'rs_cold':
                reg_diasg_factor = reg_pop / fs_rs_cold
            elif enduse == 'rs_wet':
                reg_diasg_factor = reg_pop / fs_rs_wet
            elif enduse == 'rs_consumer_electronics':
                reg_diasg_factor = reg_pop / fs_rs_consumer_electronics
            elif enduse == 'rs_home_computing':
                reg_diasg_factor = reg_pop / fs_rs_home_computing
            elif enduse == 'rs_cooking':
                reg_diasg_factor = reg_pop / fs_rs_cooking
            elif enduse == 're_space_heating':
                reg_diasg_factor = (reg_hdd * reg_floor_area) / f_rs_space_heating
            elif enduse == 'rs_water_heating':
                reg_diasg_factor = reg_pop / fs_rs_water_heating
            else:
                reg_diasg_factor = reg_pop / total_pop

            # Disaggregate
            rs_fueldata_disagg[region_name][enduse] = rs_national_fuel[enduse] * reg_diasg_factor
  
    return rs_fueldata_disagg
