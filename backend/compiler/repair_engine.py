import copy
import json
import re
from typing import Dict, Any, List
from .llm_client import LLMClient

class RepairEngine:
    def repair(self, ast: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        repaired_ast = copy.deepcopy(ast)
        repair_logs = []

        errors = validation_report.get("errors", [])
        for err in errors:
            err_target = err.get("target", "")
            err_type = err.get("type", "")
            print(f"[REPAIR ENGINE] Correcting target: {err_target} (Type: {err_type})")

            system_instruction = """You are the Repair Engine of an NL-to-App Compiler.
Your job is to apply a targeted fix to an AST subtree to resolve a validation error.

You are given:
- The entire current AST configuration
- The validation error details

Your goal is to correct the target AST subtree so that the validation error is resolved.
Output ONLY the repaired subtree as a valid JSON object. Do not include markdown code block wrapping."""

            input_context = {
                "error": err,
                "full_ast": ast
            }

            llm_repaired_subtree = LLMClient.generate_json(system_instruction, json.dumps(input_context))
            
            resolved = False
            if llm_repaired_subtree:
                if err_type == 'TYPE_MISMATCH':
                    # Parse target e.g. "api.endpoints[1].request_body.phone"
                    parts = err_target.split('.')
                    if parts[0] == 'api' and parts[1].startswith('endpoints['):
                        match = re.search(r'\d+', parts[1])
                        if match:
                            index = int(match.group())
                            field = parts[3]
                            endpoint = repaired_ast.get("api", {}).get("endpoints", [])[index]
                            db_table = endpoint.get("db_operation", {}).get("table")
                            
                            tables = repaired_ast.get("database", {}).get("tables", {})
                            if db_table in tables and field in tables[db_table].get("columns", {}):
                                old_type = tables[db_table]["columns"][field].get("type")
                                new_type = llm_repaired_subtree.get("type") or 'VARCHAR(50)'
                                tables[db_table]["columns"][field]["type"] = new_type
                                
                                repair_logs.append({
                                    "error": f"Type mismatch at {err_target}",
                                    "repair": f"Synced DB column {db_table}.{field} type from {old_type} to {new_type}",
                                    "status": "Resolved",
                                    "target_ast_subtree": f"database.tables.{db_table}.columns.{field}",
                                    "patch_applied": {"before": {"type": old_type}, "after": {"type": new_type}}
                                })
                                resolved = True
                elif err_type == 'MISSING_SECURITY_POLICY':
                    repaired_ast.setdefault("authentication", {}).setdefault("endpoint_permissions", []).append(llm_repaired_subtree)
                    repair_logs.append({
                        "error": f"Missing security policy for {err_target}",
                        "repair": f"Added permissions configuration: {llm_repaired_subtree}",
                        "status": "Resolved",
                        "target_ast_subtree": "authentication.endpoint_permissions",
                        "patch_applied": {"before": "none", "after": llm_repaired_subtree}
                    })
                    resolved = True

            if not resolved:
                # --- FALLBACK REPAIR LOGIC ---
                if err_type == 'TYPE_MISMATCH':
                    parts = err_target.split('.')
                    if parts[0] == 'api' and parts[1].startswith('endpoints['):
                        match = re.search(r'\d+', parts[1])
                        if match:
                            index = int(match.group())
                            field = parts[3]
                            endpoint = repaired_ast.get("api", {}).get("endpoints", [])[index]
                            db_table = endpoint.get("db_operation", {}).get("table")
                            
                            tables = repaired_ast.get("database", {}).get("tables", {})
                            if db_table in tables and field in tables[db_table].get("columns", {}):
                                old_type = tables[db_table]["columns"][field].get("type")
                                tables[db_table]["columns"][field]["type"] = 'VARCHAR(50)'
                                
                                repair_logs.append({
                                    "error": f"Type mismatch at {err_target}",
                                    "repair": f"Synced DB column {db_table}.{field} type from {old_type} to VARCHAR(50)",
                                    "status": "Resolved",
                                    "target_ast_subtree": f"database.tables.{db_table}.columns.{field}",
                                    "patch_applied": {"before": {"type": old_type}, "after": {"type": 'VARCHAR(50)'}}
                                })
                elif err_type == 'MISSING_SECURITY_POLICY':
                    policy = {
                        "endpoint_id": err_target,
                        "allowed_roles": ['Admin', 'Member']
                    }
                    repaired_ast.setdefault("authentication", {}).setdefault("endpoint_permissions", []).append(policy)
                    
                    repair_logs.append({
                        "error": f"Missing security policy for {err_target}",
                        "repair": f"Added permissions configuration for role Admin/Member",
                        "status": "Resolved",
                        "target_ast_subtree": "authentication.endpoint_permissions",
                        "patch_applied": {"before": "none", "after": policy}
                    })

        return {
            "ast": repaired_ast,
            "logs": repair_logs
        }
