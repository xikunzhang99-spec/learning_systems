#!/usr/bin/env node
import { requireApiKey } from './config.js';
import { generateTheme } from './generators/contentGenerator.js';
import { assembleTheme } from './generators/htmlAssembler.js';

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    showHelp();
    return;
  }

  // Parse --theme / -t
  let themeName = '';
  const themeArgIdx = args.indexOf('--theme') !== -1 ? args.indexOf('--theme') : args.indexOf('-t');
  if (themeArgIdx !== -1 && args[themeArgIdx + 1]) {
    themeName = args[themeArgIdx + 1];
  }

  if (!themeName) {
    console.error('ERROR: Please provide a theme name with --theme.\n');
    showHelp();
    process.exit(1);
  }

  // Parse --style / -s (optional)
  let style = 'flat design';
  const styleArgIdx = args.indexOf('--style') !== -1 ? args.indexOf('--style') : args.indexOf('-s');
  if (styleArgIdx !== -1 && args[styleArgIdx + 1]) {
    style = args[styleArgIdx + 1];
  }

  console.log(`Theme: "${themeName}"`);
  console.log(`Style: ${style}`);
  console.log(`\nGenerating interactive English learning theme with 5 scenes...`);
  console.log(`This may take 1-3 minutes depending on the API.\n`);

  requireApiKey();

  const startTime = Date.now();

  try {
    const themeData = await generateTheme(themeName, style);
    const outputPath = assembleTheme(themeData);
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`\nDone in ${elapsed}s!`);
    console.log(`Output: ${outputPath}`);
    console.log(`\nOpen this file in your browser to start learning!`);
    console.log(`在浏览器中打开此文件即可开始学习！`);
    console.log(`Use Ctrl+Arrow to switch scenes | 使用 Ctrl+方向键切换场景`);
  } catch (err) {
    console.error(`\nGeneration failed: ${err.message}`);
    console.error(`\nTips:`);
    console.error(`  - Check your .env file has a valid LLM_API_KEY`);
    console.error(`  - Try a different theme name`);
    console.error(`  - Check your network connection`);
    process.exit(1);
  }
}

function showHelp() {
  console.log(`
English Learning Theme Generator / 英语学习主题场景生成器

Generates an interactive HTML page with 5 connected story scenes for English learning.
Each scene contains clickable SVG illustrations, vocabulary, verb phrases, and expressions.

USAGE:
  node src/index.js --theme <name> [--style <style>]

OPTIONS:
  --theme, -t <name>   Theme name (required). E.g., "A Day at the Beach", "太空探险"
  --style, -s <style>  Visual style (optional, defaults to "flat design")
                        Presets: flat design, american comic, pixel art, hand-drawn sketch, cinematic concept art
                        Or any custom style description: "纸雕风格", "水彩+铅笔素描"
  --help, -h           Show this help message

EXAMPLES:
  node src/index.js --theme "A Day at the Beach"
  node src/index.js --theme "海滩的一天"
  node src/index.js --theme "Space Adventure" --style "american comic"
  node src/index.js --theme "森林探险" --style "水彩风格"
  node src/index.js --theme "City Tour" --style "pixel art"
  npm run generate -- --theme "Restaurant Experience"

ENVIRONMENT (set in .env):
  LLM_PROVIDER          AI provider (anthropic, openai, dashscope, deepseek, openai-compatible)
  LLM_API_KEY            Your API key
  LLM_BASE_URL           Custom API endpoint (optional)
  LLM_MODEL              Model ID (e.g., deepseek-chat, claude-sonnet-4-6-20250930)
  LLM_MAX_TOKENS         Max tokens per request

After generation, open the output HTML file in your browser.
生成后在浏览器中打开输出的 HTML 文件即可。
`);
}

main().catch(err => {
  console.error('Fatal error:', err.message);
  process.exit(1);
});
