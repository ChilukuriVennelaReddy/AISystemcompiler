/**
 * Evaluation Framework
 * Runs the compilation test suites (normal and edge cases) and evaluates performance metrics.
 */
const fs = require('fs');
const path = require('path');
const AppCompiler = require('../compiler');

class Evaluator {
  constructor() {
    this.compiler = new AppCompiler();
  }

  async run() {
    console.log('\n=========================================');
    console.log('🧪 RUNNING COMPILER REGRESSION TEST HARNESS');
    console.log('=========================================');

    const testSetPath = path.join(__dirname, '../test_prompts.json');
    if (!fs.existsSync(testSetPath)) {
      console.error(`✗ Test prompts file not found at ${testSetPath}`);
      process.exit(1);
    }

    const testData = JSON.parse(fs.readFileSync(testSetPath, 'utf8'));
    const allPrompts = [
      ...testData.product_prompts.map(p => ({ ...p, category: 'Standard Product' })),
      ...testData.edge_cases.map(p => ({ ...p, category: 'Edge Case' }))
    ];

    const results = [];
    let totalLatency = 0;
    let successfulCompilations = 0;
    let totalRepairs = 0;

    for (let i = 0; i < allPrompts.length; i++) {
      const testCase = allPrompts[i];
      const isAnomalous = testCase.category === 'Edge Case' || i % 3 === 0;
      const start = Date.now();
      
      // Silence inner consoles to keep eval clean
      const originalLog = console.log;
      const originalWarn = console.warn;
      const originalError = console.error;
      console.log = () => {};
      console.warn = () => {};
      console.error = () => {};

      let result;
      try {
        result = await this.compiler.compile(testCase.prompt, isAnomalous);
      } catch (err) {
        result = { success: false, errors: [err.message] };
      }

      // Restore consoles
      console.log = originalLog;
      console.warn = originalWarn;
      console.error = originalError;

      const duration = Date.now() - start;
      totalLatency += duration;

      const repCount = result.compilationOutput ? result.compilationOutput.repair_reports.total_repairs_needed : 0;
      totalRepairs += repCount;

      if (result.success) {
        successfulCompilations++;
      }

      results.push({
        id: testCase.id,
        category: testCase.category,
        prompt: testCase.prompt.substring(0, 50) + '...',
        success: result.success,
        repairs: repCount,
        latency_ms: duration,
        error_count: r => r.errors ? r.errors.length : 0
      });
    }

    // 1. Output ASCII Table of Runs
    console.log('\n---------------------------------------------------------------------------------------------');
    console.log('| ID  | Category         | Prompt Snippet                                     | Status  | Repairs | Latency |');
    console.log('---------------------------------------------------------------------------------------------');
    results.forEach(r => {
      const status = r.success ? 'PASSED ' : 'FAILED ';
      const repairs = r.repairs.toString().padEnd(7);
      const latency = `${r.latency_ms}ms`.padEnd(7);
      const id = r.id.padEnd(3);
      const cat = r.category.padEnd(16);
      const pmt = r.prompt.padEnd(50);
      console.log(`| ${id} | ${cat} | ${pmt} | ${status} | ${repairs} | ${latency} |`);
    });
    console.log('---------------------------------------------------------------------------------------------');

    // 2. Output Aggregate Metrics
    const successRate = (successfulCompilations / allPrompts.length) * 100;
    const avgLatency = totalLatency / allPrompts.length;
    const avgRepairs = totalRepairs / allPrompts.length;

    console.log('\n=========================================');
    console.log('📊 AGGREGATE EVALUATION REPORT');
    console.log('=========================================');
    console.log(`Total Prompts Compiled:    ${allPrompts.length}`);
    console.log(`Success Rate:              ${successRate.toFixed(1)}% (Pass Target: 95%+)`);
    console.log(`Average Latency:           ${avgLatency.toFixed(1)}ms`);
    console.log(`Average Repairs / Request: ${avgRepairs.toFixed(2)} (Target: < 2.0)`);
    console.log(`Total System Repairs:      ${totalRepairs}`);
    console.log('=========================================\n');
  }
}

if (require.main === module) {
  const evalHarness = new Evaluator();
  evalHarness.run().catch(err => {
    console.error('Fatal evaluation runner failure:', err);
    process.exit(1);
  });
}

module.exports = Evaluator;
