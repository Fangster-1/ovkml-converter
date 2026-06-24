# 奥维数据格式转换工具

将奥维地图的 `.ovkml` 和 `.ovobj` 格式批量转换为标准 KML、Shapefile、DXF 格式。

## 功能

- 支持 `.ovkml`（XML）和 `.ovobj`（二进制）两种奥维专有格式
- 输出为标准 KML、Shapefile（SHP）、DXF（CAD）
- 支持多文件和整文件夹批量转换
- 坐标系转换：WGS84 / CGCS2000 / GCJ02 / BD09 互转
- OVKML 自动识别输入坐标系
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

1. 点击「添加文件」或「添加文件夹」导入 `.ovkml` / `.ovobj` 文件
2. 选择输出格式（KML / SHP / DXF / 全部）
3. 设置输入坐标系（OVKML 会自动识别，OVOBJ 需手动选择）
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
    │   ├── ovkml_parser.py          # OVKML 解析器
    │   └── ovobj_parser.py          # OVOBJ 二进制解析器
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
.ovkml / .ovobj  →  Parser  →  GeoDocument  →  坐标转换  →  Writer  →  .kml / .shp / .dxf
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

### OVOBJ 格式

OVOBJ 是二进制格式，结构如下：

```
文件头:
  [0x00-0x04] Magic: "OviO" (4 bytes)
  [0x04-0x0C] 保留 (8 bytes, 全零)
  [0x0C-0x10] 对象总数 (4 bytes, big-endian int)
  [0x10-0xF0] 保留 (大量零填充)

文件夹记录 (重复):
  [0xF0-0xF4] 文件夹名称长度 N (4 bytes, big-endian int)
  [0xF4-0xF4+N] 文件夹名称 (UTF-8 字符串)

对象记录 (重复):
  [coord+0]  纬度 (8 bytes, little-endian double)
  [coord+8]  经度 (8 bytes, little-endian double)
  [coord+16] 填充 (4 bytes, big-endian int, 通常为 0)
  [coord+20] 对象类型 (4 bytes, big-endian int, 4=点)
  [coord+24] 标志位 (4 bytes, big-endian int, 1=有名称)
  [coord+28] 名称长度 N (4 bytes, big-endian int)
  [coord+32] 名称 (N bytes, UTF-8 字符串)
  [coord+32+N] 属性数据 (变长)
```

关键特征：
- 坐标存储顺序：`纬度, 经度`（与 KML 相反）
- 整数使用 big-endian 字节序，浮点数使用 little-endian 字节序
- 对象类型码：4 = 点，2 = 线，3 = 面
- OVOBJ 不存储坐标系信息，需通过同名 `.ovkml` 文件或手动指定

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



## 作者

方庆坪 · 微信同号：19988312343
