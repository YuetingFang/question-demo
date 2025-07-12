### src/preprocess 处理数据，生成 task description

python src/preprocess/run_pipeline.py --steps all  运行所有步骤

python src/preprocess/run_pipeline.py --steps column 

python src/preprocess/run_pipeline.py --steps db 

python src/preprocess/run_pipeline.py --steps task 


# 后端依赖
Flask==2.3.3
Flask-Cors==4.0.0
Werkzeug==2.3.7
gunicorn
python-dotenv

# 数据处理依赖
numpy>=1.20.0
pandas>=1.3.0

# 预处理模块依赖
tqdm>=4.62.0
langchain>=0.0.267
langchain-openai>=0.0.2
langchain-community>=0.0.1
python-dotenv>=0.19.0

