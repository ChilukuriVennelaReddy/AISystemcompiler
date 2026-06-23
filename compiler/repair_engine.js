const LLMClient = require('./llm_client');

class RepairEngine {
  async repair(ast, validationReport) {
    const repairedAst = JSON.parse(JSON.stringify(ast)); // Deep clone the AST
    const repairLogs = [];

    for (const err of validationReport.errors) {
      console.log(`[REPAIR ENGINE] Correcting target: ${err.target} (Type: ${err.type})`);

      const systemInstruction = `You are the Repair Engine of an NL-to-App Compiler.
Your job is to apply a targeted fix to an AST subtree to resolve a validation error.

You are given:
- The entire current AST configuration
- The validation error details

Your goal is to correct the target AST subtree so that the validation error is resolved.
Output ONLY the repaired subtree as a valid JSON object. Do not include markdown code block wrapping.`;

      const inputContext = {
        error: err,
        full_ast: ast
      };

      const llmRepairedSubtree = await LLMClient.generateJSON(systemInstruction, JSON.stringify(inputContext));
      
      if (llmRepairedSubtree) {
        // Dynamically apply the repaired subtree patch returned by the LLM
        if (err.type === 'TYPE_MISMATCH') {
          const parts = err.target.split('.');
          if (parts[0] === 'api' && parts[1].startsWith('endpoints[')) {
            const index = parseInt(parts[1].match(/\d+/)[0]);
            const field = parts[3];
            const endpoint = repairedAst.api.endpoints[index];
            const dbTable = endpoint.db_operation.table;

            if (repairedAst.database.tables[dbTable] && repairedAst.database.tables[dbTable].columns[field]) {
              const oldType = repairedAst.database.tables[dbTable].columns[field].type;
              repairedAst.database.tables[dbTable].columns[field].type = llmRepairedSubtree.type || 'VARCHAR(50)';
              
              repairLogs.push({
                error_matched: err,
                target_ast_subtree: `database.tables.${dbTable}.columns.${field}`,
                patch_applied: {
                  before: { type: oldType },
                  after: { type: repairedAst.database.tables[dbTable].columns[field].type }
                },
                status: 'Resolved'
              });
            }
          }
        } else if (err.type === 'MISSING_SECURITY_POLICY') {
          repairedAst.authentication.endpoint_permissions.push(llmRepairedSubtree);
          repairLogs.push({
            error_matched: err,
            target_ast_subtree: 'authentication.endpoint_permissions',
            patch_applied: {
              before: 'none',
              after: llmRepairedSubtree
            },
            status: 'Resolved'
          });
        }
      } else {
        // --- FALLBACK REPAIR LOGIC ---
        if (err.type === 'TYPE_MISMATCH') {
          const parts = err.target.split('.');
          if (parts[0] === 'api' && parts[1].startsWith('endpoints[')) {
            const index = parseInt(parts[1].match(/\d+/)[0]);
            const field = parts[3];
            const endpoint = repairedAst.api.endpoints[index];
            const dbTable = endpoint.db_operation.table;

            if (repairedAst.database.tables[dbTable] && repairedAst.database.tables[dbTable].columns[field]) {
              const oldType = repairedAst.database.tables[dbTable].columns[field].type;
              repairedAst.database.tables[dbTable].columns[field].type = 'VARCHAR(50)'; // Sync to string type
              
              repairLogs.push({
                error_matched: err,
                target_ast_subtree: `database.tables.${dbTable}.columns.${field}`,
                patch_applied: {
                  before: { type: oldType },
                  after: { type: 'VARCHAR(50)' }
                },
                status: 'Resolved'
              });
            }
          }
        } else if (err.type === 'MISSING_SECURITY_POLICY') {
          repairedAst.authentication.endpoint_permissions.push({
            endpoint_id: err.target,
            allowed_roles: ['Admin', 'Member']
          });
          
          repairLogs.push({
            error_matched: err,
            target_ast_subtree: 'authentication.endpoint_permissions',
            patch_applied: {
              before: 'none',
              after: { endpoint_id: err.target, allowed_roles: ['Admin', 'Member'] }
            },
            status: 'Resolved'
          });
        }
      }
    }

    return {
      ast: repairedAst,
      logs: repairLogs
    };
  }
}

module.exports = RepairEngine;
