# 奥维数据格式转换工具

将奥维地图的 `.ovkml` / `.ovkmz` / `.ovjsn` / `.ovobj` 格式批量转换为标准 KML、Shapefile、DXF 格式。项目还在持续测试中，欢迎交流学习

## 功能

- 支持四种奥维输入格式：
  - `.ovkml`（XML）—— 点 / 线 / 面，完整支持
  - `.ovkmz`（OVKML 的 ZIP 压缩包）—— 解压后等同 OVKML，完整支持
  - `.ovjsn`（JSON）—— 点 / 线 / 面，完整支持
  - `.ovobj`（私有二进制）—— **仅支持点对象**；线 / 面坐标为非标准编码无法可靠解析，请改用同名的 OVKML/OVKMZ/OVJSN
- 输出为标准 KML、Shapefile（SHP）、DXF（CAD）
- 支持多文件和整文件夹批量转换
- 坐标系转换：WGS84 / CGCS2000 / GCJ02 / BD09 互转
- OVKML / OVKMZ / OVJSN 自动识别输入坐标系（OVOBJ 需手动指定或借同名文件兜底）
- Tkinter 图形界面，操作简单

## 安装

```bash
pip install pyshp
```

唯一外部依赖为 `pyshp`，其余均为 Python 标准库。

## 使用

```bash
python main.py
```

启动图形界面后：

1. 点击「添加文件」或「添加文件夹」导入 `.ovkml` / `.ovkmz` / `.ovjsn` / `.ovobj` 文件
2. 选择输出格式（KML / SHP / DXF / 全部）
3. 设置输入坐标系（OVKML/OVKMZ/OVJSN 会自动识别，OVOBJ 需手动选择）
4. 如需坐标纠偏，选择目标坐标系；默认「与输入坐标系一致」不做转换
5. 选择输出目录，点击「开始转换」

## 打包为 exe

```bash
build.bat
```

使用 PyInstaller 打包为单文件可执行程序，输出到 `dist/` 目录。

## 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
├── main.py                          # 程序入口
├── requirements.txt                 # 依赖列表
├── build.bat                        # PyInstaller 打包脚本
└── ovkml_converter/
    ├── models/geo_objects.py        # 中间数据模型（GeoDocument/GeoObject 等）
    ├── parsers/
    │   ├── ovkml_parser.py          # OVKML 解析器（OVKMZ 解压后复用）
    │   ├── ovjsn_parser.py          # OVJSN（JSON）解析器
    │   └── ovobj_parser.py          # OVOBJ 二进制解析器（仅点对象）
    ├── transforms/
    │   └── coordinate_transform.py  # 坐标系转换（WGS84/GCJ02/BD09 互转）
    ├── writers/
    │   ├── kml_writer.py            # KML 输出
    │   ├── shp_writer.py            # Shapefile 输出（按几何类型拆分）
    │   └── dxf_writer.py            # DXF 输出
    ├── convert/
    │   └── conversion_service.py    # 转换管线编排
    └── ui/
        └── main_window.py           # Tkinter 图形界面
```

## 数据流

```
.ovkml / .ovkmz / .ovjsn / .ovobj  →  Parser  →  GeoDocument  →  坐标转换  →  Writer  →  .kml / .shp / .dxf
```

所有格式先解析为统一的 `GeoDocument` 中间模型，再由写入器输出为目标格式。新增输入或输出格式只需对接该模型。

## 格式说明

### OVKML 格式

OVKML 是标准 KML 的扩展，XML 结构如下：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>文档名称</name>
    <Folder>
        <name>文件夹名称</name>
        <Placemark>
            <name>对象名称</name>
            <description>描述信息</description>
            <OvAttr>
                <OvIcon>4</OvIcon>
                <OvIconNum>0</OvIconNum>
            </OvAttr>
            <Style>...</Style>
            <OvCoordType>CGCS2000</OvCoordType>
            <Point>
                <coordinates>经度,纬度,高程</coordinates>
            </Point>
        </Placemark>
    </Folder>
</Document>
</kml>
```

OVKML 特有元素：
- `<OvAttr>` — 奥维属性（图标类型、图标编号）
- `<OvCoordType>` — 坐标系类型（CGCS2000 / GCJ02 / WGS84）
- 坐标顺序：`经度,纬度,高程`（与标准 KML 一致）

### OVKMZ 格式

OVKMZ 是 **OVKML 的 ZIP 压缩包**（与 `KMZ = 压缩的 KML` 同理），内部包含一个 `doc.kml`（即 OVKML 内容）。工具解压后复用 OVKML 解析器，因此点 / 线 / 面均完整支持，与 OVKML 等价。

### OVJSN 格式

OVJSN 是奥维的 JSON 导出格式，结构如下（实测自奥维 V10.6.2）：

```json
{"Version":"V10.6.2","Type":1,"ObjItems":[
  {"Type":7,"Object":{"Name":"","Comment":"","ObjectDetail":{
      "Lat":29.6755252,"Lng":100.2723026,"Gcj02":0 }}}
]}
```

要点：
- `ObjItems[].Object.Type`：`7` = 点，`8` = 线，`13` = 面
- 点对象坐标在 `ObjectDetail.Lat` / `Lng`；线 / 面坐标在 `ObjectDetail.Latlng`（扁平的 `纬,经,纬,经,…` 数组）
- `ObjectDetail.Gcj02`：顶层坐标系标志，`1` = GCJ02，`0` = CGCS2000（注意：嵌套的 `Obj3dView.Gcj02` 与坐标系无关，不可使用）
- `Object.Name` / `Object.Comment` 对应名称 / 描述
- 文件常带 UTF-8 BOM，需以 `utf-8-sig` 读取

### OVOBJ 格式

OVOBJ 是奥维私有二进制格式（Magic `OviO`），**布局随版本变化且无公开文档**。实测：

- 点对象坐标以 小端 double 的 `(纬度, 经度)` 成对出现，可被定位；
- 线 / 面对象坐标采用**非标准编码**（常规 double/float/缩放整数均无法还原），无法可靠解析。

因此工具对 OVOBJ **只做点对象的尽力提取**（扫描中国经纬度范围内的成对坐标 double），名称 / 分组无法从二进制可靠还原。**线 / 面数据请改用同名的 OVKML / OVKMZ / OVJSN 文件**——它们承载同一份数据且可完整、可靠地转换。OVOBJ 不含坐标系信息，需通过同名文本格式兜底或手动指定。

### 坐标系

| 坐标系 | 说明 |
|--------|------|
| WGS84 | GPS 全球坐标系 |
| CGCS2000 | 中国大地坐标系，与 WGS84 视为等同（恒等转换） |
| GCJ02 | 国测局坐标系（火星坐标），对 WGS84 施加非线性偏移 |
| BD09 | 百度坐标系，在 GCJ02 基础上再次施加极坐标偏移 |

### 坐标转换算法

算法为纯 Python 实现（`transforms/coordinate_transform.py`），不依赖 GDAL/pyproj。以 GCJ02 为中间枢纽，任意两坐标系之间的转换路径为 `源坐标系 → GCJ02 → 目标坐标系`。

**椭球参数**（克拉索夫斯基椭球）：

```
长半轴 A  = 6378245.0
偏心率平方 EE = 0.00669342162296594323
```

**WGS84/CGCS2000 → GCJ02（正向偏移）**：

1. 判断是否在中国境外（经度不在 73.66°~135.05° 或纬度不在 3.86°~53.55°），境外直接返回原值
2. 计算经纬度扰动量 `dlat`、`dlon`，核心是对 `(lon-105, lat-35)` 做多组正弦函数叠加的非线性变换
3. 将扰动量转换为弧度增量：考虑椭球卯酉圈曲率半径 `N = A / sqrt(1 - EE * sin²(lat))`
4. 返回 `lon + dlon, lat + dlat`

**GCJ02 → WGS84/CGCS2000（反向迭代）**：

1. 境外点直接返回原值
2. 用牛顿迭代法逼近：最多迭代 30 次，每次将当前估计值正向转换后与目标值比较，修正差值
3. 收敛阈值：`|dlon| < 1e-9 且 |dlat| < 1e-9`

**GCJ02 ↔ BD09（极坐标偏移）**：

- GCJ02 → BD09：转为极坐标 `(z, θ)`，加上固定偏移 `(0.0065, 0.006)` 和三角修正
- BD09 → GCJ02：逆过程，先减去固定偏移再转回直角坐标

**转换规则**：

- `transform_point(lon, lat, src, dst)` 是单点转换入口
- CGCS2000 与 WGS84 互转视为恒等（直接返回原值）
- 源或目标为 UNKNOWN 时不转换，直接返回原值
- `transform_document(doc, target)` 遍历文档中所有点执行批量转换，每个对象可独立持有坐标系信息
- 境外点（中国经纬度范围外）跳过所有偏移，保持原始坐标



