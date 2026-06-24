import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ovkml_converter.convert.conversion_service import convert_file, detect_ovkml_crs
from ovkml_converter.models.geo_objects import CoordType

# 输出（目标）坐标系候选：首项"与输入坐标系一致"为默认，表示不转换
CRS_LABELS = ["与输入坐标系一致", "WGS84", "CGCS2000", "GCJ02", "BD09"]
# 输入（原）坐标系候选：均为具体坐标系，无"一致"项
INPUT_CRS_LABELS = ["CGCS2000", "WGS84", "GCJ02", "BD09"]
_LABEL_TO_CRS = {
    "与输入坐标系一致": CoordType.UNKNOWN,
    "WGS84": CoordType.WGS84,
    "CGCS2000": CoordType.CGCS2000,
    "GCJ02": CoordType.GCJ02,
    "BD09": CoordType.BD09,
}


def label_to_crs(label: str) -> CoordType:
    return _LABEL_TO_CRS.get(label, CoordType.UNKNOWN)


def crs_to_label(crs: CoordType) -> str:
    """把具体坐标系映射回输入下拉的标签；非具体值回落 CGCS2000。"""
    return crs.value if crs.value in INPUT_CRS_LABELS else "CGCS2000"


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("奥维数据格式转换工具")
        self.root.geometry("660x660")
        self.root.minsize(620, 600)

        self.files = []
        self.worker = None

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Button(toolbar, text="添加文件", command=self.add_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="清空", command=self.clear_files).pack(side=tk.LEFT, padx=2)

        list_frame = ttk.LabelFrame(self.root, text="文件列表")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        fmt_frame = ttk.LabelFrame(self.root, text="输出格式")
        fmt_frame.pack(fill=tk.X, padx=10, pady=5)

        self.output_format = tk.StringVar(value="kml")
        ttk.Radiobutton(fmt_frame, text="KML", variable=self.output_format, value="kml").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(fmt_frame, text="SHP", variable=self.output_format, value="shp").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(fmt_frame, text="DXF", variable=self.output_format, value="dxf").pack(side=tk.LEFT, padx=15)
        ttk.Radiobutton(fmt_frame, text="全部", variable=self.output_format, value="all").pack(side=tk.LEFT, padx=15)

        crs_frame = ttk.LabelFrame(self.root, text="坐标系")
        crs_frame.pack(fill=tk.X, padx=10, pady=5)

        crs_row = ttk.Frame(crs_frame)
        crs_row.pack(fill=tk.X, padx=5, pady=(4, 0))

        # 输入（原）坐标系——放左侧；OVKML 自动检测回填，OVOBJ 手动设置
        ttk.Label(crs_row, text="输入坐标系:").pack(side=tk.LEFT, padx=(5, 2))
        self.input_crs_var = tk.StringVar(value="CGCS2000")
        ttk.Combobox(crs_row, textvariable=self.input_crs_var,
                     values=INPUT_CRS_LABELS, state="readonly", width=12).pack(side=tk.LEFT, padx=2)

        # 输出（目标）坐标系——放右侧；默认"与输入坐标系一致"
        ttk.Label(crs_row, text="输出坐标系:").pack(side=tk.LEFT, padx=(24, 2))
        self.target_crs_var = tk.StringVar(value=CRS_LABELS[0])
        ttk.Combobox(crs_row, textvariable=self.target_crs_var,
                     values=CRS_LABELS, state="readonly", width=16).pack(side=tk.LEFT, padx=2)

        ttk.Label(crs_frame,
                  text="提示：输出坐标系默认与输入保持一致；如需纠偏可自行选择目标坐标系。"
                       "OVKML 会自动识别输入坐标系，OVOBJ 请手动设置输入坐标系。",
                  foreground="gray", wraplength=600, justify=tk.LEFT).pack(
            fill=tk.X, padx=8, pady=(2, 4))

        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(dir_frame, text="输出目录:").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT)

        # 以下控件用 side=BOTTOM 逆序钉在窗口底部，确保无论窗口高度如何，
        # "开始转换"按钮与署名始终可见（中间的文件列表会自动让出空间）。
        author_label = tk.Label(
            self.root,
            text="作者：方庆坪    联系方式（微信同号）：19988312343",
            font=("楷体", 10))
        author_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(2, 6))

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        self.convert_btn = ttk.Button(btn_frame, text="开始转换", command=self.start_convert)
        self.convert_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var).pack(side=tk.BOTTOM, fill=tk.X, padx=10)

        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("奥维文件", "*.ovkml *.ovobj"), ("所有文件", "*.*")]
        )
        added = []
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, f)
                added.append(f)
        self._auto_detect_input_crs(added)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            added = []
            for ext in ("*.ovkml", "*.ovobj"):
                for f in Path(folder).glob(ext):
                    fp = str(f)
                    if fp not in self.files:
                        self.files.append(fp)
                        self.file_listbox.insert(tk.END, fp)
                        added.append(fp)
            self._auto_detect_input_crs(added)

    def _auto_detect_input_crs(self, added_files):
        """新增文件中若有 OVKML，自动把"输入坐标系"下拉设为其检测到的坐标系。"""
        for f in added_files:
            crs = detect_ovkml_crs(f)
            if crs is not None:
                self.input_crs_var.set(crs_to_label(crs))
                self.status_var.set(f"已自动识别输入坐标系: {crs.value}（来自 {Path(f).name}）")
                return

    def clear_files(self):
        self.files.clear()
        self.file_listbox.delete(0, tk.END)

    def browse_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_dir_var.set(folder)

    def start_convert(self):
        if not self.files:
            messagebox.showwarning("提示", "请先添加要转换的文件")
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showwarning("提示", "请选择输出目录")
            return

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        self.convert_btn.config(state=tk.DISABLED)
        self.progress["maximum"] = len(self.files)
        self.progress["value"] = 0

        target_crs = label_to_crs(self.target_crs_var.get())
        ovobj_src = label_to_crs(self.input_crs_var.get())
        thread = threading.Thread(
            target=self._do_convert,
            args=(list(self.files), self.output_format.get(), output_dir, target_crs, ovobj_src),
            daemon=True)
        thread.start()

    def _do_convert(self, files, fmt, output_dir, target_crs, ovobj_src):
        fmt_list = ["kml", "shp", "dxf"] if fmt == "all" else [fmt]
        success = 0
        fail = 0
        for i, filepath in enumerate(files):
            try:
                self.root.after(0, lambda v=i, m=f"正在处理: {Path(filepath).name}": self._update_progress(v, m))
                res = convert_file(filepath, target_crs, ovobj_src, fmt_list, output_dir, sibling_files=files)
                msg = f"{Path(filepath).name}: 源={res['source_crs'].value} → 目标={res['target_crs'].value}"
                if res["out_of_china"]:
                    msg += "（含境外点，未做偏移）"
                self.root.after(0, lambda m=msg: self.status_var.set(m))
                success += 1
            except Exception as e:
                fail += 1
                self.root.after(0, lambda m=f"错误: {Path(filepath).name} - {e}": self.status_var.set(m))
        self.root.after(0, lambda: self._finish(success, fail))

    def _update_progress(self, value, msg):
        self.progress["value"] = value
        self.status_var.set(msg)

    def _finish(self, success, fail):
        self.convert_btn.config(state=tk.NORMAL)
        self.progress["value"] = self.progress["maximum"]
        self.status_var.set(f"完成: 成功 {success}, 失败 {fail}")
        messagebox.showinfo("完成", f"转换完成\n成功: {success}\n失败: {fail}")

    def run(self):
        self.root.mainloop()


def run():
    app = MainWindow()
    app.run()
