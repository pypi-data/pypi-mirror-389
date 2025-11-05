import json, yaml, xml.etree.ElementTree as ET
from .enums import DataFormat
from .parsers.toon_parser import is_toon_format

def detect_format(content: str) -> DataFormat:
    try:
        json.loads(content)
        return DataFormat.JSON
    except Exception:
        pass

    try:
        yaml.safe_load(content)
        return DataFormat.YAML
    except Exception:
        pass

    try:
        ET.fromstring(content)
        return DataFormat.XML
    except Exception:
        pass

    if is_toon_format(content):
        return DataFormat.TOON

    raise ValueError("Unknown data format")
