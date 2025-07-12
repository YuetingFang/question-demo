#!/usr/bin/env python3
"""
SQL Task Description Generation Pipeline
This script provides a complete pipeline to run all processing steps in order:
1. Generate column descriptions
2. Generate database overviews
3. Generate task descriptions

You can configure which steps to run, number of examples, and other parameters via command line arguments.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

# Import configuration module
from config import get_config, ensure_output_dirs

# Setup logging
logger = logging.getLogger('sql_pipeline')


class TqdmLoggingHandler(logging.Handler):
    """A logging handler that uses tqdm.write() to avoid interfering with progress bars."""
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg, file=sys.stdout)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

def setup_environment():
    """Setup environment and directories"""
    logger.info("Setting up environment...")
    config = get_config()
    ensure_output_dirs()
    return config

def run_column_descriptions(config, args):
    """Run column description generation"""
    logger.info("Starting column description generation...")
    from generate_column_desc import main as column_desc_main
    
    try:
        column_desc_main(
            schema_path=args.schema_path,
            prompt_path=args.column_prompt,
            model_name=args.model,
            temperature=args.temp
        )
        logger.info("Column description generation completed")
        return True
    except Exception as e:
        logger.error(f"Column description generation failed: {e}")
        if args.stop_on_error:
            raise
        return False

def run_db_overviews(config, args):
    """Run database overview generation"""
    logger.info("Starting database overview generation...")
    from generate_db_overview import main as db_overview_main
    
    try:
        db_overview_main(
            schema_path=args.schema_path,
            prompt_path=args.db_prompt,
            model_name=args.model,
            temperature=args.temp
        )
        logger.info("Database overview generation completed")
        return True
    except Exception as e:
        logger.error(f"Database overview generation failed: {e}")
        if args.stop_on_error:
            raise
        return False

def run_task_descriptions(config, args):
    """Run task description generation"""
    logger.info("Starting task description generation...")
    from generate_task_desc import main as task_desc_main
    
    try:
        task_desc_main(
            examples_path=args.examples_path,
            schema_path=args.schema_path,
            prompt_path=args.task_prompt,
            output_path=args.output_path,
            model_name=args.model,
            temperature=args.temp,
            max_examples=args.max_examples
        )
        logger.info("Task description generation completed")
        return True
    except Exception as e:
        logger.error(f"Task description generation failed: {e}")
        if args.stop_on_error:
            raise
        return False

def run_collect_description(config, args):
    """Run the initial data collection and refinement."""
    logger.info("Starting initial data collection (collect_description.py)...")
    from collect_description import main as collect_desc_main
    
    try:
        collect_desc_main()
        logger.info("Initial data collection completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Initial data collection failed: {e}")
        if args.stop_on_error:
            raise
        return False

def run_pipeline(args):
    """Run the complete pipeline"""
    start_time = time.time()
    logger.info("Starting SQL task description generation pipeline...")
    
    # Setup environment
    config = setup_environment()

    # Check if the initial refined schema file exists
    refined_schema_path = config["paths"]["schema"]
    if not refined_schema_path.exists():
        logger.warning(f"Refined schema file not found at '{refined_schema_path}'.")
        logger.info("Running initial data collection step...")
        
        success = run_collect_description(config, args)
        if not success:
            logger.critical("Initial data collection failed. Pipeline cannot continue.")
            return False
        logger.info("Initial data collection successful. Proceeding with the main pipeline.")
    else:
        logger.info(f"Found existing refined schema file at '{refined_schema_path}'. Skipping collection step.")
    
    # Determine which steps to run
    logger.info(f"Executing pipeline steps: {args.steps}")
    steps_to_run = args.steps
    if "all" in steps_to_run:
        steps_to_run = ["column", "db", "task"]
    
    # Run steps in order
    results = {}
    
    if "column" in steps_to_run:
        results["column"] = run_column_descriptions(config, args)
    
    if "db" in steps_to_run and (results.get("column", True) or not args.sequential):
        results["db"] = run_db_overviews(config, args)
    
    if "task" in steps_to_run and ((results.get("db", True) and results.get("column", True)) or not args.sequential):
        results["task"] = run_task_descriptions(config, args)
    
    # Report results
    elapsed_time = time.time() - start_time
    logger.info(f"Pipeline execution completed in {elapsed_time:.2f} seconds")
    
    for step, success in results.items():
        status = "Succeeded" if success else "Failed"
        logger.info(f"Step '{step}': {status}")
    
    return all(results.values())

def main():
    """Main function to parse command line arguments and run the pipeline"""
    config = get_config()
    paths = config["paths"]
    llm_config = config["llm"]
    
    parser = argparse.ArgumentParser(description="SQL Task Description Generation Pipeline")
    
    # Step selection
    parser.add_argument("--steps", type=str, nargs="+", 
                        choices=["column", "db", "task", "all"], default=["all"],
                        help="Steps to run")
    
    # File paths
    parser.add_argument("--schema-path", type=Path, default=paths["schema"],
                        help=f"Path to schema file (default: {paths['schema']})")
    parser.add_argument("--examples-path", type=Path, default=paths["examples"],
                        help=f"Path to examples file (default: {paths['examples']})")
    parser.add_argument("--output-path", type=Path, default=paths["task_desc_output"],
                        help=f"Output file path (default: {paths['task_desc_output']})")
    
    # Prompt templates
    parser.add_argument("--column-prompt", type=Path, default=paths["column_desc_prompt"],
                        help=f"Column description prompt template (default: {paths['column_desc_prompt']})")
    parser.add_argument("--db-prompt", type=Path, default=paths["db_overview_prompt"],
                        help=f"Database overview prompt template (default: {paths['db_overview_prompt']})")
    parser.add_argument("--task-prompt", type=Path, default=paths["task_desc_prompt"],
                        help=f"Task description prompt template (default: {paths['task_desc_prompt']})")
    
    # LLM parameters
    parser.add_argument("--model", type=str, default=llm_config["model"],
                        help=f"LLM model name (default: {llm_config['model']})")
    parser.add_argument("--temp", type=float, default=llm_config["temperature"],
                        help=f"LLM temperature (default: {llm_config['temperature']})")
    
    # Other options
    parser.add_argument("--max-examples", type=int, default=None,
                        help="Maximum number of examples to process (default: all)")
    parser.add_argument("--sequential", action="store_true", default=True,
                        help="Run steps sequentially, stopping if a step fails (default: True)")
    parser.add_argument("--stop-on-error", action="store_true", default=False,
                        help="Stop execution on error (default: False)")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("--verbose", action="store_true",
                                 help="Show verbose (DEBUG level) output.")
    verbosity_group.add_argument("--quiet", action="store_true",
                                 help="Show only WARNING and ERROR messages on console.")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = TqdmLoggingHandler()
    if args.quiet:
        console_handler.setLevel(logging.WARNING)
    else:
        console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler
    log_dir = config['paths']['log_dir']
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f'pipeline_{timestamp}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)  # Always log INFO and above to file
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Run the pipeline
    success = run_pipeline(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()