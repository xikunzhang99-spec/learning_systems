import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';
import { config } from '../config.js';

// ===== Provider-specific base URL defaults =====
const PROVIDER_BASE_URLS = {
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  deepseek: 'https://api.deepseek.com/v1',
};

function resolveBaseURL() {
  if (config.llm.baseURL) return config.llm.baseURL;
  return PROVIDER_BASE_URLS[config.llm.provider] || '';
}

// ===== Lazy-initialized clients =====
let _anthropicClient = null;
let _openaiClient = null;

function getAnthropicClient() {
  if (!_anthropicClient) {
    const opts = { apiKey: config.llm.apiKey };
    const baseURL = resolveBaseURL();
    if (baseURL) opts.baseURL = baseURL;
    _anthropicClient = new Anthropic(opts);
  }
  return _anthropicClient;
}

function getOpenAIClient() {
  if (!_openaiClient) {
    const opts = { apiKey: config.llm.apiKey };
    const baseURL = resolveBaseURL();
    if (baseURL) opts.baseURL = baseURL;
    _openaiClient = new OpenAI(opts);
  }
  return _openaiClient;
}

// ===== Main API: provider-agnostic message creation =====

/**
 * Send a prompt with tool-based structured output.
 * Returns the parsed JSON from the tool call — same shape regardless of provider.
 *
 * @param {string} systemPrompt
 * @param {string} userPrompt
 * @param {object} anthropicTool  - Tool definition in Anthropic format
 * @param {object} openaiTool     - Tool definition in OpenAI format
 * @returns {Promise<object>} Parsed JSON from the tool call
 */
export async function createMessage(systemPrompt, userPrompt, anthropicTool, openaiTool) {
  if (config.llm.provider === 'anthropic') {
    return callAnthropic(systemPrompt, userPrompt, anthropicTool);
  }
  return callOpenAICompatible(systemPrompt, userPrompt, openaiTool);
}

// ===== Anthropic (native SDK) =====

async function callAnthropic(systemPrompt, userPrompt, tool) {
  const client = getAnthropicClient();
  const response = await client.messages.create({
    model: config.llm.model,
    max_tokens: config.llm.maxTokens,
    temperature: config.llm.temperature,
    system: systemPrompt,
    messages: [{ role: 'user', content: userPrompt }],
    tools: [tool],
    tool_choice: { type: 'tool', name: tool.name },
  });

  for (const block of response.content) {
    if (block.type === 'tool_use' && block.name === tool.name) {
      return block.input;
    }
  }

  throw new Error('Model did not call the expected tool. Response did not contain a tool_use block.');
}

// ===== OpenAI-compatible (DashScope / DeepSeek / OpenAI / custom) =====

async function callOpenAICompatible(systemPrompt, userPrompt, tool) {
  const client = getOpenAIClient();
  const response = await client.chat.completions.create({
    model: config.llm.model,
    max_tokens: config.llm.maxTokens,
    temperature: config.llm.temperature,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    tools: [tool],
    tool_choice: 'auto',
  });

  const choice = response.choices?.[0];
  if (!choice) {
    throw new Error('Model returned empty response.');
  }

  const toolCall = choice.message?.tool_calls?.[0];
  if (!toolCall || toolCall.function?.name !== tool.function.name) {
    throw new Error('Model did not call the expected tool. No matching tool_call in response.');
  }

  const rawArgs = toolCall.function.arguments;
  try {
    return JSON.parse(rawArgs);
  } catch (err) {
    // Debug: log the raw arguments to help diagnose truncation issues
    console.error(`\n[DEBUG] Raw tool call arguments length: ${rawArgs.length} chars`);
    console.error(`[DEBUG] First 500 chars: ${rawArgs.slice(0, 500)}`);
    console.error(`[DEBUG] Last 500 chars: ${rawArgs.slice(-500)}`);
    throw new Error(`Failed to parse tool call arguments as JSON: ${err.message}`);
  }
}
