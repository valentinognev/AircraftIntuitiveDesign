# Python/src/aid/jsonc.py
import json
import re

def loads_jsonc(text: str) -> dict:
  lines = []
  for line in text.splitlines():
    if "//" in line:
      in_str = False
      out = []
      i = 0
      while i < len(line):
        c = line[i]
        if c == '"' and (i == 0 or line[i-1] != "\\"):
          in_str = not in_str
          out.append(c)
        elif not in_str and line[i:i+2] == "//":
          break
        else:
          out.append(c)
        i += 1
      lines.append("".join(out))
    else:
      lines.append(line)
  return json.loads("\n".join(lines))
