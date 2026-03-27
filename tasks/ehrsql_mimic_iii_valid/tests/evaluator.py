'''Official evaluation script for EHRSQL - adapted for Harbor meta-task evaluation

Original: https://github.com/glee4810/EHRSQL/blob/main/evaluate.py
Harbor adaptation: Minimal changes to fit Harbor's submission/answer key format
'''

import json
import re
import sqlite3
import numpy as np
import sys
import multiprocessing as mp
from pathlib import Path
from typing import Any
from func_timeout import func_timeout, FunctionTimedOut


# Vital sign normal ranges from EHRSQL benchmark
VITAL_RANGES = {
    'temperature': (35.5, 38.1),
    'sao2': (95.0, 100.0),
    'heart rate': (60.0, 100.0),
    'respiration': (12.0, 18.0),
    'systolic bp': (90.0, 120.0),
    'diastolic bp': (60.0, 90.0),
    'mean bp': (60.0, 110.0)
}

DEFAULT_CURRENT_TIME = '2105-12-31 23:59:00'


def post_process_sql(query, current_time=DEFAULT_CURRENT_TIME, precomputed_dict=None):
    """Post-process SQL query: replace placeholders and normalize syntax.

    Directly from original EHRSQL evaluate.py - no changes.
    """
    if precomputed_dict is None:
        precomputed_dict = VITAL_RANGES

    query = query.lower()
    if "current_time" in query:
        query = query.replace("current_time", f"'{current_time}'")
    if re.search('[ \n]+([a-zA-Z0-9_]+_lower)', query) and re.search('[ \n]+([a-zA-Z0-9_]+_upper)', query):
        vital_lower_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_lower)', query)[0]
        vital_upper_expr = re.findall('[ \n]+([a-zA-Z0-9_]+_upper)', query)[0]
        vital_name_list = list(set(re.findall('([a-zA-Z0-9_]+)_lower', vital_lower_expr) + re.findall('([a-zA-Z0-9_]+)_upper', vital_upper_expr)))
        if len(vital_name_list) == 1:
            processed_vital_name = vital_name_list[0].replace('_', ' ')
            if processed_vital_name in precomputed_dict:
                vital_range = precomputed_dict[processed_vital_name]
                query = query.replace(vital_lower_expr, f"{vital_range[0]}").replace(vital_upper_expr, f"{vital_range[1]}")
    query = query.replace("''", "'").replace('< =', '<=')
    query = query.replace("%y", "%Y").replace('%j', '%J')
    query = query.replace("'now'", f"'{current_time}'")
    return query


def process_answer(ans):
    """Process SQL result into comparable form.

    Directly from original EHRSQL evaluate.py - no changes.
    """
    return str(sorted([str(ret) for ret in ans[:100]]))  # check only up to 100th record


def execute(sql, db_path):
    """Execute SQL query against database.

    Directly from original EHRSQL evaluate.py - no changes.
    """
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    result = cur.execute(sql).fetchall()
    con.close()
    return result


def execute_wrapper(sql, db_path, timeout=60, skip_indicator='null'):
    """Execute query with timeout and error handling.

    Directly from original EHRSQL evaluate.py with minimal adaptation.
    Uses func_timeout to enforce hard query timeout limit.
    """
    if sql != skip_indicator:
        try:
            result = func_timeout(timeout, execute, args=(sql, db_path))
        except KeyboardInterrupt:
            sys.exit(0)
        except FunctionTimedOut:
            result = [('timeout_pred',)]
        except Exception:
            result = [('error_pred',)]  # possibly len(query) > 512 or not executable
        result = process_answer(result)
    else:
        result = skip_indicator
    return result

def execute_query(sql1, sql2, db_path, timeout=60, data_idx=None):
    """Execute both gold and predicted queries.

    Wrapper for multiprocessing - returns both results for comparison.
    Directly from original EHRSQL evaluate.py.
    """
    result1 = execute_wrapper(sql1, db_path, timeout=timeout)
    result2 = execute_wrapper(sql2, db_path, timeout=timeout)
    return {'data_idx': data_idx, 'real': result1, 'pred': result2}


def execute_query_distributed(query_pairs, num_workers, timeout=60):
    """Execute queries in parallel using multiprocessing.

    Adapted from original EHRSQL evaluate.py to handle per-query db_paths.

    Args:
        query_pairs: List of (sql1, sql2, db_path, data_idx) tuples
        num_workers: Number of workers
        timeout: Query timeout in seconds
    """
    exec_result = []

    def result_tracker(result):
        exec_result.append(result)

    def execute_query_with_path(sql1, sql2, db_path, data_idx):
        """Wrapper that includes db_path."""
        return execute_query(sql1, sql2, db_path, timeout=timeout, data_idx=data_idx)

    pool = mp.Pool(processes=num_workers)
    for sql1, sql2, db_path, data_idx in query_pairs:
        pool.apply_async(
            execute_query_with_path,
            args=(sql1, sql2, db_path, data_idx),
            callback=result_tracker,
        )
    pool.close()
    pool.join()

    return exec_result




def evaluate_submission_rows(
    submission_rows: list[dict[str, Any]],
    answer_key_rows: list[dict[str, Any]],
    db_dir: Path,
    current_time: str = DEFAULT_CURRENT_TIME,
    timeout: int = 60,
    num_workers: int = -1,
) -> dict[str, Any]:
    """Evaluate submitted answers against answer key.

    Harbor adaptation: Takes submission and answer key as arguments instead of file paths.
    Computes original EHRSQL metrics: precision/recall/F1 for answerability and execution.
    Supports parallel evaluation via multiprocessing.

    Args:
        submission_rows: Agent-submitted answers from submission.json
        answer_key_rows: Expected answers from answer key
        db_dir: Base directory containing SQLite files
        current_time: Timestamp for SQL placeholder replacement
        timeout: Query timeout in seconds
        num_workers: Number of workers for parallel evaluation (-1 = auto-detect CPU count)

    Returns:
        Evaluation summary with pass_at_1 and per-query metrics
    """
    # Index answer key by task_id
    answer_key = {row['task_id']: row for row in answer_key_rows}

    # Prepare queries for execution (following original main() flow)
    # Build lists of queries with db_paths and metadata (adapted for multi-database Harbor tasks)
    query_real = []
    query_pred = []
    query_db_paths = []
    results = []

    for data_idx, sub in enumerate(submission_rows):
        task_id = sub.get('task_id')
        pred_sql = sub.get('final_answer', '')
        key_row = answer_key.get(task_id, {})
        expected_sql = key_row.get('expected_answer', '')
        db_id = key_row.get('db_id', 'mimic_iii')

        db_file = db_dir / db_id / f'{db_id}.sqlite'
        db_path = str(db_file)

        # Process queries (apply placeholder substitution)
        expected_sql_processed = post_process_sql(expected_sql, current_time=current_time)
        pred_sql_processed = post_process_sql(pred_sql, current_time=current_time)

        query_real.append(expected_sql_processed)
        query_pred.append(pred_sql_processed)
        query_db_paths.append(db_path)

        results.append({
            'task_id': task_id,
            'instruction': sub.get('instruction', ''),
            'db_id': db_id,
            'expected_sql': expected_sql,
            'submitted_sql': pred_sql,
            'expected_sql_processed': expected_sql_processed,
            'submitted_sql_processed': pred_sql_processed,
        })

    # Execute queries (parallel or single-threaded, following original main())
    num_workers_actual = mp.cpu_count() if num_workers == -1 else num_workers
    exec_real = []
    exec_pred = []

    # Execute queries (single-threaded for reliability)
    # Note: Multiprocessing in Harbor container environment can be unreliable;
    # single-threaded execution is preferred for evaluation consistency
    for sql1, sql2, db_path in zip(query_real, query_pred, query_db_paths):
        ret = execute_query(sql1, sql2, db_path, timeout=timeout)
        exec_real.append(ret['real'])
        exec_pred.append(ret['pred'])

    # Convert to numpy arrays (following original EHRSQL approach)
    exec_real = np.array(exec_real)
    exec_pred = np.array(exec_pred)

    # Compute metrics (original EHRSQL logic)
    precision_ans_list = []
    precision_exec_list = []
    recall_ans_list = []
    recall_exec_list = []

    for idx in range(len(exec_real)):
        ans_real, ans_pred = exec_real[idx], exec_pred[idx]

        # Answerability: was the query correctly identified as answerable or unanswerable?
        if ans_pred != 'null':  # calculate over predicted answerable queries
            precision_ans_list.append(1 if ans_real != 'null' else 0)
            precision_exec_list.append(1 if ans_real == ans_pred else 0)

        if ans_real != 'null':  # calculate over GT answerable queries
            recall_ans_list.append(1 if ans_pred != 'null' else 0)
            recall_exec_list.append(1 if ans_real == ans_pred else 0)

        # Store result details
        results[idx]['success'] = ans_real == ans_pred
        results[idx]['reason'] = (
            'both_null' if ans_real == 'null' and ans_pred == 'null'
            else 'answerability_mismatch' if (ans_real == 'null') != (ans_pred == 'null')
            else 'execution_error' if ans_pred.startswith('error_')
            else 'result_match' if ans_real == ans_pred
            else 'result_mismatch'
        )

        # Store SQL execution results for debugging
        results[idx]['expected_result'] = ans_real
        results[idx]['predicted_result'] = ans_pred

    # Calculate original EHRSQL metrics
    precision_ans = sum(precision_ans_list) / (len(precision_ans_list) + 1e-10)
    recall_ans = sum(recall_ans_list) / (len(recall_ans_list) + 1e-10)
    f1_ans = 2 * ((precision_ans * recall_ans) / (precision_ans + recall_ans + 1e-10))

    precision_exec = sum(precision_exec_list) / (len(precision_exec_list) + 1e-10)
    recall_exec = sum(recall_exec_list) / (len(recall_exec_list) + 1e-10)
    f1_exec = 2 * ((precision_exec * recall_exec) / (precision_exec + recall_exec + 1e-10))

    # Count successes for Harbor compatibility
    passed = sum(1 for r in results if r['success'])
    total = len(results)

    return {
        # Harbor compatibility metrics
        'pass_at_1': passed / total if total > 0 else 0.0,
        'total_tasks': total,
        'passed_tasks': passed,
        'failed_tasks': total - passed,

        # Original EHRSQL metrics
        'precision_ans': round(100.0 * precision_ans, 2),
        'recall_ans': round(100.0 * recall_ans, 2),
        'f1_ans': round(100.0 * f1_ans, 2),
        'precision_exec': round(100.0 * precision_exec, 2),
        'recall_exec': round(100.0 * recall_exec, 2),
        'f1_exec': round(100.0 * f1_exec, 2),

        # Per-task results
        'results': results,
    }


if __name__ == "__main__":
    # Standalone usage for testing
    import argparse

    parser = argparse.ArgumentParser(description='EHRSQL evaluator for Harbor')
    parser.add_argument('--submission', required=True, help='Path to submission.json')
    parser.add_argument('--answer-key', required=True, help='Path to task_answer_key.json')
    parser.add_argument('--db-dir', default='/data/ehrsql', help='Path to SQLite databases')
    parser.add_argument('--current-time', default=DEFAULT_CURRENT_TIME, help='Current time for placeholders')
    parser.add_argument('--timeout', type=int, default=60, help='Query timeout in seconds')
    parser.add_argument('--num-workers', type=int, default=-1, help='Number of parallel workers (-1 = auto-detect)')
    args = parser.parse_args()

    submission = json.loads(Path(args.submission).read_text())
    answer_key = json.loads(Path(args.answer_key).read_text())

    result = evaluate_submission_rows(
        submission,
        answer_key,
        Path(args.db_dir),
        current_time=args.current_time,
        timeout=args.timeout,
        num_workers=args.num_workers,
    )
    print(json.dumps(result, indent=2))
