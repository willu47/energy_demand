import numpy as np
from energy_demand.technologies import tech_related

def test_get_tech_type():
    """
    """
    tech_list = { 
        'tech_heating_temp_dep': ['heat_p'],
        'tech_heating_const': ['boilerA'],
        'primary_heating_electricity': ['boilerC'],
        'secondary_heating_electricity': []
    }
    assert tech_related.get_tech_type('dummy_tech', tech_list) == 'dummy_tech'
    assert tech_related.get_tech_type('boilerA', tech_list) == 'boiler_heating_tech'
    assert tech_related.get_tech_type('heat_p', tech_list) == 'heat_pump'
    assert tech_related.get_tech_type('boilerC', tech_list) == 'storage_heating_electricity'
    assert tech_related.get_tech_type('test_tech', tech_list) == 'regular_tech'

def test_calc_eff_cy():
    """
    """
    sim_param = {
        'base_yr': 2015,
        'curr_yr': 2020}

    other_enduse_mode_info = {
        'diff_method': 'linear'},

    out_value = tech_related.calc_eff_cy(
        sim_param=sim_param,
        eff_by= 1.0,
        eff_ey= 2.0,
        yr_until_changed=2020,
        other_enduse_mode_info=other_enduse_mode_info,
        tech_eff_achieved_f=1.0,
        diff_method='linear')

    assert out_value == 2.0

    other_enduse_mode_info = {
        'sigmoid': {'sig_midpoint': 0,'sig_steeppness': 1}}

    out_value = tech_related.calc_eff_cy(
        sim_param=sim_param,
        eff_by= 1.0,
        eff_ey= 2.0,
        yr_until_changed=2020,
        other_enduse_mode_info=other_enduse_mode_info,
        tech_eff_achieved_f=1.0,
        diff_method='sigmoid')

    assert out_value == 2.0

def test_calc_hp_eff():
    """Testing function
    """

    temp_yh = np.zeros((365, 24)) + 10

    efficiency_intersect = 10
    t_base_heating = 15.5

    # call function
    out_value = tech_related.calc_hp_eff(
        temp_yh,
        efficiency_intersect,
        t_base_heating)

    float_value = 1.0
    expected = type(float_value)
    assert type(out_value) == expected

def test_eff_heat_pump():
    """
    """
    t_base = 15.5
    temp_yh = np.zeros((365, 24)) + 5 #make diff 10 degrees
    temp_diff = t_base - temp_yh

    efficiency_intersect = 6 #Efficiency of hp at temp diff of 10 degrees

    out_value = tech_related.eff_heat_pump(temp_diff, efficiency_intersect)

    values_every_h = -0.08 * temp_diff + (efficiency_intersect - (-0.8))
    expected = np.mean(values_every_h)

    assert out_value == expected

def test_get_fueltype_str():
    """Testing function
    """
    lu_fueltypes = {'gas': 1}
    in_value = 1
    expected = 'gas'

    # call function
    out_value = tech_related.get_fueltype_str(lu_fueltypes, in_value)

    assert out_value == expected

def test_get_fueltype_int():
    """Testing function
    """
    lu_fueltypes = {'gas': 1}
    in_value = 'gas'
    expected = 1

    # call function
    out_value = tech_related.get_fueltype_int(lu_fueltypes, in_value)

    assert out_value == expected
