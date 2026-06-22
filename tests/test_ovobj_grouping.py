from ovkml_converter.parsers.ovobj_parser import OvobjParser

SAMPLE = "奥维格式数据/姚安县验证.ovobj"


def _groups():
    doc = OvobjParser().parse(SAMPLE)
    return {f.name: sorted(o.name for o in f.objects) for f in doc.folders}


def test_total_count():
    doc = OvobjParser().parse(SAMPLE)
    assert doc.get_object_count() == 32


def test_b_folder_contains_b4_and_b6_1():
    g = _groups()
    bline = next(v for k, v in g.items() if k.endswith("B线"))
    assert "B4" in bline and "B6-1" in bline
    assert len(bline) == 12


def test_a_folder_contains_a5():
    g = _groups()
    aline = next(v for k, v in g.items() if k.endswith("A线"))
    assert "A5" in aline
    assert len(aline) == 9


def test_c_folder_count():
    g = _groups()
    cline = next(v for k, v in g.items() if k.endswith("C线"))
    assert len(cline) == 11
