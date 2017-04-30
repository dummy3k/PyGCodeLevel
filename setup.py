#!/usr/bin/env python

from setuptools import setup

setup(name='PyGCodeLevel',
      version='0.1',
      description='HeightMap Tool for PCB Milling',
      packages=['PyGCodeLevel'],
	  
    entry_points={
        'console_scripts': [
            # 'foo = my_package.some_module:main_func',
            # 'bar = other_module:some_func',
			'height_adjust = PyGCodeLevel.height_adjust:main'
        ],
        # 'gui_scripts': [
            # 'baz = my_package_gui:start_func',
        # ]
    }
	
)