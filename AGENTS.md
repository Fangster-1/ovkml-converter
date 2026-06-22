# AGENTS.md

## 项目概述

奥维地图数据格式转换工具，支持将 OVOBJ (二进制) 和 OVKML (XML) 格式转换为标准 KML、Shapefile (SHP) 和 DXF (CAD) 格式。

## 仓库结构

- `6ca3b-main/` — 原始参考工具（预编译二进制，仅作参考）
- `奥维格式数据/` — 样例数据文件
  - `姚安县验证.ovobj` — OVOBJ 格式样例（32个点对象）
  - `姚安县验证B线.ovkml` — OVKML 格式样例
- `ovkml_converter/` — Python 源码
  - `parsers/` — 格式解析器（OvkmlParser, OvobjParser）
  - `writers/` — 格式写入器（KmlWriter, ShpWriter, DxfWriter）
  - `models/` — 数据模型
  - `ui/` — PyQt5 界面
- `main.py` — 程序入口
- `dist/` — 打包输出的 exe 文件
- `build.bat` — 打包脚本

## 格式分析结果

### OVKML 格式
- 基于标准 KML 扩展的 XML 格式
- 特有元素: `<OvAttr>`, `<OvCoordType>`
- 坐标顺序: 经度,纬度,高程
- 坐标系: CGCS2000/GCJ02/WGS84

### OVOBJ 格式 (已逆向解析)
- 二进制格式，Magic: "OviO"
- 字节序: 整数 big-endian，浮点数 little-endian
- 坐标顺序: 纬度,经度（与 KML 相反）
- 对象类型码: 4=点对象
- 详见 `开发方案.md`

## 开发环境

- Python 3.13+ (使用 `D:\GD\arcgispro_clone\python.exe`)
- 依赖: `pip install PyQt5 pyshp ezdxf pyinstaller`

## 常用命令

```bash
# 运行程序
python main.py

# 打包为 exe
build.bat
# 或手动执行:
pyinstaller --onefile --windowed --name "奥维数据格式转换" main.py

# 运行测试
python -m pytest tests/
```

## 注意事项

- 原始参考工具 (`6ca3b-main/`) 不含源码，无法修改
- OVOBJ 格式解析基于逆向工程，可能不完全准确
- 需要更多样例数据验证线、面对象的解析
- `LICENSE` 中 `[year]` 和 `[fullname]` 为占位符，尚未填写
- exe 文件较大（~192MB）因为包含了完整的 Python 运行时和 Qt 库
