"""The technological stock for every simulation year"""
import energy_demand.technological_stock_functions as tf
import energy_demand.main_functions as mf
# pylint: disable=I0011,C0321,C0301,C0103, C0325
class ResidTechStock(object):
    """Class of a technological stock of a year of the residential model

    The main class of the residential model. For every region,
    a Region Object needs to be generated

    Parameters
    ----------
    data : dict
        tbd
    assumptions : dict
        tbd
    data_ext : dict
        tbd
    current_yr : int
        Current year

    """
    def __init__(self, data, data_ext, current_yr):
        """Constructor of technologies for residential sector"""
        self.base_year = data_ext['glob_var']['base_year']
        self.end_year = data_ext['glob_var']['end_year']
        self.current_yr = current_yr
        self.assumptions = data['assumptions']
        self.tech_lu = data['tech_lu']
        self.fuel_types = data['fuel_type_lu']

        # Execute function to add all technological efficiencies as self argument
        self.create_iteration_efficiency()

        # get share of technologies
        self.tech_frac_by = data['assumptions']['technologies_enduse_by'] #base year
        self.tech_frac_ey = data['assumptions']['technologies_enduse_ey'] #end year
        self.tech_frac_cy = self.get_sigmoid_tech_diff() #current year

    def create_iteration_efficiency(self):
        """Iterate technologies of each enduse in 'base_year' and add to technology_stock (linear diffusion)

        The efficiency of each technology is added as `self` attribute.
        Based on assumptions of theoretical maximum efficiency gains of
        each technology and assumptions on the actual achieved efficiency,
        the efficiency of the current year is calculated based
        on a linear diffusion.

        Returns
        -------
        Sets attributes with efficiency values for the current year

        Example
        -------
        Technology X is projected to have maximum potential efficiency increase
        from 0.5 to a 1.00 efficiency. If however, the acutal efficiency gain
        is only 50%, then after the simulation, an efficiency of 0.75 is reached
        """
        technology_list = self.assumptions['eff_by']

        for technology in technology_list:
            eff_by = self.assumptions['eff_by'][technology]
            eff_ey = self.assumptions['eff_ey'][technology]
            sim_years = self.end_year - self.base_year

            # Theoretical maximum efficiency potential if theoretical maximum is linearly calculated
            theor_max_eff = tf.linear_diff(self.base_year, self.current_yr, eff_by, eff_ey, sim_years)

            # Get assmuption how much of efficiency potential is reaped
            achieved_eff = self.assumptions['eff_achieved'][technology]

            # Actual efficiency potential
            cy_eff = achieved_eff * theor_max_eff # Efficiency gain assumption achieved * theoretically maximum achieveable efficiency gain

            ResidTechStock.__setattr__(self, technology, cy_eff)

    def get_sigmoid_tech_diff(self):
        """Calculate change in fuel demand based on sigmoid diffusion of fraction of technologies for each enduse

        I. With help of assumptions on the fraction of technologies for each
        enduse and fueltype for the `base_year` and `end_year` the
        fraction of technologies for the `current_yr` is calculated.

        II.The change in fuel is calculated depending on the relationship
        `sig_frac_tech_change`.

        Returns
        -------
        tech_frac_cy : dict
            A nested.

        Example
        -------

        Notes
        -----
        In the process of calculating the differences in the fraction
        the individual technologies are converted in to IDs in order
        to create arrays. In the end, the technology IDs are replaced
        with strings for each technology.
        """
        tech_frac_cy = {}

        tech_frac_by = self.tech_frac_by
        tech_frac_ey = self.tech_frac_ey

        # Sigmoid efficiency which is achieved up to cy (so far for all technologies)
        sig_frac_tech_change = tf.sigmoidefficiency(self.base_year, self.current_yr, self.end_year, self.assumptions['sig_midpoint'], self.assumptions['sig_steeppness'])

        for enduse in tech_frac_by:
            tech_frac_cy[enduse] = {}

            # Convert to array and replace fuels with strings
            by_enduse_array = mf.convert_to_array_technologies(tech_frac_by[enduse], self.tech_lu)  # Base year fraction of technolgies for the enduse
            ey_enduse_array = mf.convert_to_array_technologies(tech_frac_ey[enduse], self.tech_lu)  # End year fraction of technolgies for the enduse

            # If no technolgies are in this enduse
            if ey_enduse_array == []:
                for fueltype in range(len(self.fuel_types)):
                    tech_frac_cy[enduse][fueltype] = {}
                continue # Go to next enduse

            # iterate fuel type and the technologies
            for fueltype in range(len(self.fuel_types)):

                # No technologies are within this fuel type
                if by_enduse_array[fueltype] == []:
                    tech_frac_cy[enduse][fueltype] = {}
                    continue # Go to next fueltype

                diff = ey_enduse_array[fueltype][:, 1] - by_enduse_array[fueltype][:, 1] # Calculate difference in share of technologies between end and base year
                diff_fract_sig = diff * sig_frac_tech_change # Multiply overall difference with achieved efficiency
                diff_cy = by_enduse_array[fueltype][:, 1] + diff_fract_sig # Current year fraction (frac of base year plus changes up to current year)

                # Convert the arrays back to dictionary and replace strings of technologies with str
                technologey_of_enduse = tech_frac_by[enduse][fueltype].keys()
                tech_frac_cy[enduse][fueltype] = dict(zip(technologey_of_enduse, diff_cy.flatten()))

        return tech_frac_cy
