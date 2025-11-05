import re

def is_toon_format(content: str) -> bool:
    # Detect TOON by structural hints (braces, key-value style, etc.)
    # Example heuristic: presence of "extends", braces, and key: "value"
    return bool(re.search(r'\bextends\b', content) and "{" in content and ":" in content)

def toon_to_dict(content: str) -> dict:
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    data = {}
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip().strip('"')
    return data

def dict_to_toon(data: dict) -> str:
    toon_lines = []
    for k, v in data.items():
        toon_lines.append(f"  {k}: \"{v}\"")
    return "ToonFormat {\n" + "\n".join(toon_lines) + "\n}"
