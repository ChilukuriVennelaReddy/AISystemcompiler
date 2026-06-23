import json
import copy
from typing import Dict, Any, List
from .llm_client import LLMClient

class SchemaGenerator:
    def generate(self, intent_ir: Dict[str, Any], architecture_ir: Dict[str, Any], introduce_anomalies: bool = False) -> Dict[str, Any]:
        system_instruction = """You are the Schema Generation layer of an NL-to-App Compiler.
Your job is to translate the Intent and Architecture IRs into final database schemas, API schemas, UI component schemas, Authentication rules, and Business logic rules.

Output a structured JSON object containing:
- database: { tables: { [tableName]: { columns: { [colName]: { type: string, primary_key?: boolean, nullable?: boolean, unique?: boolean, references?: { table: string, column: string } } } } } }
- api: { endpoints: [{ id: string, method: string, path: string, authentication: string, parameters?: [], request_body?: {}, response_body?: {}, db_operation?: { type: string, table: string } }] }
- ui: { components: [{ id: string, type: string, data_source?: { endpoint_id: string, params: {} }, actions?: { [actionName]: { endpoint_id: string, params: {} } } }] }
- authentication: { auth_provider: string, roles: [], endpoint_permissions: [{ endpoint_id: string, allowed_roles: [] }], row_level_security?: [] }
- business_logic: { rules: [{ id: string, event: string, condition: string, action: string }] }

Ensure cross-layer schema consistency:
1. Every DB reference refers to an existing table.
2. Endpoint DB operations point to real tables.
3. UI components load data or execute actions using endpoints in the API schema.
4. Security endpoint_permissions must list endpoints in the API schema.

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping."""

        input_data = {
            "intent": intent_ir,
            "architecture": architecture_ir,
            "introduce_anomalies": introduce_anomalies
        }

        llm_result = LLMClient.generate_json(system_instruction, json.dumps(input_data))
        if llm_result:
            return llm_result

        # --- DYNAMIC FALLBACK ENGINE ---
        domain = intent_ir.get('domain', 'General CRUD')
        roles = intent_ir.get('roles', ['Admin'])
        features = intent_ir.get('features', [])
        entities = intent_ir.get('entities', ['User'])
        
        # Lowercase plural helper
        def plural(name: str) -> str:
            name_lower = name.lower()
            if name_lower.endswith('y'):
                return name_lower[:-1] + "ies"
            elif name_lower.endswith('s'):
                return name_lower
            return name_lower + "s"

        standard_entity_columns = {
            "User": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "email": {"type": "VARCHAR(255)", "unique": True, "nullable": False},
                "full_name": {"type": "VARCHAR(100)", "nullable": False}
            },
            "Contact": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "first_name": {"type": "VARCHAR(100)", "nullable": False},
                "last_name": {"type": "VARCHAR(100)", "nullable": False},
                "email": {"type": "VARCHAR(255)", "nullable": True},
                "phone": {"type": "VARCHAR(20)", "nullable": True}
            },
            "Company": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "industry": {"type": "VARCHAR(100)", "nullable": True},
                "website": {"type": "VARCHAR(255)", "nullable": True}
            },
            "Deal": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(100)", "nullable": False},
                "value": {"type": "VARCHAR(50)", "nullable": True},
                "stage": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Interaction": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "type": {"type": "VARCHAR(50)", "nullable": False},
                "notes": {"type": "TEXT", "nullable": True},
                "date": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Task": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "status": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Project": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "description": {"type": "TEXT", "nullable": True}
            },
            "Workspace": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False}
            },
            "Comment": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "content": {"type": "TEXT", "nullable": False}
            },
            "Product": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "price": {"type": "VARCHAR(50)", "nullable": False},
                "stock": {"type": "INTEGER", "nullable": False}
            },
            "Order": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "order_number": {"type": "VARCHAR(50)", "nullable": False},
                "total": {"type": "VARCHAR(50)", "nullable": False},
                "status": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Cart": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "session_id": {"type": "VARCHAR(100)", "nullable": False},
                "total": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Payment": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "amount": {"type": "VARCHAR(50)", "nullable": False},
                "method": {"type": "VARCHAR(50)", "nullable": False},
                "status": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Student": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "first_name": {"type": "VARCHAR(100)", "nullable": False},
                "last_name": {"type": "VARCHAR(100)", "nullable": False},
                "grade_level": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Course": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(100)", "nullable": False},
                "code": {"type": "VARCHAR(50)", "nullable": False},
                "description": {"type": "TEXT", "nullable": True}
            },
            "Assignment": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "due_date": {"type": "VARCHAR(50)", "nullable": True},
                "max_points": {"type": "INTEGER", "nullable": True}
            },
            "Submission": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "grade": {"type": "VARCHAR(10)", "nullable": True},
                "submitted_at": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Patient": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "first_name": {"type": "VARCHAR(100)", "nullable": False},
                "last_name": {"type": "VARCHAR(100)", "nullable": False},
                "date_of_birth": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Doctor": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "first_name": {"type": "VARCHAR(100)", "nullable": False},
                "last_name": {"type": "VARCHAR(100)", "nullable": False},
                "specialization": {"type": "VARCHAR(100)", "nullable": True}
            },
            "Appointment": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "date_time": {"type": "VARCHAR(50)", "nullable": False},
                "reason": {"type": "TEXT", "nullable": True},
                "status": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Prescription": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "medication": {"type": "VARCHAR(100)", "nullable": False},
                "dosage": {"type": "VARCHAR(100)", "nullable": False},
                "instructions": {"type": "TEXT", "nullable": True}
            },
            "Book": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "isbn": {"type": "VARCHAR(50)", "nullable": True},
                "genre": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Author": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "bio": {"type": "TEXT", "nullable": True}
            },
            "Loan": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "borrow_date": {"type": "VARCHAR(50)", "nullable": False},
                "return_date": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Member": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "membership_type": {"type": "VARCHAR(50)", "nullable": True}
            },
            "Post": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "content": {"type": "TEXT", "nullable": True}
            },
            "Blog": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "url": {"type": "VARCHAR(255)", "nullable": False}
            },
            "Category": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False}
            },
            "Tag": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Ticket": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "subject": {"type": "VARCHAR(200)", "nullable": False},
                "priority": {"type": "VARCHAR(50)", "nullable": False},
                "status": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Bug": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "severity": {"type": "VARCHAR(50)", "nullable": False}
            },
            "Issue": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "title": {"type": "VARCHAR(200)", "nullable": False},
                "description": {"type": "TEXT", "nullable": True}
            },
            "Sprint": {
                "id": {"type": "UUID", "primary_key": True, "nullable": False},
                "name": {"type": "VARCHAR(100)", "nullable": False},
                "start_date": {"type": "VARCHAR(50)", "nullable": True},
                "end_date": {"type": "VARCHAR(50)", "nullable": True}
            }
        }

        # Build database tables
        tables = {}
        for entity in entities:
            t_name = plural(entity)
            cols = {}
            if entity in standard_entity_columns:
                cols = copy.deepcopy(standard_entity_columns[entity])
            else:
                # default generic fallback columns
                cols = {
                    "id": {"type": "UUID", "primary_key": True, "nullable": False},
                    "name": {"type": "VARCHAR(100)", "nullable": False},
                    "description": {"type": "TEXT", "nullable": True},
                    "status": {"type": "VARCHAR(50)", "nullable": True}
                }
            tables[t_name] = {"columns": cols}

        # Inject references from relationshipGraph in architecture_ir
        rel_graph = architecture_ir.get("relationshipGraph", [])
        for rel in rel_graph:
            from_t = rel.get("from")
            to_t = rel.get("to")
            fk = rel.get("foreign_key")
            if to_t in tables and fk:
                tables[to_t]["columns"][fk] = {
                    "type": "UUID",
                    "nullable": False,
                    "references": {"table": from_t, "column": "id"}
                }

        database = {"tables": tables}

        # Dynamically build API endpoints
        api = {"endpoints": []}
        ui = {"components": []}

        # For mapping table name back to singular camelCase/PascalCase to build parameters
        table_to_entity = {plural(e): e for e in entities}

        for t_name, t_spec in tables.items():
            entity_name = table_to_entity.get(t_name, t_name.rstrip('s').capitalize())
            entity_upper = entity_name.upper()
            entity_upper_plural = t_name.upper()
            
            # Check if there is a parent table referencing this table
            parent_table = None
            parent_fk = None
            for rel in rel_graph:
                if rel.get("to") == t_name:
                    parent_table = rel.get("from")
                    parent_fk = rel.get("foreign_key")
                    break

            # 1. GET (list/select) endpoint
            ep_get_id = f"EP_GET_{entity_upper_plural}"
            ep_get_path = f"/api/v1/{t_name}"
            ep_get_params = []
            
            if parent_table:
                parent_entity = table_to_entity.get(parent_table, parent_table.rstrip('s').capitalize())
                parent_param_name = parent_entity[0].lower() + parent_entity[1:] + "Id"
                ep_get_path = f"/api/v1/{parent_table}/{{{parent_param_name}}}/{t_name}"
                ep_get_params.append({
                    "name": parent_param_name,
                    "in": "path",
                    "type": "string",
                    "required": True
                })

            response_fields = {}
            for col, col_spec in t_spec["columns"].items():
                col_type = col_spec.get("type", "VARCHAR").lower()
                field_type = "integer" if "int" in col_type else "string"
                response_fields[col] = {"type": field_type}

            api["endpoints"].append({
                "id": ep_get_id,
                "method": "GET",
                "path": ep_get_path,
                "authentication": "Required",
                "parameters": ep_get_params,
                "response_body": {
                    t_name: {
                        "type": "array",
                        "items": response_fields
                    }
                },
                "db_operation": {"type": "select", "table": t_name}
            })

            # 2. POST (insert) endpoint
            ep_post_id = f"EP_CREATE_{entity_upper}"
            ep_post_path = f"/api/v1/{t_name}"
            ep_post_params = []

            if parent_table:
                parent_entity = table_to_entity.get(parent_table, parent_table.rstrip('s').capitalize())
                parent_param_name = parent_entity[0].lower() + parent_entity[1:] + "Id"
                ep_post_path = f"/api/v1/{parent_table}/{{{parent_param_name}}}/{t_name}"
                ep_post_params.append({
                    "name": parent_param_name,
                    "in": "path",
                    "type": "string",
                    "required": True
                })

            request_body = {}
            for col, col_spec in t_spec["columns"].items():
                if col == "id" or col == "created_at" or col == parent_fk:
                    continue
                col_type = col_spec.get("type", "VARCHAR").lower()
                field_type = "integer" if "int" in col_type else "string"
                request_body[col] = {
                    "type": field_type,
                    "required": not col_spec.get("nullable", True)
                }

            api["endpoints"].append({
                "id": ep_post_id,
                "method": "POST",
                "path": ep_post_path,
                "authentication": "Required",
                "parameters": ep_post_params,
                "request_body": request_body,
                "db_operation": {"type": "insert", "table": t_name}
            })

            # 3. UI Component binding
            if t_name != "users":
                has_status = "status" in t_spec["columns"]
                comp_type = "KanbanBoard" if has_status else "TableList"
                
                # data_source params mapping
                ds_params = {}
                if parent_table:
                    parent_entity = table_to_entity.get(parent_table, parent_table.rstrip('s').capitalize())
                    parent_param_name = parent_entity[0].lower() + parent_entity[1:] + "Id"
                    ds_params[parent_param_name] = f"state.active{parent_entity}Id"

                # onSubmit action params mapping
                form_action_params = {}
                for field in request_body.keys():
                    form_action_params[field] = f"form.values.{field}"
                if parent_table:
                    parent_entity = table_to_entity.get(parent_table, parent_table.rstrip('s').capitalize())
                    parent_param_name = parent_entity[0].lower() + parent_entity[1:] + "Id"
                    form_action_params[parent_param_name] = f"state.active{parent_entity}Id"

                ui["components"].append({
                    "id": f"COMP_{entity_upper}_LIST",
                    "type": comp_type,
                    "data_source": {
                        "endpoint_id": ep_get_id,
                        "params": ds_params
                    }
                })

                ui["components"].append({
                    "id": f"COMP_{entity_upper}_FORM",
                    "type": "Form",
                    "actions": {
                        "onSubmit": {
                            "endpoint_id": ep_post_id,
                            "params": form_action_params
                        }
                    }
                })

        # Introduce type mismatch anomalies if requested
        if introduce_anomalies:
            anomaly_introduced = False
            for ep in api["endpoints"]:
                if ep.get("method") == "POST" and ep.get("request_body"):
                    target_table = ep.get("db_operation", {}).get("table")
                    if target_table in database["tables"]:
                        for field_name, field_spec in ep["request_body"].items():
                            if field_spec.get("type") == "string":
                                columns = database["tables"][target_table]["columns"]
                                if field_name in columns:
                                    columns[field_name]["type"] = "INTEGER"
                                    anomaly_introduced = True
                                    break
                if anomaly_introduced:
                    break

        # Build authentication Permissions
        authentication = {
            "auth_provider": 'JWT',
            "roles": roles,
            "endpoint_permissions": [],
            "row_level_security": []
        }
        for ep in api["endpoints"]:
            if ep["authentication"] == 'Required':
                # Allow Admin & Member by default, or just the first role if not Admin
                allowed = ['Admin', 'Member'] if 'Admin' in roles else [roles[0]]
                authentication["endpoint_permissions"].append({
                    "endpoint_id": ep["id"],
                    "allowed_roles": [r for r in allowed if r in roles] or [roles[0]]
                })

        # Build business logic rules
        business_logic = {"rules": []}
        if 'Payments' in features:
            business_logic["rules"].append({
                "id": 'RULE_PREMIUM_PLAN_GATE',
                "event": 'api.request.execute',
                "condition": "request.user.plan != 'Premium' and '/premium-feature' in request.path",
                "action": "ABORT('This feature requires a premium plan. Please upgrade.')"
            })

        return {
            "database": database,
            "api": api,
            "ui": ui,
            "authentication": authentication,
            "business_logic": business_logic
        }
