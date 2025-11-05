import argparse
from .converter import UniformatConverter
from .enums import DataFormat

def main():
    parser = argparse.ArgumentParser(description="Uniformat CLI Tool")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument("--to", required=True, choices=[f.value for f in DataFormat])

    args = parser.parse_args()

    with open(args.input, 'r') as f:
        content = f.read()

    converted = UniformatConverter.convert(content, DataFormat(args.to))

    with open(args.output, 'w') as f:
        f.write(converted)

if __name__ == "__main__":
    main()
