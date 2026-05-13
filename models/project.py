from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProjectConfig:
    name: str = "workbench"
    version: str = "0.1.0"
    data_dir: str = field(default_factory=lambda: str(Path.home() / ".workbench"))
