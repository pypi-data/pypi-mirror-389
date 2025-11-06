from .helpers import get_workspace_path
import json
import pathlib

def get_specialties() -> dict | None:
  workspace_path = get_workspace_path()
  if workspace_path is None:
    return None
  config_path = pathlib.Path(workspace_path) / ".percy" / ".specialties-env.json"
  if not config_path.is_file(): 
    return None
  with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
  return config