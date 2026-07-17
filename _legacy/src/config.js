import dotenv from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: resolve(__dirname, '..', '.env'), override: true });

export const config = {
  llm: {
    provider: process.env.LLM_PROVIDER || 'anthropic',
    apiKey: process.env.LLM_API_KEY || '',
    baseURL: process.env.LLM_BASE_URL || '',
    model: process.env.LLM_MODEL || '',
    temperature: parseFloat(process.env.LLM_TEMPERATURE || '0.7'),
    maxTokens: parseInt(process.env.LLM_MAX_TOKENS || '8192', 10),
  },
  outputDir: resolve(process.cwd(), 'output'),
  maxRetries: 2,
};

/** Validate required config before making API calls. */
export function requireApiKey() {
  if (!config.llm.apiKey) {
    console.error('ERROR: LLM_API_KEY not found in .env file.');
    console.error('Copy .env.example to .env and fill in your API key:');
    console.error('  LLM_API_KEY=your-key-here');
    process.exit(1);
  }
  if (!config.llm.model) {
    console.error('ERROR: LLM_MODEL not set in .env file.');
    console.error('Set the model ID, e.g.: LLM_MODEL=claude-sonnet-4-6-20250930');
    process.exit(1);
  }
  const valid = ['anthropic', 'openai', 'dashscope', 'deepseek', 'openai-compatible'];
  if (!valid.includes(config.llm.provider)) {
    console.error(`ERROR: Unknown LLM_PROVIDER "${config.llm.provider}".`);
    console.error(`Supported: ${valid.join(', ')}`);
    process.exit(1);
  }
  if (config.llm.provider === 'openai-compatible' && !config.llm.baseURL) {
    console.error('ERROR: LLM_BASE_URL is required when LLM_PROVIDER=openai-compatible.');
    process.exit(1);
  }
}
