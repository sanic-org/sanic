from pathlib import Path

from userguide.worker.factory import create_app

app = create_app(Path(__file__).parent)
