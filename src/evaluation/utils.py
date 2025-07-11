import json
import sqlparse 
from sqlparse.tokens import Punctuation
from nltk.util import ngrams
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import pairwise_distances
from scipy.stats import entropy
import numpy as np
import pandas as pd
import re
import csv


def extract_sql(filepath, as_json=False, encoding="utf-8"):
    """
    从以 <SQL>\t<dataset> 格式存储的文件中提取 SQL 查询语句。
    
    参数:
        filepath (str): 输入文件路径，例如 "dev.sql"
        as_json (bool): 如果为 True，返回 JSON 字符串；否则返回 Python 列表
        encoding (str): 文件编码（默认 utf-8）

    返回:
        list[str] | str: SQL 查询字符串的列表，或 JSON 格式字符串
    """
    queries = []
    with open(filepath, "r", encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sql_query = line.split("\t")[0]  # 提取 SQL 部分
            queries.append(sql_query)
    
    return json.dumps(queries, indent=4) if as_json else queries


# Calculate No.n-grams
def analyze_sql_patterns(sql_queries, n_gram_size, top_k=10):

    # 允许的关键词列表（注意保留单词和复合词） —— AS 和 ON 被排除
    ALLOWED_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "GROUP BY", "HAVING", "ORDER BY",
        "LIMIT", "OFFSET", "DISTINCT", "IN", "BETWEEN", "LIKE", 
        "INNER JOIN", "LEFT JOIN", "RIGHT JOIN",
        "IS NULL", "AND", "OR", "NOT", "EXISTS", "CASE"
    }

    # 复合关键词映射
    COMPOUND_KEYWORDS = {
        ("GROUP", "BY"): "GROUP BY",
        ("ORDER", "BY"): "ORDER BY",
        ("IS", "NULL"): "IS NULL",
        ("INNER", "JOIN"): "INNER JOIN", 
        ("LEFT", "JOIN"): "LEFT JOIN", 
        ("RIGHT", "JOIN"): "RIGHT JOIN"
    }

    # 1. Tokenizer
    def tokenize_sql_allowed_keywords(query):
        parsed = sqlparse.parse(query)[0]
        tokens = [str(t).strip().upper() for t in parsed.flatten() if not t.is_whitespace and t.ttype != Punctuation]
        
        # 合并复合关键词
        i = 0
        result = []
        while i < len(tokens):
            match_found = False
            for compound, label in COMPOUND_KEYWORDS.items():
                if tokens[i:i+len(compound)] == list(compound):
                    result.append(label)
                    i += len(compound)
                    match_found = True
                    break
            if not match_found:
                result.append(tokens[i])
                i += 1

        return [t for t in result if t in ALLOWED_KEYWORDS]

    # 2. 提取 n-grams
    def extract_ngrams(tokenized_queries, n):
        all_ngrams = []
        for tokens in tokenized_queries:
            grams = [' '.join(g) for g in ngrams(tokens, n)]
            all_ngrams.append(grams)
        return all_ngrams

    # Tokenize + n-gram
    tokenized_queries = [tokenize_sql_allowed_keywords(q) for q in sql_queries]
    query_ngrams = extract_ngrams(tokenized_queries, n=n_gram_size)

    # 向量化
    vectorizer = CountVectorizer(tokenizer=lambda x: x, lowercase=False)
    X = vectorizer.fit_transform(query_ngrams).toarray()

    # 熵计算
    ngram_freq = np.sum(X, axis=0)
    ngram_prob = ngram_freq / np.sum(ngram_freq)
    ngram_entropy = entropy(ngram_prob)

    # 平均 Jaccard 相似度
    jaccard_sim = 1 - pairwise_distances(X.astype(bool), metric='jaccard')
    avg_similarity = np.mean(jaccard_sim[np.triu_indices_from(jaccard_sim, k=1)])

    '''
    # 输出结果
    print(f"n-gram size: {n_gram_size}")
    print(f"Total unique n-grams: {len(vectorizer.get_feature_names_out())}")
    print(f"n-gram entropy: {ngram_entropy:.4f}")
    print(f"Average pairwise Jaccard similarity: {avg_similarity:.4f}")
    '''

    # Top n-grams
    ngram_names = vectorizer.get_feature_names_out()
    ngram_df = pd.DataFrame({'ngram': ngram_names, 'frequency': ngram_freq})
    # print("\nTop n-grams:")
    # print(ngram_df.sort_values('frequency', ascending=False).head(top_k))

    # 可返回数据框和向量矩阵供后续分析
    return {
        'total unique n-grams': len(vectorizer.get_feature_names_out()),
        'entropy': ngram_entropy,
        'jaccard_similarity': avg_similarity,        
        'top n-grams' : ngram_df.sort_values('frequency', ascending=False).head(top_k)
    }


# Calculate No.tokens(without punctuation), No.JOINS and No.keywords
def analyze_sqls_complexity(sql_list: list[str], csv_path: str):

    KEYWORDS = [
        "SELECT", "FROM", "INNER JOIN", "LEFT JOIN", "WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT",
        "OFFSET", "DISTINCT", "AS", "IN", "BETWEEN", "LIKE",
        "IS NULL", "AND", "OR", "NOT", "EXISTS", "CASE"
    ]

    COMPOUND_KEYWORDS = [
        "INNER JOIN",
        "LEFT JOIN",
        "RIGHT JOIN",
        "FULL JOIN",
        "GROUP BY",
        "ORDER BY",
        "IS NULL"
    ]

    JOIN_TYPES = ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"]

    def merge_compound_keywords(tokens, compound_keywords):
        merged_tokens = []
        i = 0
        while i < len(tokens):
            matched = False
            for compound in compound_keywords:
                parts = compound.split()
                length = len(parts)
                if i + length <= len(tokens) and tokens[i:i+length] == parts:
                    merged_tokens.append(compound)
                    i += length
                    matched = True
                    break
            if not matched:
                merged_tokens.append(tokens[i])
                i += 1
        return merged_tokens

    def count_keywords(tokens, keywords):
        counts = {kw: 0 for kw in keywords}
        for t in tokens:
            if t in counts:
                counts[t] += 1
        return counts

    def analyze_single_sql(sql: str):
        parsed = sqlparse.parse(sql)
        if not parsed:
            return {
                "tokens": 0,
                "join_count": 0,
                "keyword_counts": {kw: 0 for kw in KEYWORDS}
            }

        stmt = parsed[0]
        tokens = [
            token.value for token in stmt.flatten()
            if not token.is_whitespace and token.ttype != Punctuation
        ]

        # 这里假设 tokens 已经是大写，如果没大写，外部确保大写即可

        merged_tokens = merge_compound_keywords(tokens, COMPOUND_KEYWORDS)

        total_tokens = len(merged_tokens)
        keyword_counts = count_keywords(merged_tokens, KEYWORDS)

        join_count = sum(keyword_counts.get(jt, 0) for jt in JOIN_TYPES)
        total_keyword_count = sum(keyword_counts.values())

        return {
            "tokens": total_tokens,
            "join_count": join_count,
            "total_keyword_count": total_keyword_count,
            "keyword_counts": keyword_counts
        }

    # 分析每条 SQL
    results = []
    for idx, sql in enumerate(sql_list):
        result = analyze_single_sql(sql)
        results.append({
            "sql_index": idx,
            "tokens": result["tokens"],
            "join_count": result["join_count"],
            "total_keyword_count": result["total_keyword_count"],
            **{f"keyword:{kw}": result["keyword_counts"].get(kw, 0) for kw in KEYWORDS}
        })

    fieldnames = ["sql_index", "tokens", "join_count", "total_keyword_count"] + [f"keyword:{kw}" for kw in KEYWORDS]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
