import xml.etree.ElementTree as ET
from xml.dom import minidom
from ..models.geo_objects import GeoDocument, GeoType, CoordType


class KmlWriter:
    KML_NS = "http://www.opengis.net/kml/2.2"

    def write(self, doc: GeoDocument, filepath: str):
        root = ET.Element('kml')
        root.set('xmlns', self.KML_NS)

        doc_elem = ET.SubElement(root, 'Document')
        ET.SubElement(doc_elem, 'name').text = doc.name

        for folder in doc.folders:
            self._write_folder(doc_elem, folder, doc.coord_type)

        xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent='\t')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(xml_str)

    def _write_folder(self, parent, folder, coord_type):
        folder_elem = ET.SubElement(parent, 'Folder')
        ET.SubElement(folder_elem, 'name').text = folder.name

        for obj in folder.objects:
            ct = obj.coord_type if obj.coord_type != CoordType.UNKNOWN else coord_type
            self._write_placemark(folder_elem, obj, ct)

    def _write_placemark(self, parent, obj, coord_type):
        pm = ET.SubElement(parent, 'Placemark')
        ET.SubElement(pm, 'name').text = obj.name

        if obj.description:
            ET.SubElement(pm, 'description').text = obj.description

        if obj.style:
            self._write_style(pm, obj.style)

        if obj.attributes:
            attr_elem = ET.SubElement(pm, 'OvAttr')
            for key, val in obj.attributes.items():
                child = ET.SubElement(attr_elem, key)
                child.text = str(val)

        ct_name = coord_type.value if coord_type != CoordType.UNKNOWN else "WGS84"
        ET.SubElement(pm, 'OvCoordType').text = ct_name

        if obj.geo_type == GeoType.POINT and obj.coordinates:
            point = ET.SubElement(pm, 'Point')
            c = obj.coordinates[0]
            ET.SubElement(point, 'coordinates').text = f"{c.lon},{c.lat},{c.alt}"

        elif obj.geo_type == GeoType.LINE and obj.coordinates:
            line = ET.SubElement(pm, 'LineString')
            coords_text = ' '.join(f"{c.lon},{c.lat},{c.alt}" for c in obj.coordinates)
            ET.SubElement(line, 'coordinates').text = coords_text

        elif obj.geo_type == GeoType.POLYGON and obj.coordinates:
            poly = ET.SubElement(pm, 'Polygon')
            outer = ET.SubElement(poly, 'outerBoundaryIs')
            ring = ET.SubElement(outer, 'LinearRing')
            coords_text = ' '.join(f"{c.lon},{c.lat},{c.alt}" for c in obj.coordinates)
            ET.SubElement(ring, 'coordinates').text = coords_text

    def _write_style(self, pm, style):
        style_elem = ET.SubElement(pm, 'Style')

        if 'icon_color' in style or 'icon_href' in style:
            icon_style = ET.SubElement(style_elem, 'IconStyle')
            if 'icon_color' in style:
                ET.SubElement(icon_style, 'color').text = style['icon_color']
            if 'icon_href' in style:
                icon = ET.SubElement(icon_style, 'Icon')
                ET.SubElement(icon, 'href').text = style['icon_href']

        if 'line_color' in style or 'line_width' in style:
            line_style = ET.SubElement(style_elem, 'LineStyle')
            if 'line_color' in style:
                ET.SubElement(line_style, 'color').text = style['line_color']
            if 'line_width' in style:
                ET.SubElement(line_style, 'width').text = style['line_width']

        if 'poly_color' in style:
            poly_style = ET.SubElement(style_elem, 'PolyStyle')
            ET.SubElement(poly_style, 'color').text = style['poly_color']
