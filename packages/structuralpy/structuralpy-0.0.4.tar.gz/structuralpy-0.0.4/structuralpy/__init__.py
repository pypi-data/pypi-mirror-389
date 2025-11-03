# structuralpy/__init__.py

"""
**StructuralPy**

This module provides functions for analysis and design of structural steel and reinforced concrete members in accordance with NSCP 2015 provisions.

Included functions (currently a work in progress):
 - RC beam analysis and design
"""

from .rc_beam import analyze_flexure, design_flexure_size, design_flexure_rebar

__all__ = ['analyze_flexure', 'design_flexure_size', 'design_flexure_rebar']

def __version__() :
    return "0.0.4"

def describe() :
    description = (
        "StructuralPy\n"
        "Version: {0}\n\n"
        "This module provides functions for analysis and design of structural steel and reinforced concrete members in accordance with NSCP 2015 provisions.\n\n"
        "Included functions (currently a work in progress):\n"
        " - RC beam analysis and design\n"
    ).format(__version__())
    
    print(description)