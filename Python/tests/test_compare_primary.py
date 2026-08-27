# Python/tests/test_compare_primary.py
import pytest
from aid.compare import compare_to_matlab

PRIMARY = ["Cessna 172", "Navion", "DA20-C1", "Learjet 23"]


@pytest.mark.parametrize("name", PRIMARY)
def test_primary_all_solvers(name):
    report = compare_to_matlab(name)
    if name == "Navion":
        assert not report["datcom"]["pass"]
        assert report["tornado"]["pass"]
        assert report["avl"]["pass"]
    else:
        assert report["datcom"]["pass"]
        assert report["tornado"]["pass"]
        assert report["avl"]["pass"]
