const fs = require('fs');
const path = require('path');

const IntentExtractor = require('./compiler/intent_extractor');
const SystemDesigner = require('./compiler/system_designer');
const SchemaGenerator = require('./compiler/schema_generator');
const Refiner = require('./compiler/refiner');
const RepairEngine = require('./compiler/repair_engine');
const ExecutionSimulator = require('./compiler/execution_simulator');

class AppCompiler {
  constructor() {
    this.intentExtractor = new IntentExtractor();
    this.systemDesigner = new SystemDesigner();
    this.schemaGenerator = new SchemaGenerator();
    this.refiner = new Refiner();
    this.repairEngine = new RepairEngine();
    this.simulator = new ExecutionSimulator();
  }

  async compile(prompt, introduceAnomalies = false) {
    console.log('\n=========================================');
    console.log('🏁 STARTING COMPILATION PIPELINE');
    console.log(`Prompt: "${prompt}"`);
    console.log('=========================================');

    const start = Date.now();

    // Stage 1: Intent Extraction Layer
    console.log('\n[STAGE 1] Lexing and Intent Extraction...');
    const intentIR = await this.intentExtractor.extract(prompt);
    console.log(`  ✓ Domain matched: ${intentIR.domain}`);
    console.log(`  ✓ Roles extracted: [${intentIR.roles.join(', ')}]`);
    console.log(`  ✓ Features extracted: [${intentIR.features.join(', ')}]`);
    if (intentIR.ambiguities && intentIR.ambiguities.length > 0) {
      console.log(`  ⚠ Ambiguities Detected: \n     - ${intentIR.ambiguities.join('\n     - ')}`);
    }

    // Stage 2: System Design Layer
    console.log('\n[STAGE 2] Converting Intent to Architecture IR...');
    const architectureIR = await this.systemDesigner.design(intentIR);
    console.log(`  ✓ Relationships mapped: ${architectureIR.relationshipGraph.length} links`);
    console.log(`  ✓ Routing routes defined: ${architectureIR.routingTopology.routes.length} paths`);

    // Stage 3: Schema Generation Layer
    console.log('\n[STAGE 3] Schema Generation (DB, API, UI, Auth, Rules)...');
    const rawConfig = await this.schemaGenerator.generate(intentIR, architectureIR, introduceAnomalies);
    console.log('  ✓ Initial raw schemas provisioned.');

    // Stage 4: Refinement / Validation Layer
    console.log('\n[STAGE 4] Executing Static Validation Scans...');
    let validationReport = this.refiner.validate(rawConfig);
    let finalConfig = rawConfig;
    let repairLogs = [];

    if (!validationReport.valid) {
      console.log(`  ✗ Validation errors detected: ${validationReport.errors.length} issues.`);
      
      // Stage 5: Targeted Repair Engine
      console.log('\n[STAGE 5] Triggering Targeted Repair Engine...');
      const repairResult = await this.repairEngine.repair(rawConfig, validationReport);
      finalConfig = repairResult.ast;
      repairLogs = repairResult.logs;
      
      console.log('  ✓ Patches applied. Re-running validation...');
      validationReport = this.refiner.validate(finalConfig);
    }

    if (validationReport.valid) {
      console.log('  ✓ Configuration validated: 100% Consistent and Type-Safe.');
    } else {
      console.error('  ✗ Final validation failed. Compilation aborted.');
      return { success: false, errors: validationReport.errors };
    }

    // Stage 6: Execution Plan Generation
    const executionPlan = this.generateExecutionPlan(finalConfig);

    // Assembly of Final Output Document
    const compilationOutput = {
      metadata: {
        compiler_version: 'v1.0.0-prod',
        compilation_time_ms: Date.now() - start,
        timestamp: new Date().toISOString()
      },
      intent_ir: intentIR,
      architecture_ir: architectureIR,
      database_schema: finalConfig.database,
      api_schema: finalConfig.api,
      ui_schema: finalConfig.ui,
      authentication_rules: finalConfig.authentication,
      business_logic_rules: finalConfig.business_logic,
      validation_reports: {
        valid: validationReport.valid,
        errors: validationReport.errors
      },
      repair_reports: {
        total_repairs_needed: repairLogs.length,
        repair_attempts: repairLogs
      },
      assumptions: intentIR.assumptions,
      execution_plans: {
        execution_graph_nodes: executionPlan
      }
    };

    // Save configuration build file to output directory
    const outputDir = path.join(__dirname, 'dist');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir);
    }
    const outputPath = path.join(outputDir, 'app_configuration.json');
    fs.writeFileSync(outputPath, JSON.stringify(compilationOutput, null, 2));
    console.log(`\n✓ Emitter: Compiled output saved to ${outputPath}`);

    // Stage 7: Execution Simulation Check
    const simulationResult = this.simulator.simulate(finalConfig);

    return {
      success: true,
      outputPath,
      compilationOutput,
      simulationResult
    };
  }

  generateExecutionPlan(config) {
    const nodes = [];
    let stepCount = 1;

    // Table migrations
    if (config.database.tables) {
      Object.keys(config.database.tables).forEach(table => {
        nodes.push({
          id: `STEP_${stepCount++}_DB_MIGRATION_${table.toUpperCase()}`,
          action: 'CREATE_TABLE',
          description: `Create database table: "${table}"`,
          depends_on: []
        });
      });
    }

    // API Route register
    if (config.api.endpoints) {
      nodes.push({
        id: `STEP_${stepCount++}_API_GATEWAY_SYNC`,
        action: 'REGISTER_ROUTES',
        description: 'Bind endpoint pathways and request validation schemas',
        depends_on: nodes.map(n => n.id)
      });
    }

    // UI render deploy
    if (config.ui.components) {
      nodes.push({
        id: `STEP_${stepCount++}_UI_FRONTEND_COMPILE`,
        action: 'DEPLOY_VIEWS',
        description: 'Compile layouts and bind state action data-sources',
        depends_on: [`STEP_${stepCount - 2}_API_GATEWAY_SYNC`]
      });
    }

    return nodes;
  }
}

// Support executing directly via node CLI
if (require.main === module) {
  const compiler = new AppCompiler();
  const defaultPrompt = "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.";
  
  const userArgs = process.argv.slice(2);
  const prompt = userArgs[0] || defaultPrompt;
  const triggerRepair = userArgs.includes('--trigger-repair') || userArgs.includes('-r');

  compiler.compile(prompt, triggerRepair).catch(err => {
    console.error('Fatal compilation failure:', err);
    process.exit(1);
  });
}

module.exports = AppCompiler;
