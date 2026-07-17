import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import { config } from '../config.js';
import { ensureDir, generateFilename } from '../utils/fileUtils.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEMPLATE_PATH = resolve(__dirname, '..', 'templates', 'base.html');

export function assembleTheme(themeData) {
  let html = readFileSync(TEMPLATE_PATH, 'utf-8');

  // Theme title
  html = html.replace('{{THEME_TITLE_EN}}', escapeHTML(themeData.themeTitle.en));
  html = html.replace('{{THEME_TITLE_ZH}}', escapeHTML(themeData.themeTitle.zh));

  // Style
  html = html.replace('{{STYLE_NAME}}', escapeHTML(themeData.style));

  // Story
  html = html.replace('{{STORY_EN}}', escapeHTML(themeData.story.en));
  html = html.replace('{{STORY_ZH}}', escapeHTML(themeData.story.zh));

  // Initial scene SVG (scene 0)
  html = html.replace('{{SCENE_0_SVG}}', themeData.scenes[0].sceneSvg);

  // JSON data injections
  html = html.replace('{{THEME_TITLE_JSON}}', JSON.stringify(themeData.themeTitle));
  html = html.replace('{{THEME_STORY_JSON}}', JSON.stringify(themeData.story));

  // All scenes data as JSON
  html = html.replace('{{SCENES_DATA}}', JSON.stringify(themeData.scenes));

  // Write output
  const filename = generateFilename(`theme-${themeData.themeTitle.en}`);
  const outputPath = resolve(config.outputDir, filename);
  ensureDir(config.outputDir);
  writeFileSync(outputPath, html, 'utf-8');

  return outputPath;
}

function escapeHTML(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
