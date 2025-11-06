import pathlib
import typing

def get_workspace_path() -> typing.Union[str, None]:
    import os
    """
    Get the workspace folder that contains the Percy config file
    """
    path = pathlib.Path(os.getcwd()).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".percy").is_dir():
            return str(parent)
    return None

def get_data_source_path(source_id: str) -> typing.Union[str, None]:
    """
    Get the base path of an external data source by its ID. Usage: get_data_source_path("my_source")
    """
    workspace_path = get_workspace_path()
    if workspace_path is None:
        return None
    config_path = pathlib.Path(workspace_path) / ".percy" / "current-sources.json"
    if not config_path.is_file():
        return None
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("sources", {}).get(source_id, {}).get("path")

def resolve_file_path(source_id: typing.Union[str, None], relative_path: str) -> typing.Union[str, None]:
    """
    Resolve a path in an external data source. Access files in the workspace by passing None as the first argument. Usage: resolve_file_path("my_source", "relative/path/to/file.csv")
    """
    if source_id is None:
        return str(pathlib.Path(get_workspace_path(), relative_path).resolve())
    base_path = get_data_source_path(source_id)
    if base_path is None:
        return None
    return str((pathlib.Path(base_path) / relative_path).resolve())
