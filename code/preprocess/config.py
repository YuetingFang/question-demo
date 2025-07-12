#!/usr/bin/env python3
"""
Centralized configuration for the preprocessing pipeline.
Contains all hyperparameters and default paths used across the preprocessing scripts.
"""

import os
from pathlib import Path
from typing import Dict, Any

# --- Base Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "results/preprocess"
LOGS_DIR = BASE_DIR / "results/logs"
TEMPLATES_DIR = BASE_DIR / "src/templates"

# --- Default File Paths ---
DEFAULT_PATHS = {
    "schema": RESULTS_DIR / "preprocess_dev_tables.json",
    "examples": RESULTS_DIR / "sampled_debit_card.json",
    "task_desc_output": RESULTS_DIR / "task_descriptions.json",
    "column_desc_output": RESULTS_DIR / "dictionary_column_descriptions.json",
    "task_desc_prompt": TEMPLATES_DIR / "template_task_description.txt",
    "column_desc_prompt": TEMPLATES_DIR / "template_column_descriptions.txt",
    "db_overview_prompt": TEMPLATES_DIR / "template_db_overview.txt",
    "log_dir": LOGS_DIR,
}

# --- LLM Configuration ---
# gpt-4.1-mini
LLM_CONFIG = {
    "model": "gpt-4.1",
    "temperature": 0.2,
    "batch_size": 1,  # For future batch processing support
}

# --- Environment Configuration ---
ENV_PATH = BASE_DIR / ".env"

def get_config() -> Dict[str, Any]:
    """
    Get the complete configuration dictionary.
    
    Returns:
        Dictionary containing all configuration parameters.
    """
    return {
        "base_dir": BASE_DIR,
        "results_dir": RESULTS_DIR,
        "templates_dir": TEMPLATES_DIR,
        "paths": DEFAULT_PATHS,
        "llm": LLM_CONFIG,
        "env_path": ENV_PATH,
    }

def ensure_output_dirs():
    """
    Ensure all necessary output directories exist.
    """
    # Create all output directories
    for path_key, path in DEFAULT_PATHS.items():
        if "output" in path_key or path_key.startswith("task_"):
            output_dir = path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"Ensured output directory exists: {output_dir}")
    
    # Make sure the main results and logs directories exist
    (RESULTS_DIR).mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
