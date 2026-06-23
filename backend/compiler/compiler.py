import os
import json
import time
from typing import Dict, Any, List

from .intent_extractor import IntentExtractor
from .system_designer import SystemDesigner
from .schema_generator import SchemaGenerator
from .refiner import Refiner
from .repair_engine import RepairEngine
from .execution_simulator import ExecutionSimulator
from .artifact_generator import ArtifactGenerator

class AppCompiler:
    def __init__(self):
        self.intent_extractor = IntentExtractor()
        self.system_designer = SystemDesigner()
        self.schema_generator = SchemaGenerator()
        self.refiner = Refiner()
        self.repair_engine = RepairEngine()
        self.simulator = ExecutionSimulator()

    def compile(self, prompt: str, introduce_anomalies: bool = False) -> Dict[str, Any]:
        print('\n=========================================')
        print('🏁 STARTING COMPILATION PIPELINE (PYTHON)')
        print(f'Prompt: "{prompt}"')
        print('=========================================')

        start = time.time()

        # Stage 1: Intent Extraction Layer
        print('\n[STAGE 1] Lexing and Intent Extraction...')
        intent_ir = self.intent_extractor.extract(prompt)
        print(f"  ✓ Domain matched: {intent_ir.get('domain')}")
        print(f"  ✓ Roles extracted: [{', '.join(intent_ir.get('roles', []))}]")
        print(f"  ✓ Features extracted: [{', '.join(intent_ir.get('features', []))}]")
        if intent_ir.get('ambiguities'):
            print(f"  ⚠ Ambiguities Detected: \n     - " + "\n     - ".join(intent_ir.get('ambiguities')))

        # Stage 2: System Design Layer
        print('\n[STAGE 2] Converting Intent to Architecture IR...')
        architecture_ir = self.system_designer.design(intent_ir)
        print(f"  ✓ Relationships mapped: {len(architecture_ir.get('relationshipGraph', []))} links")
        print(f"  ✓ Routing routes defined: {len(architecture_ir.get('routingTopology', {}).get('routes', []))} paths")

        # Stage 3: Schema Generation Layer
        print('\n[STAGE 3] Schema Generation (DB, API, UI, Auth, Rules)...')
        raw_config = self.schema_generator.generate(intent_ir, architecture_ir, introduce_anomalies)
        print('  ✓ Initial raw schemas provisioned.')

        # Stage 4: Refinement / Validation Layer
        print('\n[STAGE 4] Executing Static Validation Scans...')
        validation_report = self.refiner.validate(raw_config)
        final_config = raw_config
        repair_logs = []

        if not validation_report.get("valid"):
            print(f"  ✗ Validation errors detected: {len(validation_report.get('errors', []))} issues.")
            
            # Stage 5: Targeted Repair Engine
            print('\n[STAGE 5] Triggering Targeted Repair Engine...')
            repair_result = self.repair_engine.repair(raw_config, validation_report)
            final_config = repair_result.get("ast")
            repair_logs = repair_result.get("logs", [])
            
            print('  ✓ Patches applied. Re-running validation...')
            validation_report = self.refiner.validate(final_config)

        if validation_report.get("valid"):
            print('  ✓ Configuration validated: 100% Consistent and Type-Safe.')
        else:
            print('  ✗ Final validation failed. Compilation aborted.')
            return {"success": False, "errors": validation_report.get("errors")}

        # Stage 6: Execution Plan Generation
        execution_plan = self.generate_execution_plan(final_config)

        # Assemble Final Output Document
        compilation_output = {
            "metadata": {
                "compiler_version": 'v1.0.0-prod-python',
                "compilation_time_ms": int((time.time() - start) * 1000),
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            },
            "intent_ir": intent_ir,
            "architecture_ir": architecture_ir,
            "database_schema": final_config.get("database"),
            "api_schema": final_config.get("api"),
            "ui_schema": final_config.get("ui"),
            "authentication_rules": final_config.get("authentication"),
            "business_logic_rules": final_config.get("business_logic"),
            "validation_reports": {
                "valid": validation_report.get("valid"),
                "errors": validation_report.get("errors")
            },
            "repair_reports": {
                "total_repairs_needed": len(repair_logs),
                "repair_attempts": repair_logs
            },
            "assumptions": intent_ir.get("assumptions", []),
            "execution_plans": {
                "execution_graph_nodes": execution_plan
            }
        }

        # Save configuration build file to output directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(os.path.dirname(current_dir), '..', 'dist')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'app_configuration.json')
        with open(output_path, 'w') as f:
            json.dump(compilation_output, f, indent=2)
            
        print(f"\n✓ Emitter: Compiled output saved to {output_path}")

        # Stage 7: Execution Simulation Check
        simulation_result = self.simulator.simulate(final_config)

        # Generate target code files (SQLite, FastAPI, Streamlit)
        generated_files = ArtifactGenerator.generate(final_config, output_dir)
        print(f"✓ Generated executable target application artifacts: {list(generated_files.keys())}")

        return {
            "success": True,
            "outputPath": output_path,
            "compilationOutput": compilation_output,
            "simulationResult": simulation_result,
            "generatedFiles": generated_files
        }

    def generate_execution_plan(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = []
        step_count = 1

        # Table migrations
        tables = config.get("database", {}).get("tables", {})
        for table in tables.keys():
            nodes.append({
                "id": f"STEP_{step_count}_DB_MIGRATION_{table.upper()}",
                "action": 'CREATE_TABLE',
                "description": f"Create database table: \"{table}\"",
                "depends_on": []
            })
            step_count += 1

        # API Route register
        if config.get("api", {}).get("endpoints"):
            nodes.append({
                "id": f"STEP_{step_count}_API_GATEWAY_SYNC",
                "action": 'REGISTER_ROUTES',
                "description": 'Bind endpoint pathways and request validation schemas',
                "depends_on": [n["id"] for n in nodes]
            })
            step_count += 1

        # UI render deploy
        if config.get("ui", {}).get("components"):
            nodes.append({
                "id": f"STEP_{step_count}_UI_FRONTEND_COMPILE",
                "action": 'DEPLOY_VIEWS',
                "description": 'Compile layouts and bind state action data-sources',
                "depends_on": [f"STEP_{step_count - 2}_API_GATEWAY_SYNC"]
            })
            step_count += 1

        return nodes

if __name__ == "__main__":
    import sys
    compiler = AppCompiler()
    default_prompt = "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    trigger_repair = "--trigger-repair" in sys.argv or "-r" in sys.argv
    
    compiler.compile(prompt, trigger_repair)
