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

## 实际依赖

代码的真实外部依赖**只有 `pyshp`**（`import shapefile`）。几点说明：

- UI 是 **Tkinter**（标准库，见 `ovkml_converter/ui/main_window.py`），不是 PyQt。
- DXF 写出是**手写裸 DXF 文本**（`dxf_writer.py`），并未使用 ezdxf。
- 坐标转换是**纯 `math` 实现，无新增依赖**。
- 仓库现有 `tests/` 目录（pytest，35 个测试覆盖坐标转换、OVOBJ 分组、各写入器）。运行：`D:\GD\arcgispro_clone\python.exe -m pytest tests/ -v`。
- `开发方案.md` 是早期设计稿，其中"用 PyQt5/ezdxf""有固定二进制头结构"等说法**与最终实现不符**，以代码实际 import 为准。本次坐标转换等改动的设计/计划见 `docs/superpowers/`。

## 架构

数据流是 **解析器 → 统一中间模型 →（坐标转换）→ 写入器** 管线，由 `convert/conversion_service.py` 编排：

```
.ovkml / .ovobj  →  Parser  →  GeoDocument  →  transform_document  →  Writer  →  .kml / .shp / .dxf
```

`conversion_service.convert_file()` 是统一入口：解析 → 源坐标系判定 → 坐标转换 → 多格式写出。UI 只收集参数、调用它。

- **中间模型** `ovkml_converter/models/geo_objects.py`：所有格式都先转成 `GeoDocument`（含 `GeoFolder` → `GeoObject` → `GeoPoint` 层级，附 `CoordType`/`GeoType` 枚举）。新增任何输入或输出格式都只需对接这个模型，解析器和写入器互不感知。
- **解析器** `parsers/`：
  - `OvkmlParser`——标准 ElementTree 解析；处理奥维特有的 `<OvCoordType>`、`<OvAttr>` 元素，并对带/不带 KML 命名空间两种写法都做了兼容查找。
  - `OvobjParser`——二进制格式逆向解析（详见 `开发方案.md`）。采用**滑窗扫描 + 坐标合理性校验**（`20<lat<55, 70<lon<140` 才认为是中国境内的有效点）来定位对象，而非依赖固定偏移；这是逆向格式不确定下的容错设计。整数 big-endian、浮点 little-endian，坐标顺序为**纬度,经度**（与 KML 相反）。**文件夹分组**用 `_assign_to_folders`：每个对象归属到其字节偏移之前**最近的文件夹名标记**（不是平均分配）。
- **坐标转换** `transforms/coordinate_transform.py`：纯 `math` 实现 WGS84/GCJ02/BD09 互转（CGCS2000 按等同 WGS84 处理），境外点自动跳过偏移。`transform_document(doc, target)` 集中转换一次，`target=UNKNOWN` 表示"与输入一致"（不转换）。
- **写入器** `writers/`：`KmlWriter`（stdlib XML，带 UTF-8 声明）、`ShpWriter`（pyshp，**按几何类型拆成 `_points`/`_lines`/`_polygons` 三个独立 shp**，写 `.prj`+`.cpg`+`FOLDER` 字段，多边形外环顺时针）、`DxfWriter`（裸 DXF 文本，含 `$ACADVER`+`LAYER` 表，按 folder 名建图层）。
- **UI / 入口**：`main.py` → `ovkml_converter/ui/main_window.py` 的 `run()`。有"目标坐标系/OVOBJ 源坐标系"两个下拉。转换在**后台线程**执行，通过 `root.after(0, ...)` 回主线程更新进度，避免阻塞 Tkinter 事件循环。

## 关键约定与注意点

- **坐标系**：内部用 `CoordType` 枚举（WGS84 / GCJ02 / CGCS2000 / BD09 / UNKNOWN）。**现在会做实际坐标转换**（见 `transforms/`）：默认"与输入一致"不转换，用户在 UI 选目标系才纠偏。源坐标系判定——OVKML 读 `<OvCoordType>` 自动检测（逐对象保留）；OVOBJ 无该信息，用同名 `.ovkml` 兜底、否则用 UI 手选（默认 CGCS2000）。CGCS2000≈WGS84（恒等），真正有偏移的是 GCJ02/BD09。
- **坐标顺序陷阱**：KML/OVKML 是 `经度,纬度,高程`；OVOBJ 二进制里是 `纬度,经度`。改解析器时务必注意。
- **OVOBJ 解析是启发式的**：点对象（类型码 4）较可靠；线（2）、面（3）缺少样例验证，可能不准。改动 `_try_parse_object` / `_skip_tail` 后应拿 `奥维格式数据/` 下样例回归验证（如 `姚安县验证.ovobj` 含 32 个点）。
- 样例与期望输出在 `奥维格式数据/`（含已生成的 `_points.shp/.dbf/.shx`），可作为手动验证基准。
