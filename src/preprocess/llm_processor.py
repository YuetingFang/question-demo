import json
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Union

from tqdm import tqdm
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.cache import InMemoryCache
from langchain.globals import set_llm_cache
from dotenv import load_dotenv

from config import ENV_PATH

# Set up in-memory caching for LLM calls
set_llm_cache(InMemoryCache())

def setup_llm(model_name: str, temperature: float) -> ChatOpenAI:
    """
    Set up and initialize the LLM with proper environment variables.
    """
    load_dotenv(ENV_PATH)
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY not found in environment variables")
    return ChatOpenAI(temperature=temperature, model_name=model_name)

def load_json_file(file_path: Union[str, Path]) -> Any:
    """
    Load and parse a JSON file.
    """
    file_path = Path(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file {file_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

def load_prompt_template(prompt_path: Union[str, Path]) -> str:
    """
    Load a prompt template from a file.
    """
    prompt_path = Path(prompt_path)
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template file not found: {prompt_path}")

def parse_llm_response(content: str, db_id: str = "") -> Dict[str, Any]:
    """
    Parse the LLM response content and extract JSON data.
    """
    patterns = [
        r'```json\s*([\s\S]+?)\s*```',
        r'```\s*([\s\S]+?)\s*```',
        r'\{\{([\s\S]+?)\}\}',
        r'\{([\s\S]+?)\}'
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                try:
                    return json.loads('{' + json_str + '}')
                except json.JSONDecodeError:
                    continue
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON from LLM response for db '{db_id}'"
        tqdm.write(f"Error: {error_msg}: {str(e)}")
        tqdm.write(f"Response content (truncated): {content[:200]}...")
        raise ValueError(error_msg)

def process_schemas_with_llm(
    schema_path: Union[str, Path],
    prompt_path: Union[str, Path],
    input_variables: List[str],
    data_formatter_func: Callable[[Dict[str, Any]], Dict[str, str]],
    output_field_name: str,
    output_key_in_result: str,
    llm_model_name: str = "gpt-4o",
    temperature: float = 0.1,
) -> None:
    """
    Generic function to process database schemas with an LLM.
    """
    schema_path = Path(schema_path)
    prompt_path = Path(prompt_path)
    llm = setup_llm(llm_model_name, temperature)
    all_schemas = load_json_file(schema_path)
    prompt_template = load_prompt_template(prompt_path)
    prompt = PromptTemplate(template=prompt_template, input_variables=input_variables)
    llm_chain = prompt | llm

    processed_count = 0
    error_count = 0

    for schema in tqdm(all_schemas, desc=f"Processing {output_field_name}"):
        db_id = schema.get('db_id', 'unknown')
        if output_field_name in schema and schema[output_field_name]:
            processed_count += 1
            continue
        try:
            prompt_data = data_formatter_func(schema)
            response = llm_chain.invoke(prompt_data)
            result = parse_llm_response(response.content, db_id)
            if output_key_in_result in result:
                schema[output_field_name] = result[output_key_in_result]
                processed_count += 1
            else:
                tqdm.write(f"Warning: '{output_key_in_result}' not in result for db '{db_id}'")
                error_count += 1
        except Exception as e:
            tqdm.write(f"Error processing db '{db_id}': {str(e)}")
            error_count += 1

    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(all_schemas, f, ensure_ascii=False, indent=2)

    print(f"\nProcessing complete. Results saved to {schema_path}")
    print(f"Successfully processed {processed_count}/{len(all_schemas)} schemas.")
    if error_count > 0:
        print(f"Encountered errors with {error_count} schemas.")

def process_examples_with_llm(
    examples_path: Union[str, Path],
    prompt_path: Union[str, Path],
    output_path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None,
    input_variables: List[str] = ["DATABASE_SCHEMA"],
    output_key_map: Dict[str, str] = {},
    llm_model_name: str = "gpt-4o",
    temperature: float = 0.1,
    max_examples: Optional[int] = None,
) -> None:
    """
    Process examples with an LLM using a prompt template.
    """
    examples_path = Path(examples_path)
    prompt_path = Path(prompt_path)
    output_path = Path(output_path)
    if schema_path:
        schema_path = Path(schema_path)
    
    llm = setup_llm(llm_model_name, temperature)
    examples = load_json_file(examples_path)
    
    db_id_to_schema = {}
    if schema_path:
        schemas = load_json_file(schema_path)
        db_id_to_schema = {s.get('db_id'): s for s in schemas if s.get('db_id')}
    
    prompt_template = load_prompt_template(prompt_path)
    prompt = PromptTemplate(template=prompt_template, input_variables=input_variables)
    llm_chain = prompt | llm

    if max_examples is not None and max_examples > 0:
        examples = examples[:max_examples]
    
    results = []
    error_count = 0
    success_count = 0

    for example in tqdm(examples, desc="Processing examples"):
        db_id = example.get('db_id', '')
        try:
            schema_data = {}
            if db_id and db_id in db_id_to_schema:
                schema = db_id_to_schema[db_id]
                filtered_schema = {
                    "db_id": db_id,
                    "column_names_original": schema.get("column_names_original", []),
                    "table_names_original": schema.get("table_names_original", [])
                }
                schema_data = json.dumps(filtered_schema, ensure_ascii=False, indent=2)
            
            prompt_data = {
                "DATABASE_SCHEMA": schema_data,
                "COLUMN_DESCRIPTIONS": json.dumps(example.get("column_descriptions", {}), ensure_ascii=False),
                "NLQ_SQL_PAIR": json.dumps(example, ensure_ascii=False)
            }
            
            prompt_data = {k: v for k, v in prompt_data.items() if k in input_variables}
            
            response = llm_chain.invoke(prompt_data)
            llm_output = parse_llm_response(response.content, db_id)
            
            updated_example = example.copy()
            for output_key, result_key in output_key_map.items():
                if result_key in llm_output:
                    updated_example[output_key] = llm_output[result_key]
            
            results.append(updated_example)
            success_count += 1
            
        except Exception as e:
            tqdm.write(f"Error processing example for db '{db_id}': {str(e)}")
            results.append(example)
            error_count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nProcessing complete. Results saved to {output_path}")
    print(f"Successfully processed: {success_count}/{len(examples)} examples")
    if error_count > 0:
        print(f"Encountered errors with {error_count} examples")