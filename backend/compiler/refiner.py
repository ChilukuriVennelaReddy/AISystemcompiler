from typing import Dict, Any, List

class Refiner:
    def validate(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        database = ast.get("database", {})
        tables = database.get("tables", {})
        api = ast.get("api", {})
        endpoints = api.get("endpoints", [])
        ui = ast.get("ui", {})
        components = ui.get("components", [])
        auth = ast.get("authentication", {})
        endpoint_permissions = auth.get("endpoint_permissions", [])

        # 1. Database Integrity & Key Checks
        for table_name, table_spec in tables.items():
            columns = table_spec.get("columns", {})
            for col_name, col_spec in columns.items():
                if isinstance(col_spec, dict) and "references" in col_spec:
                    ref_table = col_spec["references"].get("table")
                    ref_col = col_spec["references"].get("column")
                    if ref_table not in tables:
                        errors.append({
                            "layer": 'DB',
                            "target": f"{table_name}.{col_name}",
                            "type": 'MISSING_TABLE',
                            "message": f"Table '{table_name}' column '{col_name}' references non-existent table '{ref_table}'"
                        })
                    elif ref_col not in tables[ref_table].get("columns", {}):
                        errors.append({
                            "layer": 'DB',
                            "target": f"{table_name}.{col_name}",
                            "type": 'MISSING_COLUMN',
                            "message": f"Table '{table_name}' column '{col_name}' references non-existent column '{ref_col}' in table '{ref_table}'"
                        })

        # 2. API-to-Database Mapping & Type Checking
        for idx, ep in enumerate(endpoints):
            db_op = ep.get("db_operation")
            if db_op:
                target_table = db_op.get("table")
                if target_table not in tables:
                    errors.append({
                        "layer": 'API',
                        "target": f"{ep.get('id')} -> db_operation",
                        "type": 'MISSING_DB_MAPPING',
                        "message": f"Endpoint '{ep.get('id')}' ({ep.get('path')}) maps to non-existent DB table '{target_table}'"
                    })
                else:
                    # Verify that types are compatible between endpoint request body/params and DB columns
                    req_body = ep.get("request_body")
                    if req_body:
                        for field_name, field_spec in req_body.items():
                            db_col = tables[target_table].get("columns", {}).get(field_name)
                            if db_col:
                                api_type = field_spec.get("type", "").lower()
                                db_type = db_col.get("type", "").lower()
                                
                                # Mismatch conditions
                                if api_type == 'string' and 'integer' in db_type:
                                    errors.append({
                                        "layer": 'API',
                                        "target": f"api.endpoints[{idx}].request_body.{field_name}",
                                        "type": 'TYPE_MISMATCH',
                                        "message": f"Type mismatch. API body field '{field_name}' has type '{api_type}', but matching DB column '{target_table}.{field_name}' has type '{db_type}'"
                                    })

        # 3. UI-to-API Binding & Parameter Checking
        for comp in components:
            data_src = comp.get("data_source")
            if data_src:
                ep_id = data_src.get("endpoint_id")
                matched_ep = next((e for e in endpoints if e.get("id") == ep_id), None)
                if not matched_ep:
                    errors.append({
                        "layer": 'UI',
                        "target": f"{comp.get('id')} -> data_source",
                        "type": 'MISSING_API_MAPPING',
                        "message": f"UI Component '{comp.get('id')}' binds to non-existent API Endpoint ID '{ep_id}'"
                    })

            actions = comp.get("actions", {})
            if actions:
                for action_name, action_spec in actions.items():
                    ep_id = action_spec.get("endpoint_id")
                    matched_ep = next((e for e in endpoints if e.get("id") == ep_id), None)
                    if not matched_ep:
                        errors.append({
                            "layer": 'UI',
                            "target": f"{comp.get('id')} -> actions -> {action_name}",
                            "type": 'MISSING_API_MAPPING',
                            "message": f"UI Component '{comp.get('id')}' action '{action_name}' binds to non-existent API Endpoint ID '{ep_id}'"
                        })

        # 4. Security Layer Coverage Checks
        for ep in endpoints:
            if ep.get("authentication") == 'Required':
                has_permission = any(p.get("endpoint_id") == ep.get("id") for p in endpoint_permissions)
                if not has_permission:
                    errors.append({
                        "layer": 'AUTH',
                        "target": ep.get("id"),
                        "type": 'MISSING_SECURITY_POLICY',
                        "message": f"Secured endpoint '{ep.get('id')}' has no endpoint_permissions defined."
                    })

        # Generate warnings for ambiguities recorded
        intent_ir = ast.get("intent_ir", {}) if "intent_ir" in ast else ast
        for amb in intent_ir.get("ambiguities", []):
            warnings.append(amb)

        return {
            "status": "PASS" if not errors else "FAIL",
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
