# tests/test_design.py
from aashto_calculator.design import aashto_thickness

def test_basic():
    SN = aashto_thickness(1e6, -1.645, 0.45, 1.7, 5000)
    assert 2 < SN < 6

