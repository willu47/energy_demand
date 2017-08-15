"""Functions related to load profiles
"""
import numpy as np
# pylint: disable=I0011,C0321,C0301,C0103,C0325,no-member

class LoadProfileStock(object):
    """Collection of load shapes in a list

    Parameters
    ----------
    stock_name : string
        Load profile stock name
    """
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.load_profile_dict = {}
        self.dict_with_tuple_keys = {} # dict_with_tuple_keys

        self.enduses_in_stock = set([])

    def get_all_enduses_in_stock(self):
        """Update the list of the object with all enduses for which load profies are provided
        """
        all_enduses = set([])

        for profile_obj in self.load_profile_dict.values():
            for enduse in profile_obj.enduses:
                all_enduses.add(enduse)

        #setattr(self, 'enduses_in_stock', list(all_enduses))
        setattr(self, 'enduses_in_stock', all_enduses)

    def add_load_profile(self, unique_identifier, technologies, enduses, sectors, shape_yd=np.zeros((365)), shape_yh=np.zeros((365, 24)), enduse_peak_yd_factor=1/365, shape_peak_dh=np.ones((24))):
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
        self.load_profile_dict[unique_identifier] = LoadProfile(
            enduses,
            unique_identifier,
            shape_yd,
            shape_yh,
            enduse_peak_yd_factor,
            shape_peak_dh
            )

        # Generate lookup dictionary with triple key
        self.generate_dict_with_tuple_keys(unique_identifier, enduses, sectors, technologies)

        # Update enduses in stock
        self.get_all_enduses_in_stock()

    def generate_dict_with_tuple_keys(self, unique_identifier, enduses, sectors, technologies):
        """Generate look_up keys to position in 'load_profile_dict'

        Parameters
        ----------
        unique_identifier : string
            Unique identifier of load shape object
        enduses : list
            List with enduses
        sectors : list
            List with sectors
        technologies : list
            List with technologies
        """
        for enduse in enduses:
            for sector in sectors:
                for technology in technologies:
                    self.dict_with_tuple_keys[(enduse, sector, technology)] = unique_identifier

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
            Type of shape which is to be read out from 'load_profile_dict'

        Return
        ------
        Load profile
        """
        # Get key from lookup dict
        position_in_dict = self.dict_with_tuple_keys[(enduse, sector, technology)]

        # Get correct object
        load_profile_obj = self.load_profile_dict[position_in_dict]

        if shape == 'shape_yh':
            return load_profile_obj.shape_yh
        elif shape == 'shape_yd':
            return load_profile_obj.shape_yd
        elif shape == 'shape_y_dh':
            return load_profile_obj.shape_y_dh
        elif shape == 'enduse_peak_yd_factor':
            return load_profile_obj.enduse_peak_yd_factor

    def get_shape_peak_dh(self, enduse, sector, technology):
        """Get peak dh shape for a certain technology, enduse and sector

        Parameters
        ----------
        enduse : str
            Enduse
        sector : str
            Sector
        technology : str
            technology
        """
        position_in_dict = self.dict_with_tuple_keys[(enduse, sector, technology)]
        load_profile_obj = self.load_profile_dict[position_in_dict]

        # Test if dummy sector and thus shape_peak not provided for different sectors
        if sector == 'dummy_sector':
            shape_peak_dh = load_profile_obj.shape_peak_dh

            return shape_peak_dh
        else:
            shape_peak_dh = load_profile_obj.shape_peak_dh[sector][enduse]['shape_peak_dh']

            return shape_peak_dh

class LoadProfile(object):
    """Load profile container to store different shapes

    Parameters
    ----------
    unique_identifier : string
        Unique identifer for LoadProfile object
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
    def __init__(self, enduses, unique_identifier, shape_yd, shape_yh, enduse_peak_yd_factor, shape_peak_dh=np.ones((24))):
        """Constructor
        """
        self.unique_identifier = unique_identifier
        self.enduses = enduses


        self.shape_yd = shape_yd
        self.shape_yh = shape_yh
        self.shape_peak_dh = shape_peak_dh
        self.enduse_peak_yd_factor = enduse_peak_yd_factor

        # Calculate percentage for every day
        self.shape_y_dh = self.calc_y_dh_shape_from_yh()

    def calc_y_dh_shape_from_yh(self):
        """Calculate shape for every day

        Returns
        -------
        shape_y_dh : array
            Shape for every day
        Info
        ----
        The output gives the shape for every day in a year (total sum == 365)
        Within each day, the sum is 1
        """
        sum_every_day_p = 1 / np.sum(self.shape_yh, axis=1)

        # Replace inf by zero
        sum_every_day_p[np.isinf(sum_every_day_p)] = 0

        # Multiply (365,) + with (365, 24)
        shape_y_dh = sum_every_day_p[:, np.newaxis] * self.shape_yh

        # Replace nan by zero (faster than np.nan_to_num)
        shape_y_dh[np.isnan(shape_y_dh)] = 0

        return shape_y_dh

def absolute_to_relative_without_nan(absolute_array):
    """Convert absolute to relative (without correcting the NaN values)
    """
    try:
        return (1 / np.sum(absolute_array)) * absolute_array
    except ZeroDivisionError:
        return absolute_array # If the total sum is zero, return same array

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
        relative_array = (1 / np.sum(absolute_array)) * absolute_array
        relative_array[np.isnan(relative_array)] = 0 # replace nan by zero, faster than np.nan_to_num

    except ZeroDivisionError: # a[np.isinf(a)] = 0   # replace inf by zero (not necessary because ZeroDivsionError)
        relative_array = absolute_array # If the total sum is zero, return same array

    return relative_array

def calk_peak_h_dh(enduse_fuel_peak_dh):
    """Ger peak hour in peak day

    Parameters
    ----------
    enduse_fuel_peak_dh : array
        Fuel of peak day

    Return
    ------
    peak_fueltype_h : array
        Fuel for maximum hour in peak day per fueltype
    """
    # Get maximum value per row (maximum fuel hour per fueltype)
    peak_fueltype_h = np.max(enduse_fuel_peak_dh, axis=1)

    return peak_fueltype_h

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

    # (share of fuel boiler * fuel shape boiler) + (share of fuel heat pump * shape of heat pump)
    _var = (tech_low_high_p['low'] * fuel_shape_boilers_y_dh) + (tech_low_high_p['high'] * fuel_shape_hp_y_dh)

    # Absolute to relative for every row
    fuel_shapes_hybrid_y_dh = np.apply_along_axis(absolute_to_relative, 1, _var) #absolute_to_relative_without_nan not possible
    '''plt.plot(fuel_shapes_hybrid_y_dh[1])
    plt.show()
    '''
    return fuel_shapes_hybrid_y_dh

def calc_fueltype_share_yh_all_h(fueltypes_yh_p_cy):
    """Calculate fuel share for every hour

    Parameters
    ----------
    fueltypes_yh_p_cy : array
        Fuel share per fueltype for every day and hour (7, 365, 24)

    Returns
    -------
    fueltype_share_yh_all_h : array (7)
        Sum of fuel share for every hour
    """
    average_share_in_a_year = (1.0 / 8760)

    # Sum across rows (share of fuel per hour per fueltype) (7, 24)
    fueltypes_tech_share_yh_24 = np.sum(fueltypes_yh_p_cy, axis=1)

    # Sum across rows (overall share of fuel per fueltype) (7,)
    fueltype_share_yh_all_h = np.sum(fueltypes_tech_share_yh_24, axis=1)

    fueltype_share_yh_all_h *= average_share_in_a_year

    return fueltype_share_yh_all_h
