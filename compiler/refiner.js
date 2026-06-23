/**
 * Refiner / Multi-Layer Validation Engine
 * Executes static validation checks across Database, API, UI, and Auth layers.
 */
class Refiner {
  validate(ast) {
    const errors = [];
    const tables = ast.database.tables;
    const endpoints = ast.api.endpoints;
    const components = ast.ui.components;
    const auth = ast.authentication;

    // 1. Database Integrity & Key Checks
    for (const [tableName, tableSpec] of Object.entries(tables)) {
      for (const [colName, colSpec] of Object.entries(tableSpec.columns)) {
        if (colSpec.references) {
          const refTable = colSpec.references.table;
          const refCol = colSpec.references.column;
          if (!tables[refTable]) {
            errors.push({
              layer: 'DB',
              target: `${tableName}.${colName}`,
              type: 'MISSING_TABLE',
              message: `Table "${tableName}" column "${colName}" references non-existent table "${refTable}"`
            });
          } else if (!tables[refTable].columns[refCol]) {
            errors.push({
              layer: 'DB',
              target: `${tableName}.${colName}`,
              type: 'MISSING_COLUMN',
              message: `Table "${tableName}" column "${colName}" references non-existent column "${refCol}" in table "${refTable}"`
            });
          }
        }
      }
    }

    // 2. API-to-Database Mapping & Type Checking
    endpoints.forEach(ep => {
      if (ep.db_operation) {
        const targetTable = ep.db_operation.table;
        if (!tables[targetTable]) {
          errors.push({
            layer: 'API',
            target: `${ep.id} -> db_operation`,
            type: 'MISSING_DB_MAPPING',
            message: `Endpoint "${ep.id}" (${ep.path}) maps to non-existent DB table "${targetTable}"`
          });
        } else {
          // Verify that types are compatible between endpoint request body/params and DB columns
          if (ep.request_body) {
            for (const [fieldName, fieldSpec] of Object.entries(ep.request_body)) {
              const dbCol = tables[targetTable].columns[fieldName];
              if (dbCol) {
                const apiType = fieldSpec.type.toLowerCase();
                const dbType = dbCol.type.toLowerCase();
                
                // Mismatch conditions
                if (apiType === 'string' && dbType.includes('integer')) {
                  errors.push({
                    layer: 'API',
                    target: `api.endpoints[${endpoints.indexOf(ep)}].request_body.${fieldName}`,
                    type: 'TYPE_MISMATCH',
                    message: `Type mismatch. API body field "${fieldName}" has type "${apiType}", but matching DB column "${targetTable}.${fieldName}" has type "${dbType}"`
                  });
                }
              }
            }
          }
        }
      }
    });

    // 3. UI-to-API Binding & Parameter Checking
    components.forEach(comp => {
      if (comp.data_source) {
        const epId = comp.data_source.endpoint_id;
        const matchedEp = endpoints.find(e => e.id === epId);
        if (!matchedEp) {
          errors.push({
            layer: 'UI',
            target: `${comp.id} -> data_source`,
            type: 'MISSING_API_MAPPING',
            message: `UI Component "${comp.id}" binds to non-existent API Endpoint ID "${epId}"`
          });
        }
      }

      if (comp.actions) {
        for (const [actionName, actionSpec] of Object.entries(comp.actions)) {
          const epId = actionSpec.endpoint_id;
          const matchedEp = endpoints.find(e => e.id === epId);
          if (!matchedEp) {
            errors.push({
              layer: 'UI',
              target: `${comp.id} -> actions -> ${actionName}`,
              type: 'MISSING_API_MAPPING',
              message: `UI Component "${comp.id}" action "${actionName}" binds to non-existent API Endpoint ID "${epId}"`
            });
          }
        }
      }
    });

    // 4. Security Layer Coverage Checks
    endpoints.forEach(ep => {
      if (ep.authentication === 'Required') {
        const hasPermission = auth.endpoint_permissions.some(p => p.endpoint_id === ep.id);
        if (!hasPermission) {
          errors.push({
            layer: 'AUTH',
            target: ep.id,
            type: 'MISSING_SECURITY_POLICY',
            message: `Secured endpoint "${ep.id}" has no endpoint_permissions defined.`
          });
        }
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

module.exports = Refiner;
