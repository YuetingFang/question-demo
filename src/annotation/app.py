from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import json
import random
import sqlite3
import csv
import uuid
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_BASE_PATH = BASE_DIR / '..' / '..' / 'data' / 'dev_databases'
PREPROCESS_PATH = BASE_DIR / '..' / '..' / 'results' / 'preprocess' / 'preprocess_dev_tables.json'
DICT_DESC_PATH = BASE_DIR / '..' / '..' / 'results' / 'preprocess' / 'dictionary_column_descriptions.json'
TASK_DESC_PATH = BASE_DIR / '..' / '..' / 'results' / 'preprocess' / 'task_descriptions.json'


# 确保静态文件路径正确
app = Flask(__name__, static_folder='build', static_url_path='')
CORS(app)  # Enable CORS for all routes


# 注意：Flask静态文件处理优化
@app.route('/')
def index():
    """直接处理根路径，返回 React 页面"""
    return send_from_directory(app.static_folder, 'index.html')

# 明确处理 React 路由路径
@app.route('/guidelines')
@app.route('/examples')
@app.route('/database-task-info')
def handle_react_routes():
    """所有 React 路由返回首页，由 React Router 处理"""
    return send_from_directory(app.static_folder, 'index.html')

# 提供任务描述数据      
@app.route('/api/task-descriptions')
def get_task_descriptions():
    """
    获取任务描述数据 (从task_descriptions.json文件)
    """
    try:
        dc_task_path = TASK_DESC_PATH
        print(f"Loading DC tasks from: {dc_task_path}")
        with open(dc_task_path, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        return jsonify(tasks)
    except Exception as e:
        print(f"Error loading task descriptions: {e}")
        return jsonify([]), 500

# 处理静态文件
@app.route('/<path:path>')
def serve_static(path):
    """处理其他所有路径请求"""
    # 静态文件路径处理
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    
    # 所有其他路径都返回首页，由 React Router 处理
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/dynamic-tables', methods=['GET'])
def get_dynamic_tables():
    try:
        if not os.path.exists(DB_BASE_PATH):
            return jsonify({'error': f"Database directory not found"}), 500
        # Get db_id from request parameters, fall back to default if not provided
        requested_db_id = request.args.get('db_id')
        
        # Get all available database IDs for validation
        db_ids = [name for name in os.listdir(DB_BASE_PATH) if os.path.isdir(os.path.join(DB_BASE_PATH, name))]
        
        # Use requested db_id if valid, otherwise use default
        if requested_db_id and requested_db_id in db_ids:
            selected_db_id = requested_db_id
        else:
            selected_db_id = 'california_schools'  # Default database ID

        if not os.path.exists(PREPROCESS_PATH):
            return jsonify({'error': f"Preprocess file not found"}), 500

        with open(PREPROCESS_PATH, 'r') as f:
            all_preprocess_data = json.load(f)
        db_data = next((item for item in all_preprocess_data if item.get('db_id') == selected_db_id), None)
        if not db_data:
            return jsonify({'error': f'Data for {selected_db_id} not found'}), 404

        table_count = len(db_data.get('table_names_original', []))
        tables_to_display = db_data.get('table_names_original', [])[:3] if table_count >= 4 else db_data.get('table_names_original', [])

        # 加载字典描述
        dict_descriptions = {}
        if os.path.exists(DICT_DESC_PATH):
            with open(DICT_DESC_PATH, 'r') as f:
                dict_descriptions_data = json.load(f)
            db_entry = next((item for item in dict_descriptions_data if item.get('db_id') == selected_db_id), None)
            if db_entry:
                for table_name in db_data.get('table_names_original', []):
                    if table_name in db_entry:
                        dict_descriptions[table_name] = {col[0]: col[1] for col in db_entry[table_name] if isinstance(col, list) and len(col) >= 2}

        column_names_original = db_data.get('column_names_original', [])
        table_column_map = {}
        for col_idx, col_name in column_names_original:
            table_name = db_data['table_names_original'][col_idx]
            table_column_map.setdefault(table_name, []).append(col_name)

        column_name_mapping = {table: table_column_map.get(table, []) for table in tables_to_display}
        column_desc_mapping = {
            table: [
                {'name': col, 'description': dict_descriptions.get(table, {}).get(col, '')}
                for col in table_column_map.get(table, [])
            ] for table in tables_to_display
        }

        result = {
            'db_id': selected_db_id,
            'db_overview': db_data.get('db_overview', ''),
            'table_count': table_count,
            'table_names': db_data.get('table_names_original', []),
            'tables_to_display': tables_to_display,
            'column_names': column_name_mapping,
            'column_descriptions': column_desc_mapping,
            'table_data': {},
            'task': {
                'task_id': 'task1',
                'task_description': f'Write a query to answer a question about the {selected_db_id} database.',
                'difficulty': 'Medium'
            }
        }

        db_path = os.path.join(DB_BASE_PATH, selected_db_id, f'{selected_db_id}.sqlite')
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                for table_name in tables_to_display:
                    try:
                        safe_table_name = table_name.replace('"', '""')
                        cursor.execute(f'SELECT * FROM "{safe_table_name}" ORDER BY RANDOM() LIMIT 10')
                        rows = cursor.fetchall()
                        result['table_data'][table_name] = [dict(row) for row in rows]
                    except sqlite3.Error:
                        result['table_data'][table_name] = []
                conn.close()
            except Exception:
                for table_name in tables_to_display:
                    result['table_data'][table_name] = []
        else:
            for table_name in tables_to_display:
                result['table_data'][table_name] = []

        return jsonify(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# API endpoint to get data for a specific table
@app.route('/api/table-data', methods=['GET'])
def get_table_data():
    try:
        # Get the table name and database ID from the query parameters
        # Support both 'table_name' and 'tableName' for backwards compatibility
        table_name = request.args.get('table_name') or request.args.get('tableName')
        db_id = request.args.get('db_id')
        
        if not table_name:
            return jsonify({'error': 'Table name is required'}), 400
            
        # Use default db_id if not provided
        if not db_id:
            db_id = 'debit_card_specializing'  # Default database ID
            
        # Get all database IDs (folder names) for validation
        db_ids = [name for name in os.listdir(DB_BASE_PATH) if os.path.isdir(os.path.join(DB_BASE_PATH, name))]
        
        if not db_ids:
            return jsonify({'error': 'No databases found'}), 404
            
        # Ensure the requested db_id exists
        if db_id not in db_ids:
            return jsonify({'error': f'Database {db_id} not found'}), 404
            
        # Use the requested database ID
        selected_db_id = db_id
        
        # Load preprocessing data
        with open(PREPROCESS_PATH, 'r') as f:
            all_preprocess_data = json.load(f)
        
        # Extract data for selected DB ID
        db_data = next((item for item in all_preprocess_data if item.get('db_id') == selected_db_id), None)
        if not db_data:
            return jsonify({'error': f'Data for {selected_db_id} not found'}), 404
        
        # Result object to return - use camelCase keys to match frontend expectations
        result = {
            'tableName': table_name,
            'columns': [],     # Frontend expects 'columns' instead of 'column_names'
            'columnDescriptions': [], # Frontend expects 'columnDescriptions' instead of 'column_descriptions'
            'data': []        # Frontend expects 'data' instead of 'table_data'
        }
        
        # Get column names from the preprocess file
        column_names_original = db_data.get('column_names_original', [])
        table_names_original = db_data.get('table_names_original', [])
        
        # Find the table index
        if table_name not in table_names_original:
            return jsonify({'error': f'Table {table_name} not found'}), 404
        
        table_idx = table_names_original.index(table_name)
        
        # Load column descriptions from dictionary file
        dict_descriptions = {}
        
        if os.path.exists(DICT_DESC_PATH):
            try:
                with open(DICT_DESC_PATH, 'r') as f:
                    dict_descriptions_data = json.load(f)
                    
                    # Find the entry for this db_id
                    db_entry = next((item for item in dict_descriptions_data if item.get('db_id') == selected_db_id), None)
                    
                    if db_entry and table_name in db_entry:
                        # Initialize the table in our dictionary
                        dict_descriptions[table_name] = {}
                        
                        # Process column-description pairs for this table
                        column_pairs = db_entry[table_name]
                        if isinstance(column_pairs, list):
                            for col_pair in column_pairs:
                                if isinstance(col_pair, list) and len(col_pair) >= 2:
                                    column_name = col_pair[0]
                                    column_description = col_pair[1]
                                    dict_descriptions[table_name][column_name] = column_description
            except Exception as e:
                print(f"Error loading dictionary descriptions for table {table_name}: {e}")
        
        # Get column names for this table
        table_columns = [col_name for (col_idx, col_name) in column_names_original if col_idx == table_idx]
        result['columns'] = table_columns
        
        # Get column descriptions if available
        column_descriptions = []
        if table_name in dict_descriptions:
            table_column_descriptions = dict_descriptions[table_name]
            for col_name in table_columns:
                description = table_column_descriptions.get(col_name, '')
                column_descriptions.append({
                    'name': col_name,
                    'description': description
                })
        else:
            # Fallback to empty descriptions
            column_descriptions = [{'name': col, 'description': ''} for col in table_columns]
        
        result['columnDescriptions'] = column_descriptions
        
        # Query SQLite database for table data
        db_path = os.path.join(DB_BASE_PATH, selected_db_id, f'{selected_db_id}.sqlite')
        
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Make sure the SQL is safe by properly quoting table name
                safe_table_name = table_name.replace('"', '""')
                cursor.execute(f'SELECT * FROM "{safe_table_name}" ORDER BY RANDOM() LIMIT 10')
                rows = cursor.fetchall()
                result['data'] = [dict(row) for row in rows]
            except sqlite3.Error as e:
                print(f"Error querying table {table_name}: {e}")
                return jsonify({'error': f'Error querying table {table_name}: {str(e)}'}), 500
            finally:
                if conn:
                    conn.close()
        else:
            return jsonify({'error': f'Database file not found for {selected_db_id}'}), 404
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Handle all client-side routes
@app.route('/examples/<int:index>')
def serve_examples_with_index(index):
    # This route specifically handles the examples routes with numeric IDs
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/introduction')
@app.route('/guidelines')
@app.route('/examples')
@app.route('/thankyou')
def serve_react_routes_explicit():
    # These routes are explicitly defined to match React Router routes
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all route to serve React app for any other non-API routes
@app.route('/<path:path>')
def serve_react_routes(path):
    # Don't handle API routes with this catch-all
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
        
    # Try to serve static files first
    static_path = os.path.join(app.static_folder, path)
    if os.path.isfile(static_path):
        return send_from_directory(app.static_folder, path)
    
    # For all other paths, serve the React app
    return send_from_directory(app.static_folder, 'index.html')

# API endpoint to save user annotations to CSV
@app.route('/api/save-annotation', methods=['POST'])
def save_annotation():
    try:
        data = request.json
        
        # Extract data from request
        user_id = data.get('user_id')
        inputs = data.get('inputs', [])
        question_id = data.get('question_id')
        db_id = data.get('db_id')
        task_description = data.get('task_description')
        
        # Validate required fields
        if not user_id or not inputs or not question_id or not db_id or not task_description:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create directory for annotations if it doesn't exist
        annotations_dir = BASE_DIR / '..' / '..' / 'results' / 'annotations'
        os.makedirs(annotations_dir, exist_ok=True)
        
        # CSV file path
        csv_path = annotations_dir / 'user_annotations.csv'
        file_exists = os.path.isfile(csv_path)
        
        # Write to CSV file
        with open(csv_path, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow(['ID', 'Input', 'question_id', 'db_id', 'task_description', 'timestamp'])
            
            # Write each input as a separate row
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for input_text in inputs:
                if input_text.strip():  # Only write non-empty inputs
                    writer.writerow([user_id, input_text, question_id, db_id, task_description, timestamp])
        
        return jsonify({'success': True, 'message': 'Annotation saved successfully'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
