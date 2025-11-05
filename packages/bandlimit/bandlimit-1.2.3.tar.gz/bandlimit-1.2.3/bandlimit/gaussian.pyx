###-------------###
#gaussian.pyx##
###-------------###

 #*  Copywrite 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025  Quantum Galaxies Corporation,
 #*   and methods patented by Texas Tech University.
 #*  We acknowledge the generous support of Texas Tech University,
 #*  The Robert A. Welch Foundation, and the Army Research Office.

# MIT license


include "system.pxi"

from .coreMath cimport GaussianInSinc
from .coreMath cimport momentumIntegralInTrain3

cpdef double compute(double lattice, int n, double alpha, double y, double X):
        """
        * GTOs in plane waves
        * GaussianInSinc = < normalized_angular_gaussian(n) @ y | Sinc@ X in lattice >
        """
        return GaussianInSinc(pi/lattice, n, 0.5*alpha, y, X)


cpdef double ops(double lattice, double alpha, double y, diagonal_flag):
        """
        * GTOs in plane waves
        * Part of tensor train, a diagonal operator
        * momentumIntegralInTrain2 for normalized_gaussian @ y 
        * off diagonal piece coupled to momentum operators
        """
        return momentumIntegralInTrain3( 0,(alpha), y , lattice, diagonal_flag )
