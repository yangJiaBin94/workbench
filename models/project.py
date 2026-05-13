from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class ProjectConfig:
    name: str = "workbench"
    version: str = "0.1.0"
    data_dir: str = field(default_factory=lambda: str(PROJECT_ROOT / "data"))
