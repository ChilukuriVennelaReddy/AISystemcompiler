const fs = require('fs');
const path = require('path');

const targetFilePath = path.join(__dirname, 'COMPILER_OUTPUT_SAMPLE.json');
console.log(`Loading compilation artifact from: ${targetFilePath}`);

let ast;
try {
  const content = fs.readFileSync(targetFilePath, 'utf8');
  ast = JSON.parse(content);
  console.log('✓ JSON Syntax check passed successfully.');
} catch (err) {
  console.error('✗ Failed to parse JSON:', err.message);
  process.exit(1);
}

const errors = [];

// 1. Validate Database Integrity
const tables = ast.database_schema.tables;
console.log('\n--- Scanning Database Layer ---');
for (const [tableName, tableSpec] of Object.entries(tables)) {
  console.log(`Scanning table: ${tableName}`);
  for (const [colName, colSpec] of Object.entries(tableSpec.columns)) {
    if (colSpec.references) {
      const refTable = colSpec.references.table;
      const refCol = colSpec.references.column;
      if (!tables[refTable]) {
        errors.push(`[DB ERROR] Table "${tableName}" column "${colName}" references non-existent table "${refTable}"`);
      } else if (!tables[refTable].columns[refCol]) {
        errors.push(`[DB ERROR] Table "${tableName}" column "${colName}" references non-existent column "${refCol}" in table "${refTable}"`);
      } else {
        console.log(`  ✓ Foreign Key verified: ${tableName}.${colName} -> ${refTable}.${refCol}`);
      }
    }
  }
}

// 2. Validate API-to-Database Mapping
console.log('\n--- Scanning API Layer ---');
const endpoints = ast.api_schema.endpoints;
endpoints.forEach(ep => {
  console.log(`Scanning Endpoint [${ep.method} ${ep.path}]`);
  if (ep.db_operation) {
    const targetTable = ep.db_operation.table;
    if (!tables[targetTable]) {
      errors.push(`[API ERROR] Endpoint "${ep.id}" (${ep.path}) maps to non-existent DB table "${targetTable}"`);
    } else {
      console.log(`  ✓ Database Mapping verified: target table "${targetTable}" exists.`);
    }
  }
});

// 3. Validate UI-to-API Binding
console.log('\n--- Scanning UI Layer ---');
const components = ast.ui_schema.components;
components.forEach(comp => {
  console.log(`Scanning UI Component: ${comp.id} (${comp.type})`);
  if (comp.data_source) {
    const epId = comp.data_source.endpoint_id;
    const matchedEp = endpoints.find(ep => ep.id === epId);
    if (!matchedEp) {
      errors.push(`[UI ERROR] Component "${comp.id}" binds to non-existent API Endpoint ID "${epId}"`);
    } else {
      console.log(`  ✓ UI Data Source Binding verified: maps to endpoint ID "${epId}" (${matchedEp.method} ${matchedEp.path})`);
    }
  }
  
  if (comp.actions) {
    for (const [actionName, actionSpec] of Object.entries(comp.actions)) {
      const epId = actionSpec.endpoint_id;
      const matchedEp = endpoints.find(ep => ep.id === epId);
      if (!matchedEp) {
        errors.push(`[UI ERROR] Component "${comp.id}" action "${actionName}" binds to non-existent API Endpoint ID "${epId}"`);
      } else {
        console.log(`  ✓ UI Action Binding verified: ${actionName} maps to endpoint ID "${epId}" (${matchedEp.method} ${matchedEp.path})`);
      }
    }
  }
});

// 4. Validate Authentication Coverage
console.log('\n--- Scanning Security/Auth Layer ---');
const authRules = ast.authentication_rules;
endpoints.forEach(ep => {
  if (ep.authentication === 'Required') {
    const matchedRule = authRules.endpoint_permissions.find(p => p.endpoint_id === ep.id);
    if (!matchedRule) {
      errors.push(`[AUTH ERROR] Secured endpoint "${ep.id}" does not have any permissions defined in authentication_rules.`);
    } else {
      console.log(`  ✓ Endpoint Security verified: "${ep.id}" maps to allowed roles [${matchedRule.allowed_roles.join(', ')}]`);
    }
  }
});

console.log('\n--- Validation Summary ---');
if (errors.length > 0) {
  console.error(`✗ Validation failed with ${errors.length} errors:`);
  errors.forEach(err => console.error(`  - ${err}`));
  process.exit(1);
} else {
  console.log('✓ All cross-layer semantic validations passed successfully!');
  console.log('✓ COMPILER_OUTPUT_SAMPLE.json is 100% consistent.');
  process.exit(0);
}
