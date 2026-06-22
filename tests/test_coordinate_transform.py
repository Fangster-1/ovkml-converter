import math
from ovkml_converter.transforms.coordinate_transform import (
    out_of_china, wgs84_to_gcj02, gcj02_to_wgs84,
    gcj02_to_bd09, bd09_to_gcj02,
)


def _meters(lon1, lat1, lon2, lat2):
    dx = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1)
    return math.hypot(dx, dy) * 111320.0


def test_out_of_china():
    assert out_of_china(0.0, 0.0) is True
    assert out_of_china(101.14, 25.40) is False


def test_wgs84_to_gcj02_offset_in_range():
    glon, glat = wgs84_to_gcj02(116.404, 39.915)
    d = _meters(116.404, 39.915, glon, glat)
    assert 100 < d < 800


def test_gcj02_to_wgs84_is_inverse():
    glon, glat = wgs84_to_gcj02(116.404, 39.915)
    wlon, wlat = gcj02_to_wgs84(glon, glat)
    assert _meters(116.404, 39.915, wlon, wlat) < 1.0


def test_out_of_china_no_offset():
    assert wgs84_to_gcj02(0.0, 0.0) == (0.0, 0.0)
    assert gcj02_to_wgs84(0.0, 0.0) == (0.0, 0.0)


def test_gcj02_bd09_inverse():
    blon, blat = gcj02_to_bd09(116.404, 39.915)
    glon, glat = bd09_to_gcj02(blon, blat)
    assert _meters(116.404, 39.915, glon, glat) < 1.0
