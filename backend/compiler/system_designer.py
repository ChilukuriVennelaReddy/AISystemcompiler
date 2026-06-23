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

        # --- FALLBACK ENGINE ---
        domain = intent_ir.get('domain', 'General CRUD')
        entities = intent_ir.get('entities', ['User'])
        roles = intent_ir.get('roles', ['Admin'])

        relationship_graph = []

        if 'User' in entities:
            if 'Workspace' in entities or 'Contact' in entities:
                primary_target = 'workspaces' if 'Workspace' in entities else 'contacts'
                relationship_graph.append({
                    "from": 'users',
                    "to": primary_target,
                    "type": 'Many-to-Many',
                    "through": 'workspace_members' if primary_target == 'workspaces' else None
                })

        if domain == 'Kanban Project Management':
            relationship_graph.extend([
                {"from": 'workspaces', "to": 'projects', "type": 'One-to-Many', "foreign_key": 'workspace_id'},
                {"from": 'projects', "to": 'tasks', "type": 'One-to-Many', "foreign_key": 'project_id'},
                {"from": 'tasks', "to": 'comments', "type": 'One-to-Many', "foreign_key": 'task_id'},
                {"from": 'users', "to": 'tasks', "type": 'One-to-Many', "foreign_key": 'assignee_id', "alias": 'assigned_tasks'}
            ])
        elif domain == 'CRM':
            relationship_graph.extend([
                {"from": 'companies', "to": 'contacts', "type": 'One-to-Many', "foreign_key": 'company_id'},
                {"from": 'contacts', "to": 'deals', "type": 'One-to-Many', "foreign_key": 'contact_id'},
                {"from": 'contacts', "to": 'interactions', "type": 'One-to-Many', "foreign_key": 'contact_id'}
            ])
        elif domain == 'E-commerce':
            relationship_graph.extend([
                {"from": 'users', "to": 'orders', "type": 'One-to-Many', "foreign_key": 'user_id'},
                {"from": 'orders', "to": 'order_items', "type": 'One-to-Many', "foreign_key": 'order_id'},
                {"from": 'products', "to": 'order_items', "type": 'One-to-Many', "foreign_key": 'product_id'}
            ])

        data_flow_topology = []
        if domain == 'Kanban Project Management':
            data_flow_topology.extend([
                {"flow_id": 'create_task_flow', "source": 'UI.TaskModal.SubmitButton', "transfers_through": 'API.PostTaskEndpoint', "target": 'DB.tasks.insert'},
                {"flow_id": 'get_task_board_flow', "source": 'DB.tasks.select', "transfers_through": 'API.GetTasksEndpoint', "target": 'UI.KanbanBoard.Cards'}
            ])
        elif domain == 'CRM':
            data_flow_topology.extend([
                {"flow_id": 'create_contact_flow', "source": 'UI.ContactForm.Submit', "transfers_through": 'API.PostContactEndpoint', "target": 'DB.contacts.insert'},
                {"flow_id": 'get_contacts_flow', "source": 'DB.contacts.select', "transfers_through": 'API.GetContactsEndpoint', "target": 'UI.ContactsList.Rows'}
            ])
        else:
            data_flow_topology.append(
                {"flow_id": 'generic_create_flow', "source": 'UI.Form.Submit', "transfers_through": 'API.PostEndpoint', "target": 'DB.generic.insert'}
            )

        routing_topology = {
            "base_path": '/app',
            "routes": [
                {"path": '/dashboard', "view": 'DashboardView', "allowed_roles": roles},
                {"path": '/settings', "view": 'SettingsView', "allowed_roles": ['Admin']}
            ]
        }

        if domain == 'Kanban Project Management':
            routing_topology["routes"].append({"path": '/workspace/:workspaceId', "view": 'WorkspaceView', "allowed_roles": roles})
        elif domain == 'CRM':
            routing_topology["routes"].append({"path": '/contacts', "view": 'ContactsListView', "allowed_roles": roles})
        elif domain == 'E-commerce':
            routing_topology["routes"].append({"path": '/shop', "view": 'ProductsShopView', "allowed_roles": roles})

        return {
            "relationshipGraph": relationship_graph,
            "dataFlowTopology": data_flow_topology,
            "routingTopology": routing_topology
        }
