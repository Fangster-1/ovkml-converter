# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

奥维地图数据格式转换工具：把奥维专有的 `.ovkml`（KML 扩展的 XML）和 `.ovobj`（二进制）格式批量转换为标准 KML、Shapefile、DXF。提供 Tkinter 图形界面，支持多文件 / 整文件夹批量转换。

## 常用命令

```bash
# 运行程序（必须用指定解释器）
D:\GD\arcgispro_clone\python.exe main.py

# 安装运行依赖
D:\GD\arcgispro_clone\python.exe -m pip install pyshp

# 打包为单文件 exe（输出到 dist/）
build.bat
```

注意：`build.bat` 用 PyInstaller 的 `--exclude-module` 主动排除了 PyQt5/PyQt6/numpy/ezdxf 等模块以减小体积——这些**确实不是本项目的依赖**，不要误把它们当作缺失项装回来。

## 实际依赖（与文档不符之处）

代码的真实外部依赖**只有 `pyshp`**（`import shapefile`）。需要留意几处历史文档残留：

- `AGENTS.md` 称 UI 用 PyQt5，**实际是 Tkinter**（标准库，见 `ovkml_converter/ui/main_window.py`）。
- DXF 写出是**手写裸 DXF 文本**（`dxf_writer.py`），并未使用 ezdxf。
- `AGENTS.md` 提到 `python -m pytest tests/`，但仓库内**没有 tests 目录**，当前无自动化测试。
- `requirements.txt` 只列了 `pyshp`，是准确的。

修改文档或依赖时请以代码实际 import 为准。

## 架构

数据流是经典的 **解析器 → 统一中间模型 → 写入器** 管线，三层解耦：

```
.ovkml / .ovobj  →  Parser  →  GeoDocument  →  Writer  →  .kml / .shp / .dxf
```

- **中间模型** `ovkml_converter/models/geo_objects.py`：所有格式都先转成 `GeoDocument`（含 `GeoFolder` → `GeoObject` → `GeoPoint` 层级，附 `CoordType`/`GeoType` 枚举）。新增任何输入或输出格式都只需对接这个模型，解析器和写入器互不感知。
- **解析器** `parsers/`：
  - `OvkmlParser`——标准 ElementTree 解析；处理奥维特有的 `<OvCoordType>`、`<OvAttr>` 元素，并对带/不带 KML 命名空间两种写法都做了兼容查找。
  - `OvobjParser`——二进制格式逆向解析（详见 `开发方案.md`）。采用**滑窗扫描 + 坐标合理性校验**（`20<lat<55, 70<lon<140` 才认为是中国境内的有效点）来定位对象，而非依赖固定偏移；这是逆向格式不确定下的容错设计。整数 big-endian、浮点 little-endian，坐标顺序为**纬度,经度**（与 KML 相反）。
- **写入器** `writers/`：`KmlWriter`（stdlib XML）、`ShpWriter`（pyshp，**按几何类型拆成 `_points`/`_lines`/`_polygons` 三个独立 shp**，并写 `.prj` 投影）、`DxfWriter`（裸 DXF 文本，按 folder 名建图层）。
- **UI / 入口**：`main.py` → `ovkml_converter/ui/main_window.py` 的 `run()`。转换在**后台线程**执行，通过 `root.after(0, ...)` 回主线程更新进度，避免阻塞 Tkinter 事件循环。

## 关键约定与注意点

- **坐标系**：内部用 `CoordType` 枚举（WGS84 / GCJ02 / CGCS2000 / UNKNOWN）。OVOBJ 默认按 CGCS2000 处理。SHP 的 `.prj` 和 DXF 的 `$COORDTYPE` 头都会写出坐标系标识，但**代码不做坐标系转换**，只透传标识。
- **坐标顺序陷阱**：KML/OVKML 是 `经度,纬度,高程`；OVOBJ 二进制里是 `纬度,经度`。改解析器时务必注意。
- **OVOBJ 解析是启发式的**：点对象（类型码 4）较可靠；线（2）、面（3）缺少样例验证，可能不准。改动 `_try_parse_object` / `_skip_tail` 后应拿 `奥维格式数据/` 下样例回归验证（如 `姚安县验证.ovobj` 含 32 个点）。
- **参考实现** `6ca3b-main/`：原版工具的预编译二进制（含 `OVKML2KML.exe`），**无源码、仅作行为参考**，不可修改。
- 样例与期望输出在 `奥维格式数据/`（含已生成的 `_points.shp/.dbf/.shx`），可作为手动验证基准。
