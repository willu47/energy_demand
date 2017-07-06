import numpy as np

def calc_load_factor_h(data, fuels_tot_enduses_h, rs_fuels_peak_h):
    """Calculate load factor of a h in a year from peak data(peak hour compared to all hours in a year)
    self.rs_fuels_peak_h     :   Fuels for peak day (fueltype, data)
    self.rs_fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

    Return
    ------
    load_factor_h : array
        Array with load factor for every fuel type [in %]

    Info
    -----
    Load factor = average load / maximum load in given time period
    Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
    """
    load_factor_h = np.zeros((data['nr_of_fueltypes']))

    # Iterate fueltypes to calculate load factors for each fueltype
    for fueltype, fuels in enumerate(fuels_tot_enduses_h):

        # Maximum fuel of an hour of the peak day
        maximum_h_of_day = rs_fuels_peak_h[fueltype]

        #Calculate average in full year
        average_demand_h = np.mean(fuels)

        # If there is a maximum day hour
        if maximum_h_of_day != 0:
            load_factor_h[fueltype] = average_demand_h / maximum_h_of_day # Calculate load factor

    # Convert load factor to %
    load_factor_h *= 100

    return load_factor_h


def load_factor_d_non_peak(self, data):
    """Calculate load factor of a day in a year from non-peak data
    self.fuels_peak_d     :   Fuels for peak day (fueltype, data)
    self.rs_fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

    Return
    ------
    lf_d : array
            Array with load factor for every fuel type in %

    Info
    -----
    Load factor = average load / maximum load in given time period

    Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
    """
    lf_d = np.zeros((data['nr_of_fueltypes']))

    # Iterate fueltypes to calculate load factors for each fueltype
    for k, fueldata in enumerate(self.rs_fuels_tot_enduses_d):

        average_demand = sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days
        max_demand_d = max(fueldata)

        if  max_demand_d != 0:
            lf_d[k] = average_demand / max_demand_d # Calculate load factor

    lf_d = lf_d * 100 # Convert load factor to %

    return lf_d

def load_factor_h_non_peak(self, data):
    """Calculate load factor of a h in a year from non-peak data

    self.rs_fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data)

    Return
    ------
    load_factor_h : array
        Array with load factor for every fuel type [in %]

    Info
    -----
    Load factor = average load / maximum load in given time period

    Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
    """
    load_factor_h = np.zeros((data['nr_of_fueltypes'], 1)) # Initialise array to store fuel

    # Iterate fueltypes to calculate load factors for each fueltype
    for fueltype, fueldata in enumerate(self.fuels_tot_enduses_h):

        '''all_hours = []
        for day_hours in self.fuels_tot_enduses_h[fueltype]:
                for h in day_hours:
                    all_hours.append(h)
        maximum_h_of_day_in_year = max(all_hours)
        '''
        maximum_h_of_day_in_year = self.rs_fuels_peak_h[fueltype]

        average_demand_h = np.sum(fueldata) / (365 * 24) # Averae load = yearly demand / nr of days

        # If there is a maximum day hour
        if maximum_h_of_day_in_year != 0:
            load_factor_h[fueltype] = average_demand_h / maximum_h_of_day_in_year # Calculate load factor

    # Convert load factor to %
    load_factor_h *= 100

    return load_factor_h

def load_factor_d(self, data):
    """Calculate load factor of a day in a year from peak values
    self.fuels_peak_d     :   Fuels for peak day (fueltype, data)
    self.rs_fuels_tot_enduses_d    :   Hourly fuel for different fueltypes (fueltype, 24 hours data) for full year

    Retrn
    ------
    lf_d : array
            Array with load factor for every fuel type in %

    Info
    -----
    Load factor = average load / maximum load in given time period

    Info: https://en.wikipedia.org/wiki/Load_factor_(electrical)
    """
    lf_d = np.zeros((data['nr_of_fueltypes']))

    # Get day with maximum demand (in percentage of year)
    peak_d_demand = self.fuels_peak_d

    # Iterate fueltypes to calculate load factors for each fueltype
    for k, fueldata in enumerate(self.rs_fuels_tot_enduses_d):
        average_demand = np.sum(fueldata) / 365 # Averae_demand = yearly demand / nr of days

        if average_demand != 0:
            lf_d[k] = average_demand / peak_d_demand[k] # Calculate load factor

    lf_d = lf_d * 100 # Convert load factor to %

    return lf_d
        