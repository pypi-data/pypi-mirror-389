import json
from pathlib import Path
from typing import Any, List, Union

import dpath.util
import yaml
from gooey import Gooey, GooeyParser
from jsonpath_ng import jsonpath, parse

from dygo.config import get_program_description, get_program_name

ConfigType = Union[dict, list, str, int, float, bool, None]


def render(path: Union[str, Path]) -> Any:
    path = Path(path)

    cfg = _load_cfg(path)

    dygo_params_map = _find_dygo_params(cfg)

    if not dygo_params_map:
        return cfg

    # key: dest, value: node path
    dygo_param_maps_with_dest = {_get_path_target(node_path, cfg)["dest"]: node_path for node_path in dygo_params_map}

    args = _render_gooey(dygo_param_maps_with_dest, cfg)

    for arg_dest, node_path in dygo_param_maps_with_dest.items():
        value = getattr(args, arg_dest)
        _overwrite_map_target(cfg=cfg, node_path=node_path, value=value)

    return cfg


def _render_gooey(dygo_params_map_with_id: dict, cfg: ConfigType) -> Any:
    # Apply Gooey decorator dynamically at runtime to get current metadata
    gooey_decorator = Gooey(
        program_name=get_program_name(),
        program_description=get_program_description(),
    )

    def _inner_render_gooey():
        parser = GooeyParser(description="dygo parser")

        for _param_id, node_path in dygo_params_map_with_id.items():
            arg_params = _get_path_target(node_path=node_path, cfg=cfg)
            arg_params = _clean_arg_params(arg_params)
            parser.add_argument(**arg_params)

        args = parser.parse_args()
        return args

    # Apply the decorator and call the function
    decorated_function = gooey_decorator(_inner_render_gooey)
    return decorated_function()


def _clean_arg_params(arg_params: dict):
    arg_params.pop("dygo")
    return arg_params


def _get_path_target(node_path: str, cfg: ConfigType):
    return dpath.util.get(obj=cfg, glob=node_path, separator=".")


def _overwrite_map_target(cfg: ConfigType, node_path: str, value):
    dpath.util.set(obj=cfg, glob=node_path, value=value, separator=".")


def _find_dygo_params(cfg: ConfigType) -> List[str]:
    """Extracts all paths to dygo params from the config

    :param cfg: loaded config
    :return: list of . separated paths to dygo params
    """
    # this query searches for all 'dygo' keys
    # https://github.com/json-path/JsonPath
    jsonpath_expr: jsonpath.Descendants = parse("$..dygo")
    matches: list[jsonpath.DatumInContext] = jsonpath_expr.find(cfg)

    # .context for parent node
    return [str(match.context.full_path) for match in matches]


def _load_cfg(path: Path) -> ConfigType:
    if path.suffix == ".json":
        with path.open() as file:
            return json.load(file)

    if path.suffix in {".yaml", ".yml"}:
        with path.open() as file:
            return yaml.safe_load(file)

    msg = f"File ending {path.suffix} not supported"
    raise NotImplementedError(msg)
