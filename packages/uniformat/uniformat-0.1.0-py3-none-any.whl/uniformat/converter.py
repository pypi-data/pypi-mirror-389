import json
import yaml
import xmltodict
from .detectors import detect_format
from .enums import DataFormat
from .parsers.toon_parser import toon_to_dict, dict_to_toon


class UniformatConverter:
    """
    A universal converter that automatically detects data format (JSON, YAML, XML, TOON)
    and converts it to the desired target format.

    Supports configurable defaults (set at init) and per-call overrides.
    """

    def __init__(
        self,
        default_target: DataFormat = DataFormat.JSON,
        json_indent: int = 2,
        xml_pretty: bool = True,
        yaml_sort_keys: bool = False,
    ):
        """
        :param default_target: Default output format if not specified.
        :param json_indent: Default indentation for JSON output.
        :param xml_pretty: Default pretty-printing for XML output.
        :param yaml_sort_keys: Default sorting for YAML keys.
        """
        self.default_target = default_target
        self.json_indent = json_indent
        self.xml_pretty = xml_pretty
        self.yaml_sort_keys = yaml_sort_keys

    def convert(
        self,
        content: str,
        target_format: DataFormat | None = None,
        json_indent: int | None = None,
        xml_pretty: bool | None = None,
        yaml_sort_keys: bool | None = None,
    ) -> str:
        """
        Convert the given content to the target format.

        Optional formatting parameters (json_indent, xml_pretty, yaml_sort_keys)
        override defaults for this call only.
        """
        source_format = detect_format(content)
        target_format = target_format or self.default_target

        # Resolve formatting options (fallback to defaults)
        json_indent = json_indent if json_indent is not None else self.json_indent
        xml_pretty = xml_pretty if xml_pretty is not None else self.xml_pretty
        yaml_sort_keys = (
            yaml_sort_keys if yaml_sort_keys is not None else self.yaml_sort_keys
        )

        # Step 1: Parse input
        if source_format == DataFormat.JSON:
            data = json.loads(content)
        elif source_format == DataFormat.YAML:
            data = yaml.safe_load(content)
        elif source_format == DataFormat.XML:
            data = xmltodict.parse(content)
        elif source_format == DataFormat.TOON:
            data = toon_to_dict(content)
        else:
            raise ValueError(f"Unsupported source format: {source_format}")

        # Step 2: Convert to target format
        if target_format == DataFormat.JSON:
            return json.dumps(data, indent=json_indent)
        elif target_format == DataFormat.YAML:
            return yaml.dump(data, sort_keys=yaml_sort_keys)
        elif target_format == DataFormat.XML:
            return xmltodict.unparse(data, pretty=xml_pretty)
        elif target_format == DataFormat.TOON:
            return dict_to_toon(data)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
