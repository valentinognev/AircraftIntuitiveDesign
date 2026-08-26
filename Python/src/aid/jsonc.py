# Python/src/aid/jsonc.py
import json


def loads_jsonc(text: str) -> dict:
    lines = []
    for line in text.splitlines():
        if "//" in line:
            in_str = False
            out = []
            i = 0
            while i < len(line):
                c = line[i]
                if c == '"' and (i == 0 or line[i - 1] != "\\"):
                    in_str = not in_str
                    out.append(c)
                elif not in_str and line[i : i + 2] == "//":
                    break
                else:
                    out.append(c)
                i += 1
            lines.append("".join(out))
        else:
            lines.append(line)
    return json.loads("\n".join(lines))


def _lookup_doc(path_parts: list[str], docs: dict) -> str:
    path = ".".join(path_parts)
    if path in docs:
        return docs[path]
    stripped = ".".join(p for p in path_parts if not p.isdigit())
    if stripped in docs:
        return docs[stripped]
    if path_parts and path_parts[0] == "NP":
        for part in reversed(path_parts):
            if not part.isdigit() and part != "NP":
                wg_key = f"WG.{part}"
                if wg_key in docs:
                    return docs[wg_key]
    if path_parts and path_parts[0] == "NB":
        for part in reversed(path_parts):
            if not part.isdigit() and part != "NB":
                bd_key = f"BD.{part}"
                if bd_key in docs:
                    return docs[bd_key]
    raise KeyError(path)


def _json_scalar(value) -> str:
    return json.dumps(value)


def _is_inline(value) -> bool:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, list):
        if not value:
            return True
        return all(
            item is None or isinstance(item, (bool, int, float, str))
            for item in value
        )
    return False


def _emit_list_contents(lst: list, path_parts: list[str], docs: dict, lines: list[str], indent: int) -> None:
    pad = " " * indent
    for i, item in enumerate(lst):
        is_last = i == len(lst) - 1
        comma = "" if is_last else ","
        item_path = path_parts + [str(i)]
        if item is None:
            lines.append(pad + "null" + comma)
        elif _is_inline(item):
            lines.append(pad + _json_scalar(item) + comma)
        elif isinstance(item, dict):
            lines.append(pad + "{")
            _emit_dict_contents(item, item_path, docs, lines, indent + 4)
            lines.append(pad + "}" + comma)
        elif isinstance(item, list):
            if _is_inline(item):
                lines.append(pad + _json_scalar(item) + comma)
            else:
                lines.append(pad + "[")
                _emit_list_contents(item, item_path, docs, lines, indent + 4)
                lines.append(pad + "]" + comma)
        else:
            raise TypeError(type(item))


def _emit_dict_contents(d: dict, path_parts: list[str], docs: dict, lines: list[str], indent: int) -> None:
    pad = " " * indent
    items = list(d.items())
    for i, (key, value) in enumerate(items):
        key_path = path_parts + [key]
        doc = _lookup_doc(key_path, docs)
        is_last = i == len(items) - 1
        comma = "" if is_last else ","
        comment = f" // {doc}"
        if _is_inline(value):
            lines.append(f'{pad}"{key}": {_json_scalar(value)}{comma}{comment}')
        elif isinstance(value, dict):
            lines.append(f'{pad}"{key}": {{{comment}')
            _emit_dict_contents(value, key_path, docs, lines, indent + 4)
            lines.append(pad + "}" + comma)
        elif isinstance(value, list):
            if _is_inline(value):
                lines.append(f'{pad}"{key}": {_json_scalar(value)}{comma}{comment}')
            else:
                lines.append(f'{pad}"{key}": [{comment}')
                _emit_list_contents(value, key_path, docs, lines, indent + 4)
                lines.append(pad + "]" + comma)
        else:
            raise TypeError(type(value))


def dumps_jsonc(data: dict, docs: dict) -> str:
    lines: list[str] = []
    lines.append("{")
    _emit_dict_contents(data, [], docs, lines, 4)
    lines.append("}")
    return "\n".join(lines) + "\n"
