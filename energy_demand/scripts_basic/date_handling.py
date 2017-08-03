"""Functions related to dates
"""
from datetime import date
from datetime import timedelta
from isoweek import Week

def get_dates_week_nr(year, week_nr):
    """Get all dates from a week_nr in a list (for base year)

    Parameters
    ----------
    year : int
        Year
    week_nr : int
        ISO week number

    Returns
    -------
    list_days : list
        Constaings date objects for ISO week

    Note
    -----
    if year is a leap year, funciton may not work properly
    """
    list_days = []

    monday_in_week = Week(year, week_nr).monday()

    for day in range(1, 8):
        list_days.append(monday_in_week + timedelta(days=day))

    return list_days

def convert_date_to_yearday(year, month, day):
    """Gets the yearday (julian year day) of a year minus one to correct because of python iteration
    TESTED_PYTEST

    Parameters
    ----------
    date_base_yr : int
        Year
    date_base_yr : int
        Month
    day : int
        Day

    Example
    -------
    5. January 2015 --> Day nr 5 in year --> -1 because of python --> Out: 4
    """
    date_y = date(year, month, day)
    yearday = date_y.timetuple().tm_yday - 1 #: correct because of python iterations

    return yearday

def convert_yearday_to_date(year, yearday_python):
    """Gets the yearday of a year minus one to correct because of python iteration
    TESTED_PYTEST

    Parameters
    ----------
    year : int
        Year
    yearday_python : int
        Yearday - 1
    """
    date_first_jan = date(year, 1, 1)
    date_new = date_first_jan + timedelta(yearday_python)

    return date_new

def get_weekday_type(date_from_yearday, bank_holidays="not_globally_defined"):
    """Gets the weekday of a date
    TESTED_PYTEST

    Also bank holidays for the base year are defined (including whole week of christmas)
    Parameters
    ----------
    date_from_yearday : date
        Date of a day in ayear

    Returns
    -------
    daytype : int
        If 1: holiday, if 0; working day

    Notes
    -----
    timetuple attributes:
        tm_year
        tm_mon
        tm_mday
        tm_hour
        tm_min
        tm_sec
        tm_wday
        tm_yday
        tm_isdst
    """
    weekday = date_from_yearday.timetuple().tm_wday
    year = date_from_yearday.timetuple().tm_year

    if bank_holidays == 'not_globally_defined':
        if year == 2015:
            bank_holidays = [
                date(2015, 1, 1),
                date(2015, 4, 3),
                date(2015, 4, 6),
                date(2015, 5, 4),
                date(2015, 5, 25),
                date(2015, 8, 31),
                date(2015, 12, 25),
                date(2015, 12, 28),
                date(2015, 12, 29),
                date(2015, 12, 30),
                date(2015, 12, 31)]
        elif year == 2014:
            bank_holidays = [
                date(2014, 1, 1),
                date(2014, 4, 18),
                date(2014, 4, 21),
                date(2014, 5, 5),
                date(2014, 5, 26),
                date(2014, 8, 25),
                date(2014, 12, 25),
                date(2014, 12, 26),
                date(2014, 12, 27),
                date(2014, 12, 28),
                date(2014, 12, 29),
                date(2014, 12, 30),
                date(2014, 12, 31)]
        elif year == 2013:
            bank_holidays = [
                date(2013, 1, 1),
                date(2013, 4, 29),
                date(2013, 4, 1),
                date(2013, 5, 6),
                date(2013, 5, 27),
                date(2013, 8, 26),
                date(2013, 12, 25),
                date(2013, 12, 26),
                date(2013, 12, 27),
                date(2013, 12, 28),
                date(2013, 12, 29),
                date(2013, 12, 30),
                date(2013, 12, 31)]
        elif year == 2012:
            bank_holidays = [
                date(2012, 1, 1),
                date(2012, 1, 2),
                date(2012, 4, 6),
                date(2012, 4, 9),
                date(2012, 5, 7),
                date(2012, 6, 4),
                date(2012, 6, 7),
                date(2012, 8, 27),
                date(2012, 12, 25),
                date(2012, 12, 26),
                date(2012, 12, 27),
                date(2012, 12, 28),
                date(2012, 12, 29),
                date(2012, 12, 30),
                date(2012, 12, 31)]
        elif year == 2011:
            bank_holidays = [
                date(2011, 1, 1),
                date(2011, 1, 2),
                date(2011, 1, 3),
                date(2011, 4, 22),
                date(2011, 4, 25),
                date(2011, 4, 29),
                date(2011, 5, 2),
                date(2011, 5, 30),
                date(2011, 8, 29),
                date(2011, 12, 25),
                date(2011, 12, 26),
                date(2011, 12, 27),
                date(2011, 12, 28),
                date(2011, 12, 29),
                date(2011, 12, 30),
                date(2011, 12, 31)]
        elif year == 2010:
            bank_holidays = [
                date(2010, 1, 1),
                date(2010, 4, 2),
                date(2010, 4, 5),
                date(2010, 5, 3),
                date(2010, 5, 31),
                date(2010, 8, 30),
                date(2010, 12, 25),
                date(2010, 12, 26),
                date(2010, 12, 27),
                date(2010, 12, 28),
                date(2010, 12, 29),
                date(2010, 12, 30),
                date(2010, 12, 31)]
        elif year == 2009:
            bank_holidays = [
                date(2009, 1, 1),
                date(2009, 4, 10),
                date(2009, 4, 13),
                date(2009, 5, 4),
                date(2009, 5, 25),
                date(2009, 8, 31),
                date(2009, 12, 25),
                date(2009, 12, 26),
                date(2009, 12, 27),
                date(2009, 12, 28),
                date(2009, 12, 29),
                date(2009, 12, 30)]
        elif year == 2008:
            bank_holidays = [
                date(2008, 1, 1),
                date(2008, 4, 21),
                date(2008, 4, 24),
                date(2008, 5, 5),
                date(2008, 5, 26),
                date(2008, 8, 25),
                date(2008, 12, 25),
                date(2008, 12, 26),
                date(2008, 12, 27),
                date(2008, 12, 28),
                date(2008, 12, 29),
                date(2008, 12, 30)]
        elif year == 2007:
            bank_holidays = [
                date(2007, 1, 1),
                date(2007, 4, 6),
                date(2007, 4, 9),
                date(2007, 5, 7),
                date(2007, 5, 28),
                date(2007, 8, 27),
                date(2007, 12, 25),
                date(2007, 12, 26),
                date(2007, 12, 27),
                date(2007, 12, 28),
                date(2007, 12, 29),
                date(2007, 12, 30)]
        elif year == 2006:
            bank_holidays = [
                date(2006, 1, 2),
                date(2006, 4, 14),
                date(2006, 4, 17),
                date(2006, 5, 1),
                date(2006, 5, 29),
                date(2006, 8, 28),
                date(2006, 12, 25),
                date(2006, 12, 26),
                date(2006, 12, 27),
                date(2006, 12, 28),
                date(2006, 12, 29),
                date(2006, 12, 30)]
        elif year == 2005:
            bank_holidays = [
                date(2005, 1, 1),
                date(2005, 1, 2),
                date(2005, 1, 3),
                date(2005, 3, 25),
                date(2005, 3, 28),
                date(2005, 5, 2),
                date(2005, 5, 30),
                date(2005, 8, 29),
                date(2005, 12, 25),
                date(2005, 12, 26),
                date(2005, 12, 27),
                date(2005, 12, 28),
                date(2005, 12, 29),
                date(2005, 12, 30)]
        elif year == 2004:
            bank_holidays = [
                date(2004, 1, 1),
                date(2004, 4, 9),
                date(2004, 4, 12),
                date(2004, 4, 25),
                date(2004, 5, 3),
                date(2004, 5, 31),
                date(2004, 8, 30),
                date(2004, 12, 25),
                date(2004, 12, 26),
                date(2004, 12, 27),
                date(2004, 12, 28),
                date(2004, 12, 29),
                date(2004, 12, 30)]
        elif year == 2003:
            bank_holidays = [
                date(2003, 1, 1),
                date(2003, 4, 21),
                date(2003, 5, 5),
                date(2003, 5, 26),
                date(2003, 8, 25),
                date(2003, 12, 25),
                date(2003, 12, 26),
                date(2003, 12, 27),
                date(2003, 12, 28),
                date(2003, 12, 29),
                date(2003, 12, 30)]
        elif year == 2002:
            bank_holidays = [
                date(2002, 1, 1),
                date(2002, 4, 1),
                date(2002, 5, 6),
                date(2002, 6, 3),
                date(2002, 6, 4),
                date(2002, 8, 26),
                date(2002, 12, 25),
                date(2002, 12, 26),
                date(2002, 12, 27),
                date(2002, 12, 28),
                date(2002, 12, 29),
                date(2002, 12, 30)]
        else:
            bank_holidays = []

    if date_from_yearday in bank_holidays:
        return 'holiday'
    else:
        if weekday == 5 or weekday == 6:
            return 'holiday' # Holiday 1
        else:
            return 'working_day' # Working day 0

def fullyear_dates(start=None, end=None):
    """Calculates all dates between a star and end date.
    TESTED_PYTEST

    Parameters
    ----------
    start : date
        Start date
    end : date
        end date

    Returns
    -------
    list_dates : list
        A list with dates
    """
    list_dates = []
    span = end - start
    for day in range(span.days + 1):
        list_dates.append(start + timedelta(days=day))

    return list(list_dates)

'''def timesteps_full_year(base_yr):
    """A list is generated from the first hour of the base year to the last hour of teh base year

    This function generates a single list from a list with
    containg start and end dates of the base year

    Parameters
    ----------
    base_yr : int
        Year used to generate timesteps.

    Returns
    -------
    timesteps : dict
        Contains every yearday and the start and end time_ID

    Note
    ----
    The base year must be identical to the input energy data

    """
    # List with all dates of the base year
    list_dates = fullyear_dates(start=date(base_yr, 1, 1), end=date(base_yr, 12, 31)) # List with every date in a year

    timesteps = {}

    #Add to list
    for day_date in list_dates:
        yearday = day_date.timetuple().tm_yday - 1 # -1 because in _info yearday 1: 1. Jan    ((tm_year=2015, tm_mon=1, tm_mday=1, tm_hour=0, tm_min=0, tm_sec=0, tm_wday=3, tm_yday=1, tm_isdst=-1))

        # Iterate hours
        for h_id in range(24):
            start_period = "P{}H".format(yearday * 24 + h_id) # Start intervall ID
            end_period = "P{}H".format(yearday * 24 + h_id + 1) # End intervall ID
            yearday_h_id = str(str(yearday) + str("_") + str(h_id)) # Timestep ID

            # Add to dict
            timesteps[yearday_h_id] = {'start': start_period, 'end': end_period}

    return timesteps

'''