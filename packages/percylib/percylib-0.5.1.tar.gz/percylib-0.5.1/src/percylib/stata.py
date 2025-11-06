import stata_setup
from .specialties import get_specialties

def setup_stata():
  specialties = get_specialties()
  if specialties is None:
    return
  stata = specialties.get("stata", {})
  stata_path = stata.get("stataPath", None)
  edition = stata.get("edition", None)

  if stata_path is None or edition is None:
    raise ValueError("Stata setup requires both 'stataPath' and 'edition' to be specified in .percy/.specialties-env.json under the 'stata' key. Open the Percy project page to set these values.")
  stata_setup.config(stata_path, edition, splash=False)