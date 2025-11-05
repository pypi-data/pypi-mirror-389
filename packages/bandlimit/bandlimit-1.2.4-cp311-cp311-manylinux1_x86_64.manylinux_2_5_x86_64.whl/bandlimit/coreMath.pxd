###-------------###
####coreMath.pxd##
###-------------###

 #*  Copywrite 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025  Quantum Galaxies Corporation,
 #*   and methods patented by Texas Tech University.
 #*  We acknowledge the generous support of Texas Tech University,
 #*  The Robert A. Welch Foundation, and the Army Research Office.

# MIT license

include "system.pxi"

cdef extern from "coreMath.h":
    double GaussianInSinc( double K, int n, double alpha, double y, double X )

cdef extern from "coreMath.h":
    double momentumIntegralInTrain2 ( double beta, double kl , double d, int diagonal_flag )

cdef extern from "coreMath.h":
    double momentumIntegralInTrain3 (double boost,  double alpha, double y , double d, int diagonal_flag )

