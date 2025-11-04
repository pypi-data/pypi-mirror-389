"""Radar Range Equation Package.

A comprehensive Python package for radar range equation calculations, supporting
multiple radar types including CW, CWFM, pulsed radar, direction finding, and
pulse compression techniques.

Main Components:
    vars: Container for all radar-related variables and physical constants
    equations: Symbolic SymPy equations for radar calculations
    solve: Numeric solver functions for computing radar parameters
    convert: Unit conversion utilities (angles, power, frequency, distance)
    redefine_variable: Helper function to set variables in the vars namespace

Example:
    >>> import radar_range_equation as RRE
    >>> RRE.vars.c = 3e8  # speed of light
    >>> RRE.vars.f = 10e9  # 10 GHz
    >>> RRE.vars.wavelength = RRE.solve.wavelength()
    >>> print(f"Wavelength: {RRE.vars.wavelength} m")

For detailed documentation, see the individual module docstrings in main.py.
"""

from .main import vars, \
                    equations, \
                    solve, \
                    convert, \
                    redefine_variable

__all__ = ["vars",
           "equations",
           "solve",
           "convert",
           "redefine_variable"
           ]