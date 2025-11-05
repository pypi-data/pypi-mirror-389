/**
 *  system.h
 *
 *
 *  Copywrite 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025  Quantum Galaxies Corporation,
 *   and methods patented by Texas Tech University.
 *  We acknowledge the generous support of Texas Tech University,
 *  The Robert A. Welch Foundation, and the Army Research Office.
 *
 
 *  MIT License
*/

#ifndef system_h
#define system_h

///VERSIONING
#define VERSION 11.0
//#define COMPLEX_ME
//#define NON_SYMMETRIC_SOLVER
#define OVERHEAD_FRACTION 0.1


///MACHINE SPECIFIC
///to compile with acceleration in APPLE, not for distribution
//#define MKL
//#define OMP


///METHODS
#define SPHERE
#define SLEEP_DURATION 0
#ifndef APPLE
    #define READ_FAST
    #define WRITE_FAST
#endif
#define STEP_OVER 1
#define MODULARIZE_INPUT
#define MODULARIZE_OUTPUT
//forgets level look/roll useless 
//#define TEMP_TEMP 

#define MACHINE_PRECISION 1e-15
#define MAX_CANON_PARALLEL 3
///STATIC ALLOCATION limits
#define MAX_CORE 4
///Number of components, no limit
#define SPACE 800
///Number of 'atoms' under geometry,  really no reason to to keep this big
#define MAXBODY 4
#define MAX_PRODUCT 100
///The block-memory commands act to negate memory allocations,  this is the maximum number of blocks.  Leave this alone, unless you add blocks.
#define BLOCK_COUNT 24
///Probably too much, but dont care,
#define MAXSTRING 76
///Probably too much, but dont care,
#define SUPERMAXSTRING 200

///NATURAL NUMBERS
///All internal numbers are in au, including Hartrees.
///input in Angstroms unless 'Angstroms 0' set
#define a0  0.52917721
///natural
#define pi  3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679
///Standard Position of identity group action
#define CDT 1
#define OMEGA 0.500
#define MAX_FEATURE 3

///VERBOSITY
//#define VERBOSE_ALS
//#define VERBOSE_MEMORY
#define VERBOSE 0
//#define PRINT_STRUCTURE
//#define PRINT_HEAD

#ifdef APPLE
    #define BIT_INT
#else
#ifndef MKL
/// gnu compatible
 //   #define ATLAS
    #define LAPACKE
    #define BIT_INT
#endif
#endif

#endif /* system_h */
