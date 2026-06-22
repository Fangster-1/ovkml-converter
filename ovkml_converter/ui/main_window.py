import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ovkml_converter.parsers import OvkmlParser, OvobjParser
from ovkml_converter.writers import KmlWriter, ShpWriter, DxfWriter


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("奥维数据格式转换工具")
        self.root.geometry("650x520")
        self.root.minsize(600, 480)

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

        dir_frame = ttk.Frame(self.root)
        dir_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(dir_frame, text="输出目录:").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(dir_frame, textvariable=self.output_dir_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(dir_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(self.root, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var).pack(fill=tk.X, padx=10)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        self.convert_btn = ttk.Button(btn_frame, text="开始转换", command=self.start_convert)
        self.convert_btn.pack(side=tk.RIGHT, padx=5)

    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("奥维文件", "*.ovkml *.ovobj"), ("所有文件", "*.*")]
        )
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_listbox.insert(tk.END, f)

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            for ext in ("*.ovkml", "*.ovobj"):
                for f in Path(folder).glob(ext):
                    fp = str(f)
                    if fp not in self.files:
                        self.files.append(fp)
                        self.file_listbox.insert(tk.END, fp)

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

        thread = threading.Thread(target=self._do_convert, args=(list(self.files), self.output_format.get(), output_dir), daemon=True)
        thread.start()

    def _do_convert(self, files, fmt, output_dir):
        ovkml_parser = OvkmlParser()
        ovobj_parser = OvobjParser()
        kml_writer = KmlWriter()
        shp_writer = ShpWriter()
        dxf_writer = DxfWriter()

        success = 0
        fail = 0

        for i, filepath in enumerate(files):
            try:
                self.root.after(0, lambda v=i, m=f"正在处理: {Path(filepath).name}": self._update_progress(v, m))

                ext = Path(filepath).suffix.lower()
                if ext == ".ovkml":
                    doc = ovkml_parser.parse(filepath)
                elif ext == ".ovobj":
                    doc = ovobj_parser.parse(filepath)
                else:
                    raise ValueError(f"不支持的格式: {ext}")

                stem = Path(filepath).stem
                out = Path(output_dir)

                if fmt in ("kml", "all"):
                    kml_writer.write(doc, str(out / f"{stem}.kml"))
                if fmt in ("shp", "all"):
                    shp_writer.write(doc, str(out / f"{stem}.shp"))
                if fmt in ("dxf", "all"):
                    dxf_writer.write(doc, str(out / f"{stem}.dxf"))

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
