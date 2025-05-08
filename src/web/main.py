import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import uvicorn
from src.web.api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 