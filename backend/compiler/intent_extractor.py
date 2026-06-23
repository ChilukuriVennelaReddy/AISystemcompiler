import re
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

        # --- DYNAMIC FALLBACK ENGINE ---
        # Instead of static templates, dynamically parse nouns/verbs to support ANY prompt
        text = prompt.lower()
        
        # 1. Domain Detection
        domain = "General CRUD"
        if any(w in text for w in ["crm", "lead", "deal", "contact", "sales"]):
            domain = "CRM"
        elif any(w in text for w in ["task", "board", "project", "kanban", "todo"]):
            domain = "Kanban Project Management"
        elif any(w in text for w in ["shop", "store", "product", "e-commerce", "buy", "cart"]):
            domain = "E-commerce"
        elif any(w in text for w in ["school", "classroom", "course", "student", "teacher", "learn"]):
            domain = "Classroom Learning Management"
        elif any(w in text for w in ["hospital", "patient", "appointment", "doctor", "clinic"]):
            domain = "Healthcare Portal"
        elif any(w in text for w in ["book", "library", "author", "borrow"]):
            domain = "Library Management"

        # 2. Dynamic Entity Extraction (find nouns in the prompt text)
        entities = ["User"] # Always have User as a base entity
        
        # Clean words list
        words = re.findall(r'\b\w+\b', text)
        
        # Common entity candidates mapping
        candidate_map = {
            "contact": "Contact", "company": "Company", "deal": "Deal", "interaction": "Interaction",
            "task": "Task", "project": "Project", "workspace": "Workspace", "comment": "Comment",
            "product": "Product", "order": "Order", "cart": "Cart", "payment": "Payment",
            "student": "Student", "course": "Course", "assignment": "Assignment", "submission": "Submission",
            "patient": "Patient", "doctor": "Doctor", "appointment": "Appointment", "prescription": "Prescription",
            "book": "Book", "author": "Author", "loan": "Loan", "member": "Member",
            "post": "Post", "blog": "Blog", "category": "Category", "tag": "Tag",
            "ticket": "Ticket", "bug": "Bug", "issue": "Issue", "sprint": "Sprint"
        }
        
        for word in words:
            singular = word.rstrip('s') # simple plural removal
            if singular in candidate_map and candidate_map[singular] not in entities:
                entities.append(candidate_map[singular])
                
        # If no specific entities found, dynamically create from unmatched nouns
        if len(entities) == 1:
            # Add a generic table based on domain key
            generic_name = domain.split()[0]
            entities.append(generic_name)

        # 3. Features
        features = []
        if any(w in text for w in ["login", "auth", "signup", "access", "password"]):
            features.append("Authentication")
        if any(w in text for w in ["payment", "premium", "pay", "billing", "stripe", "subscription"]):
            features.append("Payments")
        if any(w in text for w in ["analytics", "dashboard", "report", "chart", "metrics"]):
            features.append("Analytics Dashboard")
        if any(w in text for w in ["notification", "email", "alert", "message"]):
            features.append("Notifications")

        # 4. Roles
        roles = []
        role_keywords = {
            "admin": "Admin",
            "member": "Member",
            "editor": "Editor",
            "viewer": "Viewer",
            "guest": "Guest",
            "customer": "Customer",
            "buyer": "Buyer",
            "student": "Student",
            "teacher": "Teacher",
            "doctor": "Doctor",
            "patient": "Patient"
        }
        for word in words:
            if word in role_keywords and role_keywords[word] not in roles:
                roles.append(role_keywords[word])
                
        if not roles:
            roles = ["Admin", "Member", "Guest"]
            
        assumptions = []
        if not any(w in text for w in ["role", "permission", "access"]):
            assumptions.append({
                "context": "User Roles",
                "assumption": f"No roles specified. Standard RBAC [{', '.join(roles)}] provisioned by compiler."
            })
            
        ambiguities = []
        conflicts = []
        
        if len(prompt) < 20:
            ambiguities.append("Extremely short prompt. Lacks functional specification.")
            assumptions.append({
                "context": "Scope Limitation",
                "assumption": "The prompt is under 20 characters. Compiling basic single-entity read/write system."
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
