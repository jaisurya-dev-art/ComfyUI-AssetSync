from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversionResult:
    success: bool
    source_path: str
    output_path: Optional[str]
    output_format: Optional[str]
    texture_paths: List[str] = field(default_factory=list)
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

