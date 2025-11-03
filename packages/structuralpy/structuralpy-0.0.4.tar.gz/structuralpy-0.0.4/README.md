# StructuralPy

This module provides functions for analysis and design of structural steel and reinforced concrete members in accordance with NSCP 2015 provisions.

## Features (currently a work in progress)

- Analyze and design RC beams for flexure

## Installation

Install using

```bash
pip install structuralpy
```

## Examples

```python
from structuralpy import rc_beam

# Beam analysis and design
b = 300             # beam width (mm)
h = 600             # beam depth (mm)
fcp = 20.7          # concrete strength (MPa)
fy = 415            # rebar strength (MPa)
As = 600            # tension rebar area (mm^2)
cover_bot = 65      # cover to centroid of tension reinforcement (mm)
Mu = 300e6          # factored moment (N-mm)

print(analyze_flexure(b, h, fcp, fy, As, cover_bot, Asp=0, cover_top=None, n_iter=10))
print(design_flexure_size(Mu, fcp, fy, cover_bot, aspect_ratio=2.0))
print(design_flexure_rebar(Mu, b, h, fcp, fy, cover_bot, cover_top=None))
```
