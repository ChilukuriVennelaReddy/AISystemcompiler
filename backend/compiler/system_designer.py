import json
from typing import Dict, Any, List
from .llm_client import LLMClient

class SystemDesigner:
    def design(self, intent_ir: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = f"""You are the System Design layer of an NL-to-App Compiler.
Your job is to translate an Intent IR into an Architecture IR JSON containing:
- relationshipGraph: array of objects {{ from: string, to: string, type: string, foreign_key: string }} defining entity connections (use plural lowercase table names like 'users', 'tasks').
- dataFlowTopology: array of objects {{ flow_id: string, source: string, transfers_through: string, target: string }} mapping UI actions -> API endpoints -> DB operations.
- routingTopology: object {{ base_path: string, routes: array of objects {{ path: string, view: string, allowed_roles: array of strings }} }}.

Ensure that all routes, endpoints, and relationships map directly to the entities and roles identified in the Intent IR:
Domain: {intent_ir.get('domain')}
Entities: {', '.join(intent_ir.get('entities', []))}
Roles: {', '.join(intent_ir.get('roles', []))}

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping."""

        llm_result = LLMClient.generate_json(system_instruction, json.dumps(intent_ir))
        if llm_result:
            return llm_result

        # --- DYNAMIC FALLBACK SYSTEM DESIGN ---
        entities = intent_ir.get("entities", ["User"])
        roles = intent_ir.get("roles", ["Admin"])
        domain = intent_ir.get("domain", "General CRUD")

        relationship_graph = []
        data_flow_topology = []
        
        # Lowercase pluralized helper
        def plural(name: str) -> str:
            name_lower = name.lower()
            if name_lower.endswith('y'):
                return name_lower[:-1] + "ies"
            elif name_lower.endswith('s'):
                return name_lower
            return name_lower + "s"

        # Dynamically link entities
        # E.g. User, Project, Task -> users, projects, tasks
        plural_entities = [plural(e) for e in entities]
        
        # Link all entities sequentially or to Users
        if len(plural_entities) > 1:
            main_parent = plural_entities[0] # Usually users
            for idx in range(1, len(plural_entities)):
                child = plural_entities[idx]
                parent = plural_entities[idx - 1]
                
                # If linking to users, use user_id, else parent_id
                fk_name = "user_id" if parent == "users" else f"{entities[idx-1].lower()}_id"
                relationship_graph.append({
                    "from": parent,
                    "to": child,
                    "type": "One-to-Many",
                    "foreign_key": fk_name
                })
                
                # Add data flow mappings dynamically
                data_flow_topology.append({
                    "flow_id": f"create_{entities[idx].lower()}_flow",
                    "source": f"UI.{entities[idx]}Form.Submit",
                    "transfers_through": f"API.Post{entities[idx]}Endpoint",
                    "target": f"DB.{child}.insert"
                })

        # If data flows is empty, add generic crud flow
        if not data_flow_topology:
            data_flow_topology.append({
                "flow_id": "generic_read_flow",
                "source": "DB.users.select",
                "transfers_through": "API.GetUsersEndpoint",
                "target": "UI.UsersList.View"
            })

        # Dynamic routes based on roles and entities
        routing_topology = {
            "base_path": "/app",
            "routes": [
                {"path": "/dashboard", "view": "DashboardView", "allowed_roles": roles},
                {"path": "/settings", "view": "SettingsView", "allowed_roles": ["Admin"] if "Admin" in roles else roles}
            ]
        }
        
        # Add dynamic views for each entity
        for idx in range(1, min(len(entities), 4)):
            entity_plural = plural(entities[idx])
            routing_topology["routes"].append({
                "path": f"/{entity_plural}",
                "view": f"{entities[idx]}ListView",
                "allowed_roles": roles
            })

        return {
            "relationshipGraph": relationship_graph,
            "dataFlowTopology": data_flow_topology,
            "routingTopology": routing_topology
        }
