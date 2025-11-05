from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
	Extension(
		name="bandlimit.gaussian",
		sources=["bandlimit/gaussian.pyx"
			,"Object/coreMath.c"
			,"Faddeeva/Faddeeva.cc"],
		include_dirs=["Object","Faddeeva"],
#		libraries=['gaussianSinc'],
		library_dirs=["bandlimit"],
		extra_compile_args=["-O3"],
		runtime_library_dirs=['$ORIGIN'],
		language="c",
		)
]

setup(
	packages=['bandlimit'],
	package_dir={'bandlimit':'bandlimit'},
#	package_data={'bandlimit':['libgaussianSinc.so']
#	},

	ext_modules=cythonize(
		extensions,
                compiler_directives={'language_level':3}
	),
)
