# Copyright (C) 2025  Arthur Coqué, RBINS

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""A Python version of DINEOF.

DINEOF (https://github.com/aida-alvera/DINEOF) is an EOF-based method to fill in missing
data from geophysical fields, such as clouds in sea surface temperature, and is
available as compiled Fortran code.
For more information on how DINEOF works, please refer to Alvera-Azcarate et al. (2005)
and Beckers and Rixen (2003). The multivariate application of DINEOF is explained in
Alvera-Azcarate et al. (2007), and in Beckers et al0 (2006) the error calculation using
an optimal interpolation approach is explained.
For more information about the Lanczos solver, see Toumazou and Cretaux (2001).

Available functions
-------------------
run_1D
    Run a monovariate DINEOF reconstruction of a given 1-D time series.
run_2D
    Run a monovariate DINEOF reconstruction of a given 2-D time series.
"""

from pydineof.main import run_1D, run_2D
