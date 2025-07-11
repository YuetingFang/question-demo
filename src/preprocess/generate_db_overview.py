#!/usr/bin/env python3
"""
Generate database overviews for database schemas using LLM processing.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from llm_processor import process_schemas_with_llm
from config import get_config, ensure_output_dirs

# Load configuration
config = get_config()
PATHS = config["paths"]
LLM_CONFIG = config["llm"]


def format_data_for_prompt(schema: Dict[str, Any]) -> Dict[str, str]:
    """
    Format the schema data for the database overview prompt.
    
    Args:
        schema: Database schema dictionary
        
    Returns:
        Dictionary with formatted data for prompt template variables
    """
    db_id = schema.get('db_id', 'unknown_db')
    table_names = schema.get('table_names', [])
    column_descs = schema.get('column_descriptions', [])

    database_schema = json.dumps({
        "db_id": db_id,
        "table_names": table_names
    }, ensure_ascii=False, indent=2)

    column_descriptions = json.dumps({
        "column_descriptions": column_descs
    }, ensure_ascii=False, indent=2)

    return {
        "DATABASE_SCHEMA": database_schema,
        "COLUMN_DESCRIPTIONS": column_descriptions
    }


def main(
    schema_path: Optional[Path] = None,
    prompt_path: Optional[Path] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> None:
    """
    Generate database overviews using the LLM processor.
    
    Args:
        schema_path: Path to the schema JSON file
        prompt_path: Path to the prompt template file
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
    """
    # Use default paths from config if not provided
    schema_path = schema_path or PATHS["schema"]
    prompt_path = prompt_path or PATHS["db_overview_prompt"]
    model_name = model_name or LLM_CONFIG["model"]
    temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]
    
    # Validate file existence
    for path, name in [
        (schema_path, "Schema"),
        (prompt_path, "Prompt template")
    ]:
        if not Path(path).exists():
            raise FileNotFoundError(f"{name} file not found: {path}")
    
    print(f"Generating database overviews with:")
    print(f"  - Schema: {schema_path}")
    print(f"  - Prompt: {prompt_path}")
    print(f"  - Model: {model_name} (temp={temperature})")
    
    try:
        process_schemas_with_llm(
            schema_path=schema_path,
            prompt_path=prompt_path,
            input_variables=["DATABASE_SCHEMA", "COLUMN_DESCRIPTIONS"],
            data_formatter_func=format_data_for_prompt,
            output_field_name="db_overview",
            output_key_in_result="db_overview",
            llm_model_name=model_name,
            temperature=temperature
        )
        print("Database overviews generation completed successfully.")
    except Exception as e:
        print(f"Error generating database overviews: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate database overviews for schemas")
    parser.add_argument("--schema", type=Path, help=f"Path to schema file (default: {PATHS['schema']})")
    parser.add_argument("--prompt", type=Path, help=f"Path to prompt template (default: {PATHS['db_overview_prompt']})")
    parser.add_argument("--model", type=str, help=f"LLM model name (default: {LLM_CONFIG['model']})")
    parser.add_argument("--temp", type=float, help=f"LLM temperature (default: {LLM_CONFIG['temperature']})")
    
    args = parser.parse_args()
    
    main(
        schema_path=args.schema,
        prompt_path=args.prompt,
        model_name=args.model,
        temperature=args.temp
    )