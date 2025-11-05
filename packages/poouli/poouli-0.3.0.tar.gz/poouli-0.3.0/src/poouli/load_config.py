import os
from pathlib import Path
from typing import List, Optional
import pywikibot as wk
import pypandoc as pdc
import yaml
import frontmatter as fm

def config_paths(
	base_dir: Path,
	filenames: List[str] = ('config.yaml', 'config.yml', 'poouli.yml', 'poouli.yaml')
) -> List[Path]:
	"""Return a list of possible config file paths inside *base_dir*."""
	return [base_dir / name for name in filenames]

def load_config(
	filenames: List[str] = ('config.yaml', 'config.yml', 'poouli.yml', 'poouli.yaml')) -> dict:
	"""
	Load a YAML configuration file, accepting both `.yaml` and `.yml` extensions.

	Search order:
	1. Current working directory (pwd)
	2. User's global config directory: ~/.config/poouli/
	"""
	for path in config_paths(Path.cwd(), filenames):
		if path.is_file():
			config_path = path
			break
	else:
		global_dir = Path.home() / '.config' / 'poouli'
		for path in config_paths(global_dir, filenames):
			if path.is_file():
				config_path = path
				break
		else:
			print(
				f'⚠️ No config file found in cwd or {global_dir} '
				f'(tried: {', '.join(str(p) for p in config_paths(Path.cwd(), filenames))})'
			)
			return {}

	try:
		with open(config_path, 'r', encoding='utf-8') as f:
			cfg = yaml.safe_load(f) or {}
		print(f"✅ Loaded config from: {config_path}")
		return cfg
	except yaml.YAMLError as exc:
		print(f"❌ Failed to parse YAML ({config_path}): {exc}")
		return {}
	except Exception as exc:
		print(f"❌ Unexpected error while reading {config_path}: {exc}")
		return {}
