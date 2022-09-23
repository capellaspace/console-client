import json
from uuid import UUID
from pathlib import Path
from typing import List, Dict, Any, Iterable


class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)


def convert_to_uuid_str(dict_args: Dict[str, Any], uuid_arg_names: Iterable[str]) -> Dict[str, Any]:
    for conv in uuid_arg_names:
        if dict_args.get(conv):
            dict_args[conv] = str(dict_args[conv])

    return dict_args
