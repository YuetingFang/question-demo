#!/usr/bin/env python3
"""
Generate column descriptions for database schemas using LLM processing.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import os
from llm_processor import process_schemas_with_llm
from config import get_config

# Load configuration
config = get_config()
PATHS = config["paths"]
LLM_CONFIG = config["llm"]


def format_data_for_prompt(schema: Dict[str, Any]) -> Dict[str, str]:
    """
    Format the schema data for the column description prompt.
    
    Args:
        schema: Database schema dictionary
        
    Returns:
        Dictionary with formatted data for prompt template variables
    """
    db_id = schema.get('db_id', 'unknown_db')
    table_names = schema.get('table_names', [])
    column_names = schema.get('column_names', [])
    column_descs = schema.get('column_descriptions_original', [])

    database_schema = json.dumps({
        "db_id": db_id,
        "table_names": table_names,
        "column_names": column_names
    }, ensure_ascii=False, indent=2)

    original_column_descriptions = json.dumps({
        "column_descriptions_original": column_descs
    }, ensure_ascii=False, indent=2)

    return {
        "DATABASE_SCHEMA": database_schema,
        "ORIGINAL_COLUMN_DESCRIPTIONS": original_column_descriptions
    }


def transform_and_save(
    processed_schema_path: Path,
    output_path: Path
) -> None:
    """
    Transform the processed schema and save it to the desired format.
    """
    with open(processed_schema_path, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)

    transformed_data = []
    for schema in processed_data:
        db_id = schema.get('db_id')
        if not db_id:
            continue

        column_names = schema.get('column_names_original', [])
        table_names = schema.get('table_names_original', [])
        descriptions = schema.get('column_descriptions', [])

        if len(column_names) != len(descriptions):
            print(f"Warning: Mismatch in column count for db '{db_id}'. Skipping.")
            continue

        db_entry = {"db_id": db_id}
        table_dict = {}

        for i, (col_id, col_name) in enumerate(column_names):
            if col_id == -1:  # Skip '*' columns
                continue

            table_name = table_names[col_id]
            if table_name not in table_dict:
                table_dict[table_name] = []

            description_item = descriptions[i]
            final_description = description_item
            # Handle cases where the description is a list [index, text]
            if isinstance(description_item, list) and len(description_item) > 1:
                final_description = description_item[1]

            table_dict[table_name].append([col_name, final_description])

        db_entry.update(table_dict)
        transformed_data.append(db_entry)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transformed_data, f, ensure_ascii=False, indent=2)
    
    print(f"Transformed column descriptions saved to {output_path}")

def main(
    schema_path: Optional[Path] = None,
    prompt_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> None:
    """
    Generate refined column descriptions using the LLM processor.
    
    Args:
        schema_path: Path to the schema JSON file
        prompt_path: Path to the prompt template file
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
    """
    # Use default paths from config if not provided
    schema_path = schema_path or PATHS["schema"]
    prompt_path = prompt_path or PATHS["column_desc_prompt"]
    model_name = model_name or LLM_CONFIG["model"]
    temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]
    output_path = output_path or PATHS["column_desc_output"]
    
    # Validate file existence
    for path, name in [
        (schema_path, "Schema"),
        (prompt_path, "Prompt template")
    ]:
        if not Path(path).exists():
            raise FileNotFoundError(f"{name} file not found: {path}")
    
    print(f"Generating column descriptions with:")
    print(f"  - Schema: {schema_path}")
    print(f"  - Prompt: {prompt_path}")
    print(f"  - Model: {model_name} (temp={temperature})")
    
    try:
        process_schemas_with_llm(
            schema_path=schema_path,
            prompt_path=prompt_path,
            input_variables=["DATABASE_SCHEMA", "ORIGINAL_COLUMN_DESCRIPTIONS"],
            data_formatter_func=format_data_for_prompt,
            output_field_name="column_descriptions",
            output_key_in_result="column_descriptions",
            llm_model_name=model_name,
            temperature=temperature
        )
        print("Column descriptions generation completed successfully.")
        transform_and_save(schema_path, output_path)
    except Exception as e:
        print(f"Error generating column descriptions: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate column descriptions for database schemas")
    parser.add_argument("--schema", type=Path, help=f"Path to schema file (default: {PATHS['schema']})")
    parser.add_argument("--prompt", type=Path, help=f"Path to prompt template (default: {PATHS['column_desc_prompt']})")
    parser.add_argument("--output", type=Path, help=f"Output file path for transformed data (default: {PATHS['column_desc_output']})")
    parser.add_argument("--model", type=str, help=f"LLM model name (default: {LLM_CONFIG['model']})")
    parser.add_argument("--temp", type=float, help=f"LLM temperature (default: {LLM_CONFIG['temperature']})")
    
    args = parser.parse_args()
    
    main(
        schema_path=args.schema,
        prompt_path=args.prompt,
        output_path=args.output,
        model_name=args.model,
        temperature=args.temp
    )