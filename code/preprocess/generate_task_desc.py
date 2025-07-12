#!/usr/bin/env python3
"""
Generate task descriptions for SQL queries using LLM processing.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from llm_processor import process_examples_with_llm
from config import get_config, ensure_output_dirs

# Load configuration
config = get_config()
PATHS = config["paths"]
LLM_CONFIG = config["llm"]

def format_data_for_prompt(example: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, str]:
    """
    Format the example and schema data for the task description prompt.
    
    Args:
        example: Example dictionary containing query and other fields
        schema: Database schema dictionary
        
    Returns:
        Dictionary with formatted data for prompt template variables
    """
    query = example.get('query', '')
    db_id = example.get('db_id', '')
    
    # Format database schema as JSON string
    database_schema = json.dumps({
        "db_id": db_id,
        "table_names": schema.get('table_names', []),
        "column_names": schema.get('column_names', []),
        "column_types": schema.get('column_types', []),
        "foreign_keys": schema.get('foreign_keys', []),
        "primary_keys": schema.get('primary_keys', [])
    }, ensure_ascii=False, indent=2)
    
    # Include all required variables for the prompt template
    return {
        "QUERY": query,
        "DATABASE_SCHEMA": database_schema,
        "COLUMN_DESCRIPTIONS": json.dumps(example.get("column_descriptions", {}), ensure_ascii=False),
        "NLQ_SQL_PAIR": json.dumps({
            "question": example.get("question", ""),
            "query": query
        }, ensure_ascii=False)
    }


def main(
    examples_path: Optional[Path] = None,
    schema_path: Optional[Path] = None,
    prompt_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_examples: Optional[int] = None,
) -> None:
    """
    Generate task descriptions for SQL queries using LLM processing.
    
    Args:
        examples_path: Path to the examples JSON file
        schema_path: Path to the schema JSON file
        prompt_path: Path to the prompt template file
        output_path: Path to save the output JSON file
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
        max_examples: Maximum number of examples to process
    """
    # Use default paths from config if not provided
    examples_path = examples_path or PATHS["examples"]
    schema_path = schema_path or PATHS["schema"]
    prompt_path = prompt_path or PATHS["task_desc_prompt"]
    output_path = output_path or PATHS["task_desc_output"]
    model_name = model_name or LLM_CONFIG["model"]
    temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]
    
    # Validate file existence
    for path, name in [
        (examples_path, "Examples"),
        (schema_path, "Schema"),
        (prompt_path, "Prompt template")
    ]:
        if not Path(path).exists():
            raise FileNotFoundError(f"{name} file not found: {path}")
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    print(f"Generating task descriptions with:")
    print(f"  - Examples: {examples_path}")
    print(f"  - Schema: {schema_path}")
    print(f"  - Prompt: {prompt_path}")
    print(f"  - Output: {output_path}")
    print(f"  - Model: {model_name} (temp={temperature})")
    if max_examples:
        print(f"  - Max examples: {max_examples}")
    
    # Define output key mapping
    output_key_map = {
        "reasoning": "reasoning",
        "task_description": "task_description"
    }
    
    # Process examples with LLM
    try:
        process_examples_with_llm(
            examples_path=examples_path,
            schema_path=schema_path,
            prompt_path=prompt_path,
            output_path=output_path,
            input_variables=["DATABASE_SCHEMA", "COLUMN_DESCRIPTIONS", "NLQ_SQL_PAIR"],
            output_key_map=output_key_map,
            llm_model_name=model_name,
            temperature=temperature,
            max_examples=max_examples
        )
        print("Task description generation completed successfully.")
    except Exception as e:
        print(f"An error occurred during task description generation: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate task descriptions for SQL queries")
    parser.add_argument("--examples", type=Path, help=f"Path to examples file (default: {PATHS['examples']})")
    parser.add_argument("--schema", type=Path, help=f"Path to schema file (default: {PATHS['schema']})")
    parser.add_argument("--prompt", type=Path, help=f"Path to prompt template (default: {PATHS['task_desc_prompt']})")
    parser.add_argument("--output", type=Path, help=f"Path to output file (default: {PATHS['task_desc_output']})")
    parser.add_argument("--model", type=str, help=f"LLM model name (default: {LLM_CONFIG['model']})")
    parser.add_argument("--temp", type=float, help=f"LLM temperature (default: {LLM_CONFIG['temperature']})")
    parser.add_argument("--max", type=int, help="Maximum number of examples to process")
    
    args = parser.parse_args()
    
    main(
        examples_path=args.examples,
        schema_path=args.schema,
        prompt_path=args.prompt,
        output_path=args.output,
        model_name=args.model,
        temperature=args.temp,
        max_examples=args.max
    )