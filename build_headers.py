from pathlib import Path

HEADER = '''"""
VYPa 2025 — VYPlanguage Compiler
Authors: AUTHOR_NAME_1 (xlogin01), AUTHOR_NAME_2 (xlogin02)
"""
'''

files = list(Path("src").glob("*.py")) + [Path("vypcomp")]
for path in files:
    text = path.read_text(encoding="utf-8")
    if "VYPa 2025" in text[:400]:
        print("skip", path)
        continue

    if path.name == "vypcomp":
        lines = text.splitlines(True)
        shebang = ""
        if lines and lines[0].startswith("#!"):
            shebang = lines[0]
            text = "".join(lines[1:]).lstrip("\n")
        if text.startswith('"""'):
            end = text.find('"""', 3)
            if end != -1:
                text = text[end + 3 :].lstrip("\n")
        path.write_text(shebang + HEADER + "\n" + text, encoding="utf-8")
        print("updated", path)
        continue

    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end != -1:
            text = text[end + 3 :].lstrip("\n")
    path.write_text(HEADER + "\n" + text, encoding="utf-8")
    print("updated", path)
