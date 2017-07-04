"""Create chart of correlating HDD with gas demand

Calculate HDD with weather data from a asingle weather station for the whole of the UK.abs
Correlate HDD with national gas data.

National gas data source: National Grid (2015) Seasonal Normal Demand Forecasts
"""
import os
from energy_demand import data_loader_functions as df
from energy_demand import main_functions as mf
from scipy import stats
import matplotlib.pyplot as plt
import numpy as np
from energy_demand.scripts_shape_handling import hdd_cdd
from energy_demand.scripts_data import read_weather_data
from energy_demand.scripts_data import read_weather_data

def cm2inch(*tupl):
    """Convert input cm to inches
    """
    inch = 2.54
    if isinstance(tupl[0], tuple):
        return tuple(i/inch for i in tupl[0])
    else:
        return tuple(i/inch for i in tupl)

# ----------------------------------
# Read temp data and weather station
# ----------------------------------
path_data_temp = os.path.join(r'Z:\01-Data_NISMOD\data_energy_demand', r'16-Met_office_weather_data\midas_wxhrly_201501-201512.csv')
path_data_stations = os.path.join(r'Z:\01-Data_NISMOD\data_energy_demand', r'16-Met_office_weather_data\excel_list_station_details.csv')

# Read temp data
print("...read temp")
temperature_data_raw = read_weather_data.read_weather_data_raw(path_data_temp, 9999)

# Clean raw temperature data
print("...clean temp")
temperature_data = read_weather_data.clean_weather_data_raw(temperature_data_raw, 9999)
        
# Weather stations
print("...weatherstations")
weather_stations = read_weather_data.read_weather_stations_raw(path_data_stations, temperature_data.keys())

# Temperature weather data weater station 
# 595	CHURCH	LAWFORD	WARWICKSHIRE	COUNTY	01/01/1983	Current	52.3584	-1.32987	CV23	9
#593	ELMDON	WEST	MIDLANDS	COUNTY	01/01/1949	Current	52.4524	-1.74099	B26	3				--> slightly better correlation
station_ID_ELMDON = 593 #593
temperatures = temperature_data[station_ID_ELMDON]


# Calculate average day temp
averag_day_temp = []
for day in temperatures:
    averag_day_temp.append(np.mean(day))

# ----------------------------------
# Calculate HDD
# ----------------------------------
print("...calc hdd")
print(temperatures.shape)

t_base_heating = 15.5 # Heating t_base temp

# HDD
hdd_reg = hdd_cdd.calc_hdd(t_base_heating, temperatures)
print("shape hdd  " + str(hdd_reg.shape))
'''
hdd_reg = np.zeros((365))
for weaterstaion in temperature_data.keys():
    print("Station: " + str(weaterstaion))
    print(temperature_data[weaterstaion][:1])
    hdd_reg += hdd_cdd.calc_hdd(t_base_heating, temperature_data[weaterstaion])
'''
# Test if correlation with mean temp is better than with HDd
#hdd_reg = averag_day_temp

# Data

# -- Non daily metered gas demand in mcm == Residential heating gas demand for year 2015 (Jan - Dez --> Across two excel in orig file)
gas_demand_NDM_2015_2016 = [
    2059.3346672,
    2170.0185108,
    2098.5700609,
    2129.0042078,
    2183.3908583,
    2183.3755211,
    2181.77478289999,
    2180.2661608,
    2171.9539465,
    2093.1630535,
    2123.4248103,
    2177.2511151,
    2177.4395409,
    2177.4392085,
    2175.2222323,
    2166.6139387,
    2087.285658,
    2115.1954239,
    2167.4317226,
    2166.5545797,
    2164.694753,
    2163.4837384,
    2157.386435,
    2080.9887003,
    2111.8947958,
    2166.0717924,
    2162.6456414,
    2159.295252,
    2155.8334129,
    2145.8472366,
    2061.1717803,
    2082.3903686,
    2127.0822845,
    2118.2712922,
    2113.193853,
    2107.8898595,
    2095.8412092,
    2014.9440596,
    2049.2258347,
    2107.0791469,
    2112.1583269,
    2117.2396604,
    2123.0313351,
    2122.1358234,
    2051.7066905,
    2087.3670451,
    2136.4535688,
    2132.1460485,
    2128.3906968,
    2124.2843977,
    2105.6629196,
    2019.1113801,
    2036.5569675,
    2077.2039557,
    2061.8101344,
    2046.7869234,
    2031.4318873,
    2005.2602169,
    1914.0892568,
    1922.9069295,
    1954.9594171,
    1933.6480271,
    1912.3061523,
    1890.5476499,
    1862.3706414,
    1775.6671805,
    1783.4502818,
    1814.9200643,
    1796.8545889,
    1784.4710306,
    1771.6500082,
    1752.3369114,
    1674.0247522,
    1687.99816,
    1726.2909774,
    1715.8915875,
    1705.7032311,
    1692.0716697,
    1671.1552101,
    1594.1241588,
    1603.713891,
    1636.247885,
    1620.6947572,
    1605.2659081,
    1590.0104955,
    1569.4656755,
    1494.5719877,
    1502.5278704,
    1535.2362037,
    1526.2747126,
    1513.4608687,
    1504.8484041,
    1490.7666095,
    1325.9250159,
    1316.9165572,
    1462.4932465,
    1458.1802196,
    1442.6262542,
    1426.8417784,
    1411.3589019,
    1335.8538668,
    1333.6755582,
    1356.6697705,
    1334.994619,
    1313.3468669,
    1291.2764263,
    1261.7044342,
    1187.3254679,
    1182.7090036,
    1206.201116,
    1187.9607269,
    1169.0975458,
    1150.8622665,
    1125.7570188,
    1059.6150794,
    1057.5077396,
    1081.4643041,
    1065.2552632,
    1049.0529795,
    1032.9539024,
    1007.1793016,
    914.58361712,
    897.87864486,
    880.61178046,
    909.11557166,
    890.86945346,
    871.96514751,
    853.8612021,
    791.8538562,
    775.11686001,
    832.03363633,
    814.21901615,
    799.58233329,
    784.71165334,
    761.63725303,
    707.19260431,
    704.66692408,
    729.32567359,
    716.8394616,
    704.16329367,
    692.60720982,
    673.62744381,
    625.16539826,
    616.31467523,
    606.17192685,
    636.72436643,
    625.93400599,
    615.10886486,
    605.22026297,
    557.46992056,
    551.34168138,
    578.47909485,
    570.13253752,
    561.78823047,
    553.3654021,
    538.91778989,
    498.94506464,
    500.61103512,
    529.17638846,
    522.76561207,
    516.42800386,
    510.56638091,
    496.03207692,
    456.62523814,
    456.93248186,
    484.57825041,
    478.35283027,
    472.67018165,
    467.07413108,
    452.94073995,
    415.61047941,
    417.54936646,
    447.87992936,
    444.32552312,
    440.34388174,
    436.93497309,
    425.39778941,
    390.98147195,
    393.27803263,
    422.2499116,
    418.01587597,
    413.61939995,
    409.40057065,
    397.24314025,
    362.84744615,
    363.93696426,
    393.56430501,
    390.46598983,
    387.50245828,
    384.08572436,
    373.79849944,
    341.87745791,
    344.96303388,
    375.65480602,
    374.49215286,
    372.75648874,
    371.74226978,
    361.8690835,
    331.52439876,
    335.15290392,
    366.77742567,
    365.12052235,
    364.02193295,
    362.52261752,
    352.52451205,
    322.45011946,
    326.07034766,
    357.85885375,
    357.46873061,
    356.17585959,
    356.18529447,
    347.76795445,
    318.87093053,
    323.44991194,
    357.14307241,
    358.48343406,
    359.41495,
    360.13619174,
    352.30573134,
    323.75524954,
    328.47959503,
    361.26301948,
    361.91381511,
    362.52822042,
    363.04084256,
    354.83105903,
    327.4003489,
    333.7913569,
    367.75844026,
    369.11519087,
    372.6949059,
    375.8462941,
    371.01068634,
    344.6986732,
    353.4825506,
    390.13714534,
    393.84951909,
    397.83499025,
    401.57927692,
    396.97028525,
    370.21486247,
    379.29129941,
    416.16743945,
    420.07485221,
    423.97519461,
    429.74321627,
    427.2986801,
    401.46194542,
    413.22870233,
    456.07775396,
    465.3295712,
    474.21723331,
    483.12391875,
    484.18266475,
    461.009664,
    476.92695202,
    521.59453157,
    530.84505032,
    540.18546168,
    549.72258375,
    551.25306059,
    525.45532919,
    542.29079386,
    587.07994975,
    596.34233521,
    607.50869098,
    618.97893781,
    622.86393906,
    597.19837803,
    621.39030489,
    674.41691171,
    690.65537739,
    706.66602486,
    750.44401705,
    761.5020047,
    735.3577927,
    758.94313283,
    820.97761046,
    841.64549132,
    862.82785312,
    882.73942176,
    895.8174329,
    867.22285798,
    895.86950089,
    962.4264397,
    986.21496809,
    1010.5025124,
    1034.947993,
    1049.36376,
    1016.2553526,
    1045.7292098,
    1113.1746337,
    1125.8164178,
    1141.3139762,
    1159.7889682,
    1167.2284687,
    1125.5987857,
    1158.1749163,
    1228.6271493,
    1250.8619219,
    1276.6254017,
    1300.3160004,
    1317.8170358,
    1282.8879339,
    1320.3942354,
    1394.2587548,
    1416.5190559,
    1438.5435458,
    1461.7634807,
    1479.7562971,
    1438.8539543,
    1478.9216764,
    1557.1207719,
    1573.4090718,
    1587.6655331,
    1603.6341589,
    1613.333634,
    1562.3586478,
    1600.277806,
    1679.9344601,
    1697.4619665,
    1712.8552817,
    1724.7516139,
    1724.0138982,
    1657.0594241,
    1682.3440925,
    1748.5809406,
    1752.9203251,
    1763.9782637,
    1775.1642524,
    1782.4227695,
    1722.1387718,
    1761.2175743,
    1843.516748,
    1861.6814774,
    1873.721509,
    1884.7695907,
    1889.1761128,
    1820.2893554,
    1849.3759024,
    1927.6865797,
    1941.1637845,
    1949.9179591,
    1955.9424808,
    1956.9521671,
    1880.0208367,
    1906.0644726,
    1980.6623416,
    1988.0433795,
    1992.2170495,
    2003.9919664,
    2009.5777063,
    1937.9896745,
    1964.8414739,
    2036.894857,
    2044.9981179,
    2053.3450878,
    1974.8040044,
    1814.6135915,
    1904.8874509,
    1909.229843,
    1911.2513971,
    1995.545462,
    1995.3479943,
    1997.4328038
    ]


# ----------------
# Linear regression
# ----------------
def lin_func(x, slope, intercept):
    y = slope * x + intercept
    return y

print("...regression")
slope, intercept, r_value, p_value, std_err = stats.linregress(gas_demand_NDM_2015_2016, hdd_reg)

print("Slope:         " + str(slope))
print("intercept:     " + str(intercept))
print("r_value:       " + str(r_value))
print("p_value:       " + str(p_value))
print("std_err:       " + str(std_err))

# Set figure size in cm
plt.figure(figsize=cm2inch(10, 10))

# plot points
plt.plot(gas_demand_NDM_2015_2016, hdd_reg, 'ro', markersize=5, color='gray')

# plot line
#plt.plot(gas_demand_NDM_2015_2016, hdd_reg, 'ro')

# Plot regression line
X_plot = np.linspace(300, 2250, 500)

Y_plot = []
for x in X_plot:
    Y_plot.append(lin_func(x, slope, intercept))

plt.plot(X_plot, Y_plot, color='k')
#plt.axis([0, 6, 0, 20])



plt.xlabel("National gas demand [GWh]")
plt.ylabel("Heating degree days")
plt.title("Correlation between national gas demand and hdd (r_value:  {}".format(r_value))
plt.show()
