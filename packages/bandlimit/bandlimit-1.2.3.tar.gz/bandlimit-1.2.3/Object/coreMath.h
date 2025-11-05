/**
 *  coreMath.h
 *
 *
 *  Copywrite 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025  Quantum Galaxies Corporation,
 *   and methods patented by Texas Tech University.
 *  We acknowledge the generous support of Texas Tech University,
 *  The Robert A. Welch Foundation, and the Army Research Office.
 *
 
 *  MIT License
*/

#ifndef coreMath_h
#define coreMath_h
#include "constants.h"

DCOMPLEX expErf ( DCOMPLEX z );
//double GaussianInSinc( double K, int n, double alpha, double y, double X );


#ifdef __cplusplus
extern "C" {
#endif

double GaussianInSinc( double K, int n, double alpha, double y, double X );
double momentumIntegralInTrain2 ( double beta, double kl , double d, int diagonal_flag );
double momentumIntegralInTrain3 ( double boost, double alpha, double y , double d, int diagonal_flag );
#ifdef __cplusplus
}
#endif

#endif /* coreMath_h */
