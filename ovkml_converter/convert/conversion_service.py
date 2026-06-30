import zipfile
from pathlib import Path

from ..parsers import OvkmlParser, OvobjParser, OvjsnParser
from ..writers import KmlWriter, ShpWriter, DxfWriter
from ..transforms.coordinate_transform import transform_document, out_of_china
from ..models.geo_objects import CoordType, GeoDocument

# 文本类格式：自带坐标系信息，可自动识别（OVKMZ 解压后即 OVKML）
_AUTO_CRS_EXTS = (".ovkml", ".ovkmz", ".ovjsn")
# 全部支持的输入扩展名
SUPPORTED_EXTS = (".ovkml", ".ovkmz", ".ovjsn", ".ovobj")


def _read_ovkmz_kml(filepath) -> bytes:
    """OVKMZ 是 ZIP 包，内含一个 doc.kml（OVKML 内容）。返回其字节。"""
    with zipfile.ZipFile(filepath) as z:
        names = [n for n in z.namelist() if n.lower().endswith((".kml", ".ovkml"))]
        if not names:
            raise ValueError("OVKMZ 内未找到 KML 文件")
        return z.read(names[0])


def parse_input(filepath) -> GeoDocument:
    """按扩展名把任意奥维输入格式解析为统一的 GeoDocument。"""
    ext = Path(filepath).suffix.lower()
    stem = Path(filepath).stem
    if ext == ".ovkml":
        return OvkmlParser().parse(filepath)
    if ext == ".ovkmz":
        return OvkmlParser().parse_string(_read_ovkmz_kml(filepath), stem)
    if ext == ".ovjsn":
        return OvjsnParser().parse(filepath)
    if ext == ".ovobj":
        return OvobjParser().parse(filepath)
    raise ValueError(f"不支持的格式: {ext}")


def resolve_source_crs(filepath, parsed_doc, ovobj_src_crs, sibling_files):
    ext = Path(filepath).suffix.lower()
    if ext in _AUTO_CRS_EXTS:
        if parsed_doc.coord_type != CoordType.UNKNOWN:
            return parsed_doc.coord_type
        return ovobj_src_crs

    # OVOBJ 不含坐标系：先找同名文本格式兜底，再回落到手动设置
    stem = Path(filepath).stem
    for sf in sibling_files or []:
        sp = Path(sf)
        if sp.suffix.lower() in _AUTO_CRS_EXTS and sp.stem == stem and sp.exists():
            crs = _try_detect(str(sp))
            if crs is not None:
                return crs
    for e in _AUTO_CRS_EXTS:
        cand = Path(filepath).with_suffix(e)
        if cand.exists():
            crs = _try_detect(str(cand))
            if crs is not None:
                return crs
    return ovobj_src_crs


def _try_detect(filepath):
    try:
        doc = parse_input(filepath)
        if doc.coord_type != CoordType.UNKNOWN:
            return doc.coord_type
    except Exception:
        pass
    return None


def detect_input_crs(filepath):
    """文本类格式（OVKML/OVKMZ/OVJSN）返回检测到的坐标系；OVOBJ 或失败返回 None。

    供 UI 在添加文件时自动回填"输入坐标系"下拉用。
    """
    if Path(filepath).suffix.lower() not in _AUTO_CRS_EXTS:
        return None
    return _try_detect(filepath)


def _stamp_source(doc: GeoDocument, src: CoordType, override_all: bool) -> None:
    for folder in doc.folders:
        for obj in folder.objects:
            if override_all or obj.coord_type == CoordType.UNKNOWN:
                obj.coord_type = src
    doc.coord_type = src


def _crs_class(crs: CoordType):
    if crs in (CoordType.WGS84, CoordType.CGCS2000):
        return "wgs"
    return crs


def _any_in_china(doc: GeoDocument) -> bool:
    for folder in doc.folders:
        for obj in folder.objects:
            for p in obj.coordinates:
                if not out_of_china(p.lon, p.lat):
                    return True
    return False


def convert_file(filepath, target_crs, ovobj_src_crs, formats, out_dir, sibling_files=None):
    ext = Path(filepath).suffix.lower()
    doc = parse_input(filepath)

    if ext == ".ovobj" and doc.get_object_count() == 0:
        raise ValueError(
            "OVOBJ 仅支持点对象；线/面坐标为奥维私有压缩编码无法可靠还原。"
            "请改用同名的 OVKML / OVKMZ / OVJSN 文件转换线/面数据")

    src = resolve_source_crs(filepath, doc, ovobj_src_crs, sibling_files)
    _stamp_source(doc, src, override_all=(ext == ".ovobj"))

    in_china = _any_in_china(doc)
    out_doc = transform_document(doc, target_crs)
    effective_target = src if target_crs == CoordType.UNKNOWN else target_crs

    # 输出名带源扩展名后缀（如 测试点.ovkml.kml），避免同一份数据的多种格式
    # （.ovkml/.ovkmz/.ovjsn/.ovobj）输出同名文件互相覆盖。
    suffix = Path(filepath).suffix          # 含点，如 ".ovkml"
    base = Path(filepath).stem + suffix     # 如 "测试点.ovkml"
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if "kml" in formats:
        KmlWriter().write(out_doc, str(out / f"{base}.kml"))
    if "shp" in formats:
        ShpWriter().write(out_doc, str(out / f"{base}.shp"))
    if "dxf" in formats:
        DxfWriter().write(out_doc, str(out / f"{base}.dxf"))

    needs_offset = (target_crs != CoordType.UNKNOWN
                    and _crs_class(src) != _crs_class(effective_target))
    return {
        "source_crs": src,
        "target_crs": effective_target,
        "out_of_china": (needs_offset and not in_china),
    }
