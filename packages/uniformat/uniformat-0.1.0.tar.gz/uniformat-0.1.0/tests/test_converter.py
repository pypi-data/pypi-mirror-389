from uniformat.converter import UniformatConverter
from uniformat.enums import DataFormat

def test_json_to_yaml():
    json_data = '{"name": "Alice", "age": 30}'
    output = UniformatConverter.convert(json_data, DataFormat.YAML)
    assert "name: Alice" in output
