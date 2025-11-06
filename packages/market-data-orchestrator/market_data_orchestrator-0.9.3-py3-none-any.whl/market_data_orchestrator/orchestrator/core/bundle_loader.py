"""
Bundle configuration loader with Jinja2 templating support.

Loads YAML bundle specs and renders templates with runtime variables.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2
import yaml

logger = logging.getLogger(__name__)


def load_bundle(path: str | Path) -> dict[str, Any]:
    """
    Load and template a YAML bundle configuration.

    Args:
        path: Path to the bundle YAML file

    Returns:
        Parsed bundle configuration dictionary

    Raises:
        FileNotFoundError: If bundle file doesn't exist
        yaml.YAMLError: If YAML is invalid
        jinja2.TemplateError: If template rendering fails

    Example:
        >>> bundle = load_bundle("config/bundles/replay.yaml")
        >>> bundle["bundle_name"]
        'replay_and_export'
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Bundle not found: {path}")

    logger.info(f"Loading bundle from {path}")

    with open(path_obj) as f:
        raw_yaml = f.read()

    # Render Jinja2 template with context
    template = jinja2.Template(raw_yaml)
    context = {
        "today": datetime.utcnow().date(),
        "now": datetime.utcnow(),
    }
    rendered = template.render(**context)

    # Parse YAML
    try:
        config = yaml.safe_load(rendered)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML from {path}: {e}")
        raise

    logger.debug(f"Loaded bundle: {config.get('bundle_name', 'unknown')}")
    return config

