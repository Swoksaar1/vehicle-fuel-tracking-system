import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fuel_system.settings")

from waitress import serve
from fuel_system.wsgi import application


if __name__ == "__main__":
    print("Starting Django backend on http://127.0.0.1:8000")
    serve(application, host="127.0.0.1", port=8000, threads=8)