"""This scripts reads the national electricity data for the base year"""
# pylint: disable=I0011,C0321,C0301,C0103,C0325,no-member
import sys
import csv
import numpy as np
from math import factorial
import matplotlib.pyplot as plt
from energy_demand.scripts_basic import date_handling
from energy_demand.scripts_basic import unit_conversions
#from energy_demand.scripts_technologies import diffusion_technologies as diffusion

def get_month_from_string(month_string):
    """Convert string month to int month with Jan == 1
    """
    if month_string == 'Jan':
        month_int = 1
    elif month_string == 'Feb':
        month_int = 2
    elif month_string == 'Mar':
        month_int = 3
    elif month_string == 'Apr':
        month_int = 4
    elif month_string == 'May':
        month_int = 5
    elif month_string == 'Jun':
        month_int = 6
    elif month_string == 'Jul':
        month_int = 7
    elif month_string == 'Aug':
        month_int = 8
    elif month_string == 'Sep':
        month_int = 9
    elif month_string == 'Oct':
        month_int = 10
    elif month_string == 'Nov':
        month_int = 11
    elif month_string == 'Dec':
        month_int = 12
    else:
        sys.exit("Could not convert string month to int month")

    return int(month_int)

def read_raw_elec_2015_data(path_to_csv):
    """Read in national electricity values provided in MW and convert to GWh

    Info
    -----
    Half hourly measurements are aggregated to hourly values

    Necessary data preparation: On 29 March and 25 Octobre there are 46 and 48 values because of the changing of the clocks
    The 25 Octobre value is omitted, the 29 March hour interpolated in the csv file
    """
    year = 2015

    elec_data_INDO = np.zeros((365, 24))
    elec_data_ITSDO = np.zeros((365, 24))

    # Read CSV file
    with open(path_to_csv, 'r') as csvfile:
        read_lines = csv.reader(csvfile, delimiter=',') # Read line
        _headings = next(read_lines) # Skip first row

        hour = 0
        counter_half_hour = 0
        # Iterate rows
        for line in read_lines:
            month = get_month_from_string(line[0].split("-")[1])
            day = int(line[0].split("-")[0])

            # Get yearday
            yearday = date_handling.convert_date_to_yearday(year, month, day)

            if counter_half_hour == 1:
                counter_half_hour = 0

                # Sum value of first and second half hour
                hour_elec_demand_INDO = half_hour_demand_INDO + float(line[2]) # INDO - National Demand
                hour_elec_demand_ITSDO  = half_hour_demand_ITSDO + float(line[4]) # ITSDO - Transmission System Demand

                # Convert MW to GWH (input is MW aggregated for two half
                # hourly measurements, therfore divide by 0.5)
                hour_elec_demand_gwh_INDO = unit_conversions.convert_mw_gwh(hour_elec_demand_INDO, 0.5)
                hour_elec_demand_gwh_ITSDO = unit_conversions.convert_mw_gwh(hour_elec_demand_ITSDO, 0.5)

                # Add to array
                #print(" sdf  {}  {}  {}  ".format(yearday, hour, hour_elec_demand_gwh))
                elec_data_INDO[yearday][hour] = hour_elec_demand_gwh_INDO
                elec_data_ITSDO[yearday][hour] = hour_elec_demand_gwh_ITSDO

                hour += 1
            else:
                counter_half_hour += 1

                half_hour_demand_INDO = float(line[2]) # INDO - National Demand
                half_hour_demand_ITSDO = float(line[4]) # Transmission System Demand

            if hour == 24:
                hour = 0

    return elec_data_INDO, elec_data_ITSDO

def compare_results(y_real_array_INDO, y_real_array_ITSDO, y_factored_INDO, y_calculated_array, title_left, days_to_plot):
    """Compare national electrictiy demand data with model results

    Info
    ----
    RMSE fit criteria : Lower values of RMSE indicate better fit
    https://stackoverflow.com/questions/17197492/root-mean-square-error-in-python
    """
    print("...compare elec results")
    def rmse(predictions, targets):
        """RMSE calculations
        """
        return np.sqrt(((predictions - targets) ** 2).mean())

    nr_of_h_to_plot = len(days_to_plot) * 24

    x = range(nr_of_h_to_plot)

    y_real_INDO = []
    y_real_ITSDO = []
    y_real_INDO_factored = []
    y_calculated = []

    for day in days_to_plot:
        for hour in range(24):
            y_real_INDO.append(y_real_array_INDO[day][hour])
            y_real_ITSDO.append(y_real_array_ITSDO[day][hour])
            y_calculated.append(y_calculated_array[day][hour])
            y_real_INDO_factored.append(y_factored_INDO[day][hour])

    # -------------------
    # Smoothing algorithm
    # -------------------
    #y_calculated = savitzky_golay(y_calculated, 3, 3) # window size 51, polynomial order 3

    # RMSE
    rmse_val_INDO = rmse(np.array(y_real_INDO), np.array(y_calculated))
    rmse_val_ITSDO = rmse(np.array(y_real_ITSDO), np.array(y_calculated))
    rmse_val_corrected = rmse(np.array(y_real_INDO_factored), np.array(y_calculated))
    rmse_val_own_factor_correction = rmse(np.array(y_real_INDO), np.array(y_calculated))

    # R squared
    #slope, intercept, r_value, p_value, std_err = stats.linregress(np.array(y_real_INDO), np.array(y_calculated))

    # plot points
    plt.plot(x, y_real_INDO, color='black', label='TD') #'ro', markersize=1
    plt.plot(x, y_real_ITSDO, color='grey', label='TSD') #'ro', markersize=1
    plt.plot(x, y_real_INDO_factored, color='green', label='TD_factored') #'ro', markersize=1
    plt.plot(x, y_calculated, color='red', label='modelled') #'ro', markersize=1

    plt.xlim([0, 8760])
    plt.title('RMSE (TD): {}  RMSE (TSD):  {} RMSE (factored TSD): {}'.format(rmse_val_INDO, rmse_val_ITSDO, rmse_val_corrected))
    plt.title(title_left, loc='left')
    #plt.title('Right Title', loc='right')
    plt.xlabel("Hours")
    plt.ylabel("National electrictiy use [GWh]")
    plt.axis('tight')

    plt.legend()

    plt.show()

def compare_peak(validation_elec_data_2015, peak_all_models_all_enduses_fueltype):
    """Compare Peak electricity day with calculated peak energy demand
    """
    print("...compare elec peak results")
    # -------------------------------
    # Find maximumg peak in real data
    # -------------------------------
    max_h_year = 0
    max_day = "None"

    for day in range(365):
        max_h_day = np.max(validation_elec_data_2015[day])

        if max_h_day > max_h_year:
            max_h_year = max_h_day
            max_day = day

    print("Max Peak Day:                    " + str(max_day))
    print("max_h_year (real):               " + str(max_h_year))
    print("max_h_year (modelled):           " + str(np.max(peak_all_models_all_enduses_fueltype)))
    print("Fuel max peak day (real):        " + str(np.sum(validation_elec_data_2015[max_day])))
    print("Fuel max peak day (modelled):    " + str(np.sum(peak_all_models_all_enduses_fueltype)))
    # -------------------------------
    # Compare values
    # -------------------------------
    '''#Scrap
    a = []
    for day in range(365):
        for hour in range(24):
            a.append(validation_elec_data_2015[day][hour])
    plt.plot(range(8760), a, color='green', label='real')
    plt.show()
    '''

    x = range(24)
    plt.plot(x, peak_all_models_all_enduses_fueltype, color='red', label='modelled')
    plt.plot(x, validation_elec_data_2015[max_day], color='green', label='real')

    plt.axis('tight')
    plt.title("Peak day comparison", loc='left')
    plt.xlabel("Hours")
    plt.ylabel("National electrictiy use [GWh]")
    plt.legend()
    plt.show()

def compare_results_hour_boxplots(data_real, data_calculated):
    """Calculate differences for every hour and plot according to hour
    for the full year


    """
    data_h_full_year = {}

    for i in range(24):
        data_h_full_year[i] = []

    for yearday_python in range(365):
        #date_object = date_handling.convert_yearday_to_date(2015, yearday_python) # Yerday
        #month = date_object.timetuple().tm_mon - 1 # Month

        for hour in range(24):

            # Calculate difference in electricity use
            diff = data_real[yearday_python][hour] - data_calculated[yearday_python][hour]

            # Differenc in % of real value
            diff_percent = (100 / data_real[yearday_python][hour]) * data_calculated[yearday_python][hour]
            # Add differene to list of specific hour

            data_h_full_year[hour].append(diff_percent)

    fig = plt.figure()


    ax = fig.add_subplot(111)

    # Add a horizontal grid to the plot, but make it very light in color so we can use it for reading data values but not be distracting
    ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
    ax.axhline(y=100, xmin=0, xmax=3,c="red", linewidth=1, zorder=0)

    diff_values = []
    for hour in range(24):
        diff_values.append(np.asarray(data_h_full_year[hour]))

    ax.boxplot(diff_values)
    plt.xlabel("Hour")
    #plt.ylabel("Modelled electricity difference (real-modelled) [GWh]")
    plt.ylabel("Modelled electricity difference (real-modelled) [%]")

    plt.show()

def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    """Smooth (and optionally differentiate) data with a Savitzky-Golay filter.
    The Savitzky-Golay filter removes high frequency noise from data.
    It has the advantage of preserving the original shape and
    features of the signal better than other types of filtering
    approaches, such as moving averages techniques.

    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).

    Notes
    -----
    The Savitzky-Golay is a type of low-pass filter, particularly
    suited for smoothing noisy data. The main idea behind this
    approach is to make for each point a least-square fit with a
    polynomial of high order over a odd-sized window centered at
    the point.

    Examples
    --------
    t = np.linspace(-4, 4, 500)
    y = np.exp( -t**2 ) + np.random.normal(0, 0.05, t.shape)
    ysg = savitzky_golay(y, window_size=31, order=4)
    import matplotlib.pyplot as plt
    plt.plot(t, y, label='Noisy signal')
    plt.plot(t, np.exp(-t**2), 'k', lw=1.5, label='Original signal')
    plt.plot(t, ysg, 'r', label='Filtered signal')
    plt.legend()
    plt.show()

    References
    ----------
    .. [1] A. Savitzky, M. J. E. Golay, Smoothing and Differentiation of
       Data by Simplified Least Squares Procedures. Analytical
       Chemistry, 1964, 36 (8), pp 1627-1639.
    .. [2] Numerical Recipes 3rd Edition: The Art of Scientific Computing
       W.H. Press, S.A. Teukolsky, W.T. Vetterling, B.P. Flannery
       Cambridge University Press ISBN-13: 9780521880688
    """
    try:
        window_size = np.abs(np.int(window_size))
        order = np.abs(np.int(order))
    except ValueError:
        raise ValueError("window_size and order have to be of type int")
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2

    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))

    return np.convolve( m[::-1], y, mode='valid')