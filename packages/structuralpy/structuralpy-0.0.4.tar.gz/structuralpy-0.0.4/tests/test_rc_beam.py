# tests/test_rc_beam.py

import pytest
from structuralpy.rc_beam import analyze_flexure, design_flexure_size, design_flexure_rebar

b = 300
h = 600
fcp = 20.7
fy = 415
As = 600
cover_bot = 65
Mu = 300e6

def test_analyze_flexure() :
    assert analyze_flexure(b, h, fcp, fy, As, cover_bot) == pytest.approx(114607822.25063941, rel=1e-9)

def test_design_flexure_size() :
    assert design_flexure_size(Mu, fcp, fy, cover_bot) == (300, 650)

def test_design_flexure_rebar() :
    assert design_flexure_rebar(Mu, b, h, fcp, fy, cover_bot) == pytest.approx((1718.2712311467246, 0), rel=1e-9)

if __name__ == "__main__" :
    pytest.main()