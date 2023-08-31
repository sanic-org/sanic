from pathlib import Path

from webapp.worker.factory import create_app

app = create_app(Path(__file__).parent)
