# Uniformat — Universal Format Converter

Uniformat automatically detects and converts between JSON, YAML, XML, and TOON formats.

## Install
```bash
pip install uniformat
```

## Usage
```python
from uniformat import UniformatConverter, DataFormat

json_data = '{"name": "Sumeet"}'
yaml_data = UniformatConverter.convert(json_data, DataFormat.YAML)
print(yaml_data)
```

CLI usage:
```bash
uniformat input.json output.yaml --to yaml
```
