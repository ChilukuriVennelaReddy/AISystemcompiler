import os
import json
import time
import sqlite3
from typing import Dict, Any, List

from .compiler import AppCompiler

class Evaluator:
    def __init__(self):
        self.compiler = AppCompiler()

    def run(self) -> Dict[str, Any]:
        print('\n=========================================')
        print('🧪 RUNNING COMPILER REGRESSION TEST HARNESS')
        print('=========================================')

        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_set_path = os.path.join(current_dir, '..', '..', 'test_prompts.json')
        if not os.path.exists(test_set_path):
            print(f"✗ Test prompts file not found at {test_set_path}")
            return {"success": False, "error": "Prompts file missing"}

        with open(test_set_path, 'r') as f:
            test_data = json.load(f)
            
        all_prompts = []
        for p in test_data.get("product_prompts", []):
            p["category"] = "Standard Product"
            all_prompts.append(p)
        for p in test_data.get("edge_cases", []):
            p["category"] = "Edge Case"
            all_prompts.append(p)

        results = []
        total_latency = 0
        successful_compilations = 0
        total_repairs = 0

        # Silence standard console print during evaluation runs to prevent log clutter
        import sys
        class SilenceOutput:
            def __enter__(self):
                self._original_stdout = sys.stdout
                sys.stdout = open(os.devnull, 'w')
            def __exit__(self, exc_type, exc_val, exc_tb):
                sys.stdout.close()
                sys.stdout = self._original_stdout

        for i, test_case in enumerate(all_prompts):
            is_anomalous = test_case["category"] == "Edge Case" or i % 3 == 0
            start = time.time()
            
            with SilenceOutput():
                try:
                    res = self.compiler.compile(test_case["prompt"], is_anomalous)
                    success = res.get("success", False)
                except Exception as e:
                    res = {"success": False, "errors": [str(e)]}
                    success = False
            
            duration_ms = int((time.time() - start) * 1000)
            total_latency += duration_ms

            rep_count = 0
            if "compilationOutput" in res:
                rep_count = res["compilationOutput"].get("repair_reports", {}).get("total_repairs_needed", 0)
            
            total_repairs += rep_count
            if success:
                successful_compilations += 1

            results.append({
                "id": test_case["id"],
                "category": test_case["category"],
                "prompt_snippet": test_case["prompt"][:50] + "...",
                "success": success,
                "repairs": rep_count,
                "latency_ms": duration_ms
            })

        # Save results to sqlite history DB
        db_path = os.path.join(current_dir, '..', 'compiler_history.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Init DB schema if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                id INTEGER PRIMARY KEY AUTO增,
                timestamp TEXT,
                total_prompts INTEGER,
                success_rate REAL,
                avg_latency_ms REAL,
                avg_repairs REAL,
                detailed_results TEXT
            )
        '''.replace("AUTO增", "AUTOINCREMENT"))
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compilation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                prompt TEXT,
                success INTEGER,
                latency_ms INTEGER,
                repairs INTEGER,
                domain TEXT,
                output_json TEXT
            )
        ''')
        
        success_rate = (successful_compilations / len(all_prompts)) * 100
        avg_latency = total_latency / len(all_prompts)
        avg_repairs = total_repairs / len(all_prompts)

        cursor.execute('''
            INSERT INTO evaluation_runs (timestamp, total_prompts, success_rate, avg_latency_ms, avg_repairs, detailed_results)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            len(all_prompts),
            success_rate,
            avg_latency,
            avg_repairs,
            json.dumps(results)
        ))
        conn.commit()
        conn.close()

        # Display results table
        print('\n---------------------------------------------------------------------------------------------')
        print('| ID  | Category         | Prompt Snippet                                     | Status  | Repairs | Latency |')
        print('---------------------------------------------------------------------------------------------')
        for r in results:
            status = 'PASSED ' if r["success"] else 'FAILED '
            repairs = str(r["repairs"]).ljust(7)
            latency = f"{r['latency_ms']}ms".ljust(7)
            id_val = r["id"].ljust(3)
            cat = r["category"].ljust(16)
            pmt = r["prompt_snippet"].ljust(50)
            print(f"| {id_val} | {cat} | {pmt} | {status} | {repairs} | {latency} |")
        print('---------------------------------------------------------------------------------------------')

        print('\n=========================================')
        print('📊 AGGREGATE EVALUATION REPORT')
        print('=========================================')
        print(f"Total Prompts Compiled:    {len(all_prompts)}")
        print(f"Success Rate:              {success_rate:.1f}% (Pass Target: 95%+)")
        print(f"Average Latency:           {avg_latency:.1f}ms")
        print(f"Average Repairs / Request: {avg_repairs:.2f} (Target: < 2.0)")
        print(f"Total System Repairs:      {total_repairs}")
        print('=========================================\n')

        return {
            "total_prompts": len(all_prompts),
            "success_rate": success_rate,
            "avg_latency": avg_latency,
            "avg_repairs": avg_repairs,
            "results": results
        }

if __name__ == "__main__":
    evaluator = Evaluator()
    evaluator.run()
