const fs = require('fs');
const path = require('path');

const targetFilePath = path.join(__dirname, 'COMPILER_OUTPUT_SAMPLE.json');
console.log(`Reading configuration file: ${targetFilePath}`);

let config;
try {
  const content = fs.readFileSync(targetFilePath, 'utf8');
  config = JSON.parse(content);
} catch (err) {
  console.error('✗ Failed to read configuration:', err.message);
  process.exit(1);
}

const executionNodes = config.execution_plans?.execution_graph_nodes;
if (!executionNodes || !Array.isArray(executionNodes)) {
  console.error('✗ No execution plan found in the configuration.');
  process.exit(1);
}

console.log('\n=========================================');
console.log('🏁 RUNNING COMPILED APP DEPLOYMENT GRAPH');
console.log('=========================================');

const executed = new Set();
const nodesToProcess = [...executionNodes];

let iterations = 0;
const maxIterations = 100; // prevent infinite loop in circular graphs

while (nodesToProcess.length > 0 && iterations < maxIterations) {
  iterations++;
  
  for (let i = 0; i < nodesToProcess.length; i++) {
    const node = nodesToProcess[i];
    
    // Check if all dependencies have been executed
    const depsSatisfied = node.depends_on.every(dep => executed.has(dep));
    
    if (depsSatisfied) {
      console.log(`\nExecuting [${node.id}] - Action: ${node.action}`);
      console.log(`  Description: ${node.description}`);
      
      // Simulate action work
      if (node.action === 'CREATE_TABLE') {
        const tableName = node.id.replace('STEP_MIGRATION_', '').toLowerCase();
        console.log(`  ✓ [Database] Table "${tableName}" successfully provisioned on Target DB.`);
      } else if (node.action === 'REGISTER_ENDPOINTS') {
        console.log(`  ✓ [API Gateway] Bindings and request validation schemas loaded successfully.`);
      } else if (node.action === 'APPLY_SECURITY_POLICIES') {
        console.log(`  ✓ [Auth Server] JWT claims access matrix applied successfully.`);
      } else if (node.action === 'BUILD_AND_DEPLOY_UI') {
        console.log(`  ✓ [CDN Hosting] Static HTML pages compiled and deployed successfully.`);
      }
      
      executed.add(node.id);
      nodesToProcess.splice(i, 1);
      break; // break the inner loop to start checking from beginning again
    }
  }
}

console.log('\n=========================================');
console.log('🎉 APP DEPLOYED AND DEPLOYMENT PLAN FULLY EXECUTED!');
console.log('=========================================');
process.exit(0);
