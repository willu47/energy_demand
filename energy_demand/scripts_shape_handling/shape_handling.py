"""Functions related to load profiles
"""
import sys
import numpy as np

class LoadProfileStock(object):
    """Collection of load shapes in a list
    """
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.load_profile_list = []

    def add_load_profile(
            self,
            technologies,
            enduses,
            sectors,
            shape_yd=np.zeros((365)),
            shape_yh=np.zeros((365, 24)),
            enduse_peak_yd_factor=1/365,
            shape_peak_dh=np.ones((24))
        ):
        """Add load profile to stock

        Parameters
        ----------
        technologies : list
            Technologies for which the profile applies
        enduses : list
            Enduses for which the profile applies
        sectors : list
            Sectors for which the profile applies
        shape_yd : array
            Shape yd (from year to day)
        shape_yh : array
            Shape yh (from year to hour)
        enduse_peak_yd_factor : float
            Factor to calculate daily demand from yearly demand
            Standard value is average daily amount
        shape_peak_dh : array
            Shape (dh), shape of a day for every hour
        """
        loadprofile_obj = LoadProfile(
            technologies,
            enduses,
            sectors,
            shape_yd,
            shape_yh,
            enduse_peak_yd_factor,
            shape_peak_dh
            )

        self.load_profile_list.append(loadprofile_obj)

    def get_load_profile(self, enduse, sector, technology, shape):
        """Get shape for a certain technology, enduse and sector

        Parameters
        ----------
        enduse : str
            Enduse
        sector : str
            Sector
        technology : str
            technology
        shape : str
            Type of shape which is to be read out

        Return
        ------
        attr_to_get : array
            Required shape
        """
        for load_profile_obj in self.load_profile_list:

            # Multiple conditions
            if enduse in load_profile_obj.enduses:
                if sector in load_profile_obj.sectors:
                    if technology in load_profile_obj.technologies:

                        if shape == 'shape_yh':
                            return load_profile_obj.shape_yh
                        elif shape == 'shape_yd':
                            return load_profile_obj.shape_yd
                        elif shape == 'enduse_peak_yd_factor':
                            return load_profile_obj.enduse_peak_yd_factor

        #function_run_crit = False
            '''if (technology in load_profile_obj.technologies
                    and enduse in load_profile_obj.enduses
                    and sector in load_profile_obj.sectors):
            
                # SPEED: Slow version
                attr_to_get = getattr(load_profile_obj, shape)
                function_run_crit = True
                return attr_to_get
            '''
        '''if function_run_crit:
            return attr_to_get
        else:
            sys.exit("Error in get_load_profile: {} {} {} {}".format(
                enduse,
                sector,
                technology,
                shape))
        '''


    def get_shape_peak_dh(self, enduse, sector, technology):
        """Get peak dh shape for a certain technology, enduse and sector
        """
        for load_profile_obj in self.load_profile_list:

            if (technology in load_profile_obj.technologies
                    and enduse in load_profile_obj.enduses
                    and sector in load_profile_obj.sectors):

                # Test if dummy sector and thus shape_peak not provided for different sectors
                if sector == 'dummy_sector':
                    shape_peak_dh = load_profile_obj.shape_peak_dh
                    return shape_peak_dh
                else:
                    #attr_all_sectors = load_profile_obj.shape_peak_dh
                    #shape_peak_dh = attr_all_sectors[sector][enduse]['shape_peak_dh']
                    shape_peak_dh = load_profile_obj.shape_peak_dh[sector][enduse]['shape_peak_dh']
                    return shape_peak_dh

class LoadProfile(object):
    """Load profile container to store different shapes

    Parameters
    ----------
    technologies : list
        Technologies for which the profile applies
    enduses : list
        Enduses for which the profile applies
    sectors : list
        Sectors for which the profile applies
    shape_yd : array
        Shape yd (from year to day)
    shape_yh : array
        Shape yh (from year to hour)
    enduse_peak_yd_factor : float
        Factor to calculate daily demand from yearly demand
        Standard value is average daily amount
    shape_peak_dh : array
        Shape (dh), shape of a day for every hour
    """
    def __init__(
            self,
            technologies,
            enduses,
            sectors,
            shape_yd,
            shape_yh,
            enduse_peak_yd_factor,
            shape_peak_dh=np.ones((24))
        ):
        """Constructor
        """
        #self.region
        self.technologies = technologies
        self.enduses = enduses
        self.sectors = sectors
        self.shape_yd = shape_yd
        self.shape_yh = shape_yh
        self.shape_peak_dh = shape_peak_dh
        self.enduse_peak_yd_factor = enduse_peak_yd_factor

def absolute_to_relative(absolute_array):
    """Convert absolute numbers in an array to relative

    If the total sum is zero, return an array with zeros and raise a warning

    Parameters
    ----------
    absolute_array : array
        Contains absolute numbers in it

    Returns
    -------
    relative_array : array
        Contains relative numbers
    """
    try:
        relative_array = np.nan_to_num((1 / np.sum(absolute_array)) * absolute_array)
    except ZeroDivisionError:
        relative_array = absolute_array # If the total sum is zero, return same array

    return relative_array

def convert_dh_yd_to_yh(shape_yd, shape_y_dh):
    """Convert yd shape and shape for every day (y_dh) into yh

    Parameters
    ----------
    shape_yd : array
        Array with yd shape
    shape_y_dh : array
        Array with y_dh shape

    Return
    ------
    shape_yh : array
        Array with yh shape
    """
    shape_yh = np.zeros((365, 24))
    for day, value_yd in enumerate(shape_yd):
        shape_yh[day] = value_yd * shape_y_dh[day]

    return shape_yh

def get_hybrid_fuel_shapes_y_dh(fuel_shape_boilers_y_dh, fuel_shape_hp_y_dh, tech_low_high_p):
    """Calculate  fuel shapes for hybrid technologies for every day in a year (y_dh)

    Depending on the share of service each hybrid technology in every hour,
    the daily fuelshapes of each technology are taken for every hour respectively

    #TODO: IMPROVE DESCRITPION

    Parameters
    ----------
    fuel_shape_boilers_y_dh : array
        Fuel shape of low temperature technology (e.g. boiler technology)
    fuel_shape_hp_y_dh : array
        Fuel shape of high temp technology (y_dh) (heat pump technology)
    tech_low_high_p : array
        Share of service of technology in every hour (heat pump technology)

    Return
    ------
    fuel_shapes_hybrid_y_dh : array
        Fuel shape (y_dh) for hybrid technology

    Example
    --------
    E.g. 0-12, 16-24:   TechA
         12-16          TechA 50%, TechB 50%

    The daily shape is taken for TechA for 0-12 and weighted according to efficency
    Between 12 and Tech A and TechB are taken with 50% shares and weighted with either efficiency

    Info
    ----
    In case no fuel is provided for a day 'fuel_shapes_hybrid_y_dh' for this day is zero. Therfore
    the total sum of 'fuel_shapes_hybrid_y_dh not necessarily 365.
    """
    '''fuel_shapes_hybrid_y_dh = np.zeros((365, 24))

    for day in range(365): #SPEED
        dh_fuel_hybrid = np.zeros(24)
        for hour in range(24): #SPEED

            # Shares of each technology for every hour
            low_p = tech_low_high_p['low'][day][hour]
            high_p = tech_low_high_p['high'][day][hour]

            # Calculate fuel for every hour
            if low_p == 0:
                fuel_boiler = 0
            else:
                fuel_boiler = low_p * fuel_shape_boilers_y_dh[day][hour]

            if high_p == 0:
                fuel_hp = 0
            else:
                fuel_hp = high_p * fuel_shape_hp_y_dh[day][hour]

            # Weighted hourly dh shape with efficiencies
            dh_fuel_hybrid[hour] = fuel_boiler + fuel_hp

        # Normalise dh shape
        fuel_shapes_hybrid_y_dh[day] = absolute_to_relative(dh_fuel_hybrid)
    '''
    # FAST TODO #(share of fuel boiler * fuel shape boiler) + (share of fuel heat pump * shape of heat pump)
    _var = (tech_low_high_p['low'] * fuel_shape_boilers_y_dh) + (tech_low_high_p['high'] * fuel_shape_hp_y_dh)

    # Absolute to relative for every row
    fuel_shapes_hybrid_y_dh = np.apply_along_axis(absolute_to_relative, 1, _var) 

    '''plt.plot(fuel_shapes_hybrid_y_dh[1])
    plt.show()
    '''
    return fuel_shapes_hybrid_y_dh
