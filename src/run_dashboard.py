#!/usr/bin/env python
import streamlit.web.cli as stcli
import sys
from pathlib import Path

if __name__ == "__main__":
    dashboard_path = str(Path(__file__).resolve().parent.parent / 'src' / 'dashboard.py')
    sys.argv = [
        "streamlit", "run",
        dashboard_path,
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true"
    ]
    sys.exit(stcli.main())
