import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ovkml_converter.ui.main_window import run

if __name__ == '__main__':
    run()
