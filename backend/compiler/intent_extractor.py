from typing import Dict, Any, List
from .llm_client import LLMClient

class IntentExtractor:
    def extract(self, prompt: str) -> Dict[str, Any]:
        system_instruction = """You are the Intent Extraction layer of an NL-to-App Compiler.
Your job is to parse unstructured user prompt requirements into a structured Intent Intermediate Representation (IR) JSON containing:
- domain: string (e.g. CRM, Kanban, E-commerce, Wiki, Classroom)
- entities: array of strings representing entity names (singular, PascalCase, e.g. User, Task, Contact, Product)
- features: array of strings (e.g. Authentication, Payments, Analytics, etc.)
- roles: array of strings representing user roles
- ambiguities: array of strings explaining vague or underspecified requirements
- conflicts: array of strings explaining contradictory requests
- assumptions: array of objects { context: string, assumption: string } mapping choices made to resolve ambiguities.

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping."""

        llm_result = LLMClient.generate_json(system_instruction, prompt)
        if llm_result:
            llm_result["raw_prompt"] = prompt
            return llm_result

        # --- FALLBACK ENGINE ---
        text = prompt.lower()
        domain = 'General CRUD'
        entities = ['User']

        if 'crm' in text or 'contact' in text or 'sales' in text:
            domain = 'CRM'
            entities = ['User', 'Contact', 'Company', 'Deal', 'Interaction']
        elif any(k in text for k in ['task', 'kanban', 'project', 'board']):
            domain = 'Kanban Project Management'
            entities = ['User', 'Workspace', 'Project', 'Task', 'Comment', 'ActivityLog']
        elif any(k in text for k in ['shop', 'store', 'e-commerce', 'checkout', 'product']):
            domain = 'E-commerce'
            entities = ['User', 'Product', 'Order', 'OrderItem', 'Cart', 'Payment']

        features = []
        if any(k in text for k in ['login', 'auth', 'signup']):
            features.append('Authentication')
        if any(k in text for k in ['payment', 'premium', 'billing', 'stripe']):
            features.append('Payments')
        if any(k in text for k in ['analytics', 'dashboard', 'report', 'chart']):
            features.append('Analytics Dashboard')
        if any(k in text for k in ['notification', 'email', 'alert']):
            features.append('Notifications')

        roles = []
        if 'admin' in text:
            roles.append('Admin')
        if 'member' in text or 'editor' in text:
            roles.append('Member')
        if 'viewer' in text or 'guest' in text:
            roles.append('Guest')
        if 'customer' in text or 'buyer' in text:
            roles.append('Customer')

        assumptions = []
        if not roles:
            roles = ['Admin', 'Member', 'Guest']
            assumptions.append({
                "context": 'User Roles',
                "assumption": 'No roles specified. Compiler provisioned standard role-based access control (Admin, Member, Guest).'
            })

        ambiguities = []
        conflicts = []

        if len(prompt) < 20:
            ambiguities.append('Extremely short prompt. Lacks functional specification.')
            assumptions.append({
                "context": 'Scope Limitation',
                "assumption": 'The prompt is under 20 characters. Compiling basic single-entity read/write system.'
            })

        if not any(k in text for k in ['role', 'permission', 'access']):
            ambiguities.append('Access control details are underspecified.')

        if 'guest can edit' in text and 'guest is read-only' in text:
            conflicts.append('Conflicting permissions: Guest is defined as both read-only and having edit rights.')
            assumptions.append({
                "context": 'Guest Role Conflict',
                "assumption": 'Resolved conflict by restricting Guest role to read-only views for security safety.'
            })

        return {
            "domain": domain,
            "entities": entities,
            "features": features,
            "roles": roles,
            "ambiguities": ambiguities,
            "conflicts": conflicts,
            "assumptions": assumptions,
            "raw_prompt": prompt
        }
