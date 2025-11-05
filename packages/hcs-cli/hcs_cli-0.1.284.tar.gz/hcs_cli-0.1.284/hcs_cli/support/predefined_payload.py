import json
import os.path as path


def load(name: str, as_json: bool = False) -> str:
    file_name = path.join(path.dirname(__file__), f"../payload/{name}")
    file_name = path.abspath(file_name)
    with open(file_name, "rt") as f:
        if as_json:
            return json.load(f)
        return f.read()
