const LLMClient = require('./llm_client');

class IntentExtractor {
  async extract(prompt) {
    const systemInstruction = `You are the Intent Extraction layer of an NL-to-App Compiler.
Your job is to parse unstructured user prompt requirements into a structured Intent Intermediate Representation (IR) JSON containing:
- domain: string (e.g. CRM, Kanban, E-commerce, Wiki, Classroom)
- entities: array of strings representing entity names (singular, PascalCase, e.g. User, Task, Contact, Product)
- features: array of strings (e.g. Authentication, Payments, Analytics, etc.)
- roles: array of strings representing user roles
- ambiguities: array of strings explaining vague or underspecified requirements
- conflicts: array of strings explaining contradictory requests
- assumptions: array of objects { context: string, assumption: string } mapping choices made to resolve ambiguities.

Output ONLY valid JSON matching this exact structure. Do not include markdown code block wrapping.`;

    const llmResult = await LLMClient.generateJSON(systemInstruction, prompt);
    if (llmResult) {
      llmResult.raw_prompt = prompt;
      return llmResult;
    }

    // --- FALLBACK ENGINE ---
    const text = prompt.toLowerCase();
    let domain = 'General CRUD';
    let entities = ['User'];
    
    if (text.includes('crm') || text.includes('contact') || text.includes('sales')) {
      domain = 'CRM';
      entities = ['User', 'Contact', 'Company', 'Deal', 'Interaction'];
    } else if (text.includes('task') || text.includes('kanban') || text.includes('project') || text.includes('board')) {
      domain = 'Kanban Project Management';
      entities = ['User', 'Workspace', 'Project', 'Task', 'Comment', 'ActivityLog'];
    } else if (text.includes('shop') || text.includes('store') || text.includes('e-commerce') || text.includes('checkout') || text.includes('product')) {
      domain = 'E-commerce';
      entities = ['User', 'Product', 'Order', 'OrderItem', 'Cart', 'Payment'];
    }

    const features = [];
    if (text.includes('login') || text.includes('auth') || text.includes('signup')) features.push('Authentication');
    if (text.includes('payment') || text.includes('premium') || text.includes('billing') || text.includes('stripe')) features.push('Payments');
    if (text.includes('analytics') || text.includes('dashboard') || text.includes('report') || text.includes('chart')) features.push('Analytics Dashboard');
    if (text.includes('notification') || text.includes('email') || text.includes('alert')) features.push('Notifications');

    const roles = [];
    if (text.includes('admin')) roles.push('Admin');
    if (text.includes('member') || text.includes('editor')) roles.push('Member');
    if (text.includes('viewer') || text.includes('guest')) roles.push('Guest');
    if (text.includes('customer') || text.includes('buyer')) roles.push('Customer');
    
    const assumptions = [];
    if (roles.length === 0) {
      roles.push('Admin', 'Member', 'Guest');
      assumptions.push({
        context: 'User Roles',
        assumption: 'No roles specified. Compiler provisioned standard role-based access control (Admin, Member, Guest).'
      });
    }

    const ambiguities = [];
    const conflicts = [];

    if (prompt.length < 20) {
      ambiguities.push('Extremely short prompt. Lacks functional specification.');
      assumptions.push({
        context: 'Scope Limitation',
        assumption: 'The prompt is under 20 characters. Compiling basic single-entity read/write system.'
      });
    }
    
    if (!text.includes('role') && !text.includes('permission') && !text.includes('access')) {
      ambiguities.push('Access control details are underspecified.');
    }

    if (text.includes('guest can edit') && text.includes('guest is read-only')) {
      conflicts.push('Conflicting permissions: Guest is defined as both read-only and having edit rights.');
      assumptions.push({
        context: 'Guest Role Conflict',
        assumption: 'Resolved conflict by restricting Guest role to read-only views for security safety.'
      });
    }

    return {
      domain,
      entities,
      features,
      roles,
      ambiguities,
      conflicts,
      assumptions,
      raw_prompt: prompt
    };
  }
}

module.exports = IntentExtractor;
