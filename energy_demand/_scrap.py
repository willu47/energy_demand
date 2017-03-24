
'''
1. Calculate fraction without fuel switch (assumption about internal shift between technologies)
2. Caclulate fuel switches: I. Amount of new fuel sigmoid
                            II. Update shares of technologies witihn fuel shares of existing technology (save fuels of internal fuel switches)
                            III. Calc Fuel of each technology: Share & eff 

                            Total fuel = (shareA* effA) + (shareB * effB) + fuelswtichesFuelTechA + fuelsWitch TechB

                            IV. Update cy technology shares including switch

          '''

import numpy as np
import matplotlib.pyplot as plt



a = [1,1,1,1,1]
b = [2,2,2,2,2]

y = np.row_stack((a,b))
x = [1,2,3,4,5]

#bin = np.arange(5) 
#plt.xlim([0,bin.size])

fig, ax = plt.subplots()
ax.stackplot(x, y)
plt.show()

    """A one-line summary that does not use variable names or the
    function name.
    Several sentences providing an extended description. Refer to
    variables using back-ticks, e.g. `var`.

    Parameters
    ----------
    var1 : array_like
        Array_like means all those objects -- lists, nested lists, etc. --
        that can be converted to an array.  We can also refer to
        variables like `var1`.
    var2 : int
        The type above can either refer to an actual Python type
        (e.g. ``int``), or describe the type of the variable in more
        detail, e.g. ``(N,) ndarray`` or ``array_like``.
    long_var_name : {'hi', 'ho'}, optional
        Choices in brackets, default first when optional.

    Returns
    -------
    type
        Explanation of anonymous return value of type ``type``.
    describe : type
        Explanation of return value named `describe`.
    out : type
        Explanation of `out`.

    Other Parameters
    ----------------
    only_seldom_used_keywords : type
        Explanation
    common_parameters_listed_above : type
        Explanation

    Raises
    ------
    BadException
        Because you shouldn't have done that.

    See Also
    --------
    otherfunc : relationship (optional)
    newfunc : Relationship (optional), which could be fairly long, in which
              case the line wraps here.
    thirdfunc, fourthfunc, fifthfunc

    Notes
    -----
    Notes about the implementation algorithm (if needed).
    This can have multiple paragraphs.
    You may include some math:

"""