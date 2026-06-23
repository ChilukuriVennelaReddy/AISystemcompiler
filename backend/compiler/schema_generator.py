import json
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

        # --- FALLBACK ENGINE ---
        domain = intent_ir.get('domain', 'General CRUD')
        roles = intent_ir.get('roles', ['Admin'])
        features = intent_ir.get('features', [])
        
        database = {}
        api = {"endpoints": []}
        ui = {"components": []}
        authentication = {
            "auth_provider": 'JWT',
            "roles": roles,
            "endpoint_permissions": [],
            "row_level_security": []
        }
        business_logic = {"rules": []}

        if domain == 'Kanban Project Management':
            database = {
                "tables": {
                    "users": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "email": {"type": 'VARCHAR(255)', "unique": True, "nullable": False},
                            "full_name": {"type": 'VARCHAR(100)', "nullable": False}
                        }
                    },
                    "workspaces": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "name": {"type": 'VARCHAR(100)', "nullable": False}
                        }
                    },
                    "projects": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "workspace_id": {"type": 'UUID', "nullable": False, "references": {"table": 'workspaces', "column": 'id'}},
                            "name": {"type": 'VARCHAR(100)', "nullable": False}
                        }
                    },
                    "tasks": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "project_id": {"type": 'UUID', "nullable": False, "references": {"table": 'projects', "column": 'id'}},
                            "title": {"type": 'VARCHAR(200)', "nullable": False},
                            "status": {"type": 'INTEGER' if introduce_anomalies else 'VARCHAR(50)', "nullable": False}
                        }
                    }
                }
            }

            api["endpoints"] = [
                {
                    "id": 'EP_GET_TASKS',
                    "method": 'GET',
                    "path": '/api/v1/projects/{projectId}/tasks',
                    "authentication": 'Required',
                    "parameters": [{"name": 'projectId', "in": 'path', "type": 'string', "required": True}],
                    "response_body": {
                        "tasks": {"type": 'array', "items": {"id": {"type": 'string'}, "title": {"type": 'string'}, "status": {"type": 'string'}}}
                    },
                    "db_operation": {"type": 'select', "table": 'tasks'}
                },
                {
                    "id": 'EP_UPDATE_TASK_STATUS',
                    "method": 'PATCH',
                    "path": '/api/v1/tasks/{taskId}/status',
                    "authentication": 'Required',
                    "parameters": [{"name": 'taskId', "in": 'path', "type": 'string', "required": True}],
                    "request_body": {
                        "status": {"type": 'string', "required": True}
                    },
                    "db_operation": {"type": 'update', "table": 'tasks'}
                }
            ]

            ui["components"] = [
                {
                    "id": 'COMP_KANBAN_BOARD',
                    "type": 'KanbanBoard',
                    "data_source": {
                        "endpoint_id": 'EP_GET_TASKS',
                        "params": {"projectId": 'state.activeProjectId'}
                    },
                    "actions": {
                        "onCardDrag": {
                            "endpoint_id": 'EP_UPDATE_TASK_STATUS',
                            "params": {"taskId": 'event.cardId', "status": 'event.targetColumn'}
                        }
                    }
                }
            ]

        elif domain == 'CRM':
            database = {
                "tables": {
                    "users": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "email": {"type": 'VARCHAR(255)', "unique": True, "nullable": False}
                        }
                    },
                    "contacts": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "first_name": {"type": 'VARCHAR(100)', "nullable": False},
                            "last_name": {"type": 'VARCHAR(100)', "nullable": False},
                            "email": {"type": 'VARCHAR(255)', "nullable": True},
                            "phone": {"type": 'INTEGER' if introduce_anomalies else 'VARCHAR(20)', "nullable": True}
                        }
                    }
                }
            }

            api["endpoints"] = [
                {
                    "id": 'EP_GET_CONTACTS',
                    "method": 'GET',
                    "path": '/api/v1/contacts',
                    "authentication": 'Required',
                    "response_body": {
                        "contacts": {"type": 'array', "items": {"id": {"type": 'string'}, "first_name": {"type": 'string'}, "phone": {"type": 'string'}}}
                    },
                    "db_operation": {"type": 'select', "table": 'contacts'}
                },
                {
                    "id": 'EP_CREATE_CONTACT',
                    "method": 'POST',
                    "path": '/api/v1/contacts',
                    "authentication": 'Required',
                    "request_body": {
                        "first_name": {"type": 'string', "required": True},
                        "last_name": {"type": 'string', "required": True},
                        "phone": {"type": 'string', "required": False}
                    },
                    "db_operation": {"type": 'insert', "table": 'contacts'}
                }
            ]

            ui["components"] = [
                {
                    "id": 'COMP_CONTACTS_LIST',
                    "type": 'TableList',
                    "data_source": {
                        "endpoint_id": 'EP_GET_CONTACTS',
                        "params": {}
                    }
                },
                {
                    "id": 'COMP_CONTACT_FORM',
                    "type": 'Form',
                    "actions": {
                        "onSubmit": {
                            "endpoint_id": 'EP_CREATE_CONTACT',
                            "params": {
                                "first_name": 'form.values.first_name',
                                "last_name": 'form.values.last_name',
                                "phone": 'form.values.phone'
                            }
                        }
                    }
                }
            ]

        else:
            database = {
                "tables": {
                    "items": {
                        "columns": {
                            "id": {"type": 'UUID', "primary_key": True, "nullable": False},
                            "title": {"type": 'VARCHAR(100)', "nullable": False},
                            "description": {"type": 'TEXT', "nullable": True}
                        }
                    }
                }
            }

            api["endpoints"] = [
                {
                    "id": 'EP_GET_ITEMS',
                    "method": 'GET',
                    "path": '/api/v1/items',
                    "authentication": 'Required',
                    "response_body": {"items": {"type": 'array', "items": {"id": {"type": 'string'}, "title": {"type": 'string'}}}},
                    "db_operation": {"type": 'select', "table": 'items'}
                }
            ]

            ui["components"] = [
                {
                    "id": 'COMP_ITEMS_LIST',
                    "type": 'List',
                    "data_source": {"endpoint_id": 'EP_GET_ITEMS', "params": {}}
                }
            ]

        for ep in api["endpoints"]:
            if ep["authentication"] == 'Required':
                authentication["endpoint_permissions"].append({
                    "endpoint_id": ep["id"],
                    "allowed_roles": ['Admin', 'Member'] if 'Admin' in roles else [roles[0]]
                })

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
