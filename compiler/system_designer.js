const LLMClient = require('./llm_client');

class SystemDesigner {
  async design(intentIR) {
    const systemInstruction = `You are the System Design layer of an NL-to-App Compiler.
Your job is to translate an Intent IR into an Architecture IR JSON containing:
- relationshipGraph: array of objects { from: string, to: string, type: string, foreign_key: string } defining entity connections (use plural lowercase table names like 'users', 'tasks').
- dataFlowTopology: array of objects { flow_id: string, source: string, transfers_through: string, target: string } mapping UI actions -> API endpoints -> DB operations.
- routingTopology: object { base_path: string, routes: array of objects { path: string, view: string, allowed_roles: array of strings } }.

Ensure that all routes, endpoints, and relationships map directly to the entities and roles identified in the Intent IR:
Domain: ${intentIR.domain}
Entities: ${intentIR.entities.join(', ')}
Roles: ${intentIR.roles.join(', ')}

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping.`;

    const llmResult = await LLMClient.generateJSON(systemInstruction, JSON.stringify(intentIR));
    if (llmResult) {
      return llmResult;
    }

    // --- FALLBACK ENGINE ---
    const { domain, entities, roles } = intentIR;
    const relationshipGraph = [];
    
    if (entities.includes('User')) {
      if (entities.includes('Workspace') || entities.includes('Contact')) {
        const primaryTarget = entities.includes('Workspace') ? 'workspaces' : 'contacts';
        relationshipGraph.push({
          from: 'users',
          to: primaryTarget,
          type: 'Many-to-Many',
          through: primaryTarget === 'workspaces' ? 'workspace_members' : null
        });
      }
    }

    if (domain === 'Kanban Project Management') {
      relationshipGraph.push(
        { from: 'workspaces', to: 'projects', type: 'One-to-Many', foreign_key: 'workspace_id' },
        { from: 'projects', to: 'tasks', type: 'One-to-Many', foreign_key: 'project_id' },
        { from: 'tasks', to: 'comments', type: 'One-to-Many', foreign_key: 'task_id' },
        { from: 'users', to: 'tasks', type: 'One-to-Many', foreign_key: 'assignee_id', alias: 'assigned_tasks' }
      );
    } else if (domain === 'CRM') {
      relationshipGraph.push(
        { from: 'companies', to: 'contacts', type: 'One-to-Many', foreign_key: 'company_id' },
        { from: 'contacts', to: 'deals', type: 'One-to-Many', foreign_key: 'contact_id' },
        { from: 'contacts', to: 'interactions', type: 'One-to-Many', foreign_key: 'contact_id' }
      );
    } else if (domain === 'E-commerce') {
      relationshipGraph.push(
        { from: 'users', to: 'orders', type: 'One-to-Many', foreign_key: 'user_id' },
        { from: 'orders', to: 'order_items', type: 'One-to-Many', foreign_key: 'order_id' },
        { from: 'products', to: 'order_items', type: 'One-to-Many', foreign_key: 'product_id' }
      );
    }

    const dataFlowTopology = [];
    if (domain === 'Kanban Project Management') {
      dataFlowTopology.push(
        { flow_id: 'create_task_flow', source: 'UI.TaskModal.SubmitButton', transfers_through: 'API.PostTaskEndpoint', target: 'DB.tasks.insert' },
        { flow_id: 'get_task_board_flow', source: 'DB.tasks.select', transfers_through: 'API.GetTasksEndpoint', target: 'UI.KanbanBoard.Cards' }
      );
    } else if (domain === 'CRM') {
      dataFlowTopology.push(
        { flow_id: 'create_contact_flow', source: 'UI.ContactForm.Submit', transfers_through: 'API.PostContactEndpoint', target: 'DB.contacts.insert' },
        { flow_id: 'get_contacts_flow', source: 'DB.contacts.select', transfers_through: 'API.GetContactsEndpoint', target: 'UI.ContactsList.Rows' }
      );
    } else {
      dataFlowTopology.push(
        { flow_id: 'generic_create_flow', source: 'UI.Form.Submit', transfers_through: 'API.PostEndpoint', target: 'DB.generic.insert' }
      );
    }

    const routingTopology = {
      base_path: '/app',
      routes: [
        { path: '/dashboard', view: 'DashboardView', allowed_roles: roles },
        { path: '/settings', view: 'SettingsView', allowed_roles: ['Admin'] }
      ]
    };

    if (domain === 'Kanban Project Management') {
      routingTopology.routes.push({ path: '/workspace/:workspaceId', view: 'WorkspaceView', allowed_roles: roles });
    } else if (domain === 'CRM') {
      routingTopology.routes.push({ path: '/contacts', view: 'ContactsListView', allowed_roles: roles });
    } else if (domain === 'E-commerce') {
      routingTopology.routes.push({ path: '/shop', view: 'ProductsShopView', allowed_roles: roles });
    }

    return {
      relationshipGraph,
      dataFlowTopology,
      routingTopology
    };
  }
}

module.exports = SystemDesigner;
