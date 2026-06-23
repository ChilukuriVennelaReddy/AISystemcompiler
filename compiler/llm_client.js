const { env } = require('process');

class LLMClient {
  static async generateJSON(systemInstruction, userPrompt) {
    const geminiKey = env.GEMINI_API_KEY;
    const openaiKey = env.OPENAI_API_KEY;

    if (geminiKey) {
      return await this.callGemini(geminiKey, systemInstruction, userPrompt);
    } else if (openaiKey) {
      return await this.callOpenAI(openaiKey, systemInstruction, userPrompt);
    } else {
      // Fallback to local rule-based matching
      return null;
    }
  }

  static async callGemini(apiKey, systemInstruction, userPrompt) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
    const payload = {
      contents: [{
        parts: [{
          text: `${systemInstruction}\n\nUser Input/Context:\n${userPrompt}`
        }]
      }],
      generationConfig: {
        responseMimeType: "application/json"
      }
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Gemini API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const textResponse = data.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!textResponse) {
        throw new Error('Empty response from Gemini');
      }

      return JSON.parse(textResponse);
    } catch (err) {
      console.warn(`[LLM CLIENT WARNING] Gemini call failed: ${err.message}. Falling back to rule-based engine.`);
      return null;
    }
  }

  static async callOpenAI(apiKey, systemInstruction, userPrompt) {
    const url = 'https://api.openai.com/v1/chat/completions';
    const payload = {
      model: 'gpt-4o-mini',
      response_format: { type: "json_object" },
      messages: [
        { role: 'system', content: systemInstruction },
        { role: 'user', content: userPrompt }
      ]
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`OpenAI API error: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      const content = data.choices?.[0]?.message?.content;
      return JSON.parse(content);
    } catch (err) {
      console.warn(`[LLM CLIENT WARNING] OpenAI call failed: ${err.message}. Falling back to rule-based engine.`);
      return null;
    }
  }
}

module.exports = LLMClient;
