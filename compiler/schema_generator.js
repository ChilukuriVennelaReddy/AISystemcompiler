const LLMClient = require('./llm_client');

class SchemaGenerator {
  async generate(intentIR, architectureIR, introduceAnomalies = false) {
    const systemInstruction = `You are the Schema Generation layer of an NL-to-App Compiler.
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

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping.`;

    const inputData = {
      intent: intentIR,
      architecture: architectureIR,
      introduce_anomalies: introduceAnomalies
    };

    const llmResult = await LLMClient.generateJSON(systemInstruction, JSON.stringify(inputData));
    if (llmResult) {
      return llmResult;
    }

    // --- FALLBACK ENGINE ---
    const { domain, roles, features } = intentIR;
    let database = {};
    let api = { endpoints: [] };
    let ui = { components: [] };
    let authentication = {
      auth_provider: 'JWT',
      roles: roles,
      endpoint_permissions: [],
      row_level_security: []
    };
    let business_logic = { rules: [] };

    if (domain === 'Kanban Project Management') {
      database = {
        tables: {
          users: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              email: { type: 'VARCHAR(255)', unique: true, nullable: false },
              full_name: { type: 'VARCHAR(100)', nullable: false }
            }
          },
          workspaces: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              name: { type: 'VARCHAR(100)', nullable: false }
            }
          },
          projects: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              workspace_id: { type: 'UUID', nullable: false, references: { table: 'workspaces', column: 'id' } },
              name: { type: 'VARCHAR(100)', nullable: false }
            }
          },
          tasks: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              project_id: { type: 'UUID', nullable: false, references: { table: 'projects', column: 'id' } },
              title: { type: 'VARCHAR(200)', nullable: false },
              status: { type: introduceAnomalies ? 'INTEGER' : 'VARCHAR(50)', nullable: false }
            }
          }
        }
      };

      api.endpoints = [
        {
          id: 'EP_GET_TASKS',
          method: 'GET',
          path: '/api/v1/projects/{projectId}/tasks',
          authentication: 'Required',
          parameters: [{ name: 'projectId', in: 'path', type: 'string', required: true }],
          response_body: {
            tasks: { type: 'array', items: { id: { type: 'string' }, title: { type: 'string' }, status: { type: 'string' } } }
          },
          db_operation: { type: 'select', table: 'tasks' }
        },
        {
          id: 'EP_UPDATE_TASK_STATUS',
          method: 'PATCH',
          path: '/api/v1/tasks/{taskId}/status',
          authentication: 'Required',
          parameters: [{ name: 'taskId', in: 'path', type: 'string', required: true }],
          request_body: {
            status: { type: 'string', required: true }
          },
          db_operation: { type: 'update', table: 'tasks' }
        }
      ];

      ui.components = [
        {
          id: 'COMP_KANBAN_BOARD',
          type: 'KanbanBoard',
          data_source: {
            endpoint_id: 'EP_GET_TASKS',
            params: { projectId: 'state.activeProjectId' }
          },
          actions: {
            onCardDrag: {
              endpoint_id: 'EP_UPDATE_TASK_STATUS',
              params: { taskId: 'event.cardId', status: 'event.targetColumn' }
            }
          }
        }
      ];

    } else if (domain === 'CRM') {
      database = {
        tables: {
          users: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              email: { type: 'VARCHAR(255)', unique: true, nullable: false }
            }
          },
          contacts: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              first_name: { type: 'VARCHAR(100)', nullable: false },
              last_name: { type: 'VARCHAR(100)', nullable: false },
              email: { type: 'VARCHAR(255)', nullable: true },
              phone: { type: introduceAnomalies ? 'INTEGER' : 'VARCHAR(20)', nullable: true }
            }
          }
        }
      };

      api.endpoints = [
        {
          id: 'EP_GET_CONTACTS',
          method: 'GET',
          path: '/api/v1/contacts',
          authentication: 'Required',
          response_body: {
            contacts: { type: 'array', items: { id: { type: 'string' }, first_name: { type: 'string' }, phone: { type: 'string' } } }
          },
          db_operation: { type: 'select', table: 'contacts' }
        },
        {
          id: 'EP_CREATE_CONTACT',
          method: 'POST',
          path: '/api/v1/contacts',
          authentication: 'Required',
          request_body: {
            first_name: { type: 'string', required: true },
            last_name: { type: 'string', required: true },
            phone: { type: 'string', required: false }
          },
          db_operation: { type: 'insert', table: 'contacts' }
        }
      ];

      ui.components = [
        {
          id: 'COMP_CONTACTS_LIST',
          type: 'TableList',
          data_source: {
            endpoint_id: 'EP_GET_CONTACTS',
            params: {}
          }
        },
        {
          id: 'COMP_CONTACT_FORM',
          type: 'Form',
          actions: {
            onSubmit: {
              endpoint_id: 'EP_CREATE_CONTACT',
              params: {
                first_name: 'form.values.first_name',
                last_name: 'form.values.last_name',
                phone: 'form.values.phone'
              }
            }
          }
        }
      ];

    } else {
      database = {
        tables: {
          items: {
            columns: {
              id: { type: 'UUID', primary_key: true, nullable: false },
              title: { type: 'VARCHAR(100)', nullable: false },
              description: { type: 'TEXT', nullable: true }
            }
          }
        }
      };

      api.endpoints = [
        {
          id: 'EP_GET_ITEMS',
          method: 'GET',
          path: '/api/v1/items',
          authentication: 'Required',
          response_body: { items: { type: 'array', items: { id: { type: 'string' }, title: { type: 'string' } } } },
          db_operation: { type: 'select', table: 'items' }
        }
      ];

      ui.components = [
        {
          id: 'COMP_ITEMS_LIST',
          type: 'List',
          data_source: { endpoint_id: 'EP_GET_ITEMS', params: {} }
        }
      ];
    }

    api.endpoints.forEach(ep => {
      if (ep.authentication === 'Required') {
        authentication.endpoint_permissions.push({
          endpoint_id: ep.id,
          allowed_roles: roles.includes('Admin') ? ['Admin', 'Member'] : [roles[0]]
        });
      }
    });

    if (features.includes('Payments')) {
      business_logic.rules.push({
        id: 'RULE_PREMIUM_PLAN_GATE',
        event: 'api.request.execute',
        condition: "request.user.plan !== 'Premium' && request.path.includes('/premium-feature')",
        action: "ABORT('This feature requires a premium plan. Please upgrade.')"
      });
    }

    return {
      database,
      api,
      ui,
      authentication,
      business_logic
    };
  }
}

module.exports = SchemaGenerator;
