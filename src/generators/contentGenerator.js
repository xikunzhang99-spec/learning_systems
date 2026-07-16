import { createMessage } from '../llm/client.js';
import {
  buildThemeOutlineSystemPrompt, buildThemeOutlineUserPrompt,
  buildSceneSystemPrompt, buildSceneUserPrompt,
  THEME_OUTLINE_ANTHROPIC_TOOL, THEME_OUTLINE_OPENAI_TOOL,
  SCENE_ANTHROPIC_TOOL, SCENE_OPENAI_TOOL,
} from '../llm/prompts.js';
import { validateThemeOutline, validateSceneData } from '../utils/schema.js';
import { config } from '../config.js';

export async function generateTheme(themeName, style) {
  const styleName = style || 'flat design';
  const startTime = Date.now();

  // ===== Phase 1: Generate Theme Outline =====
  console.log(`\nPhase 1/2: Generating story and 5 scene outlines...`);
  const outline = await generateOutline(themeName, styleName);

  console.log(`  Theme: ${outline.themeTitle.en} (${outline.themeTitle.zh})`);
  console.log(`  Story: ${outline.story.en.slice(0, 80)}...`);
  for (const s of outline.scenes) {
    console.log(`  Scene ${s.sceneNumber}: ${s.sceneTitle.en} — ${s.setting}`);
  }

  // ===== Phase 2: Generate All 5 Scenes in Parallel =====
  console.log(`\nPhase 2/2: Generating 5 scenes in parallel...`);
  const startPhase2 = Date.now();

  const scenePromises = outline.scenes.map((sceneOutline, index) =>
    generateOneScene(sceneOutline, themeName, styleName, outline, index)
  );

  const sceneDataList = await Promise.all(scenePromises);

  const phase2Elapsed = ((Date.now() - startPhase2) / 1000).toFixed(1);
  console.log(`  All 5 scenes generated in ${phase2Elapsed}s`);

  const totalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\nTotal generation time: ${totalElapsed}s`);

  return {
    themeTitle: outline.themeTitle,
    story: outline.story,
    style: styleName,
    scenes: sceneDataList,
  };
}

async function generateOutline(themeName, style) {
  const systemPrompt = buildThemeOutlineSystemPrompt(style);
  const userPrompt = buildThemeOutlineUserPrompt(themeName);

  let lastErrors = '';

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    const attemptNum = attempt + 1;
    console.log(`  [Outline ${attemptNum}/${config.maxRetries + 1}] Generating...`);

    try {
      const prompt = attempt === 0
        ? userPrompt
        : `${userPrompt}\n\nPREVIOUS ATTEMPT HAD ERRORS:\n${lastErrors}\n\nFix ALL issues and regenerate.`;

      const data = await createMessage(
        systemPrompt, prompt,
        THEME_OUTLINE_ANTHROPIC_TOOL, THEME_OUTLINE_OPENAI_TOOL
      );

      const { valid, errors } = validateThemeOutline(data);

      if (valid) {
        console.log(`  Outline validation passed.`);
        return data;
      }

      lastErrors = errors.join('; ');
      console.warn(`  Outline validation warnings: ${errors.join(', ')}`);
      if (attempt < config.maxRetries) console.log(`  Retrying...`);

    } catch (err) {
      lastErrors = err.message;
      console.error(`  Outline error: ${err.message}`);
      if (attempt < config.maxRetries) {
        console.log(`  Retrying...`);
        await sleep(1000 * (attempt + 1));
      } else {
        throw err;
      }
    }
  }

  throw new Error(
    `Failed to generate valid theme outline after ${config.maxRetries + 1} attempts.\n` +
    `Last errors: ${lastErrors}`
  );
}

async function generateOneScene(sceneOutline, themeName, style, fullOutline, index) {
  const sceneNum = sceneOutline.sceneNumber;
  const storySummary = fullOutline.story.en.slice(0, 200);
  const themeTitle = fullOutline.themeTitle.en;

  const systemPrompt = buildSceneSystemPrompt(style, themeTitle, storySummary, sceneOutline);
  const userPrompt = buildSceneUserPrompt(sceneOutline, themeName);

  let lastErrors = '';

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    const attemptNum = attempt + 1;
    if (attempt === 0) {
      console.log(`  [Scene ${sceneNum}/5] Generating "${sceneOutline.sceneTitle.en}"...`);
    } else {
      console.log(`  [Scene ${sceneNum}/5] Retry ${attemptNum}/${config.maxRetries + 1}...`);
    }

    try {
      const prompt = attempt === 0
        ? userPrompt
        : `${userPrompt}\n\nPREVIOUS ATTEMPT HAD VALIDATION ERRORS:\n${lastErrors}\n\nFix ALL issues and regenerate.`;

      const data = await createMessage(
        systemPrompt, prompt,
        SCENE_ANTHROPIC_TOOL, SCENE_OPENAI_TOOL
      );

      // Ensure scene number is set
      data.sceneNumber = sceneNum;

      const { valid, errors } = validateSceneData(data);

      if (valid) {
        console.log(`  [Scene ${sceneNum}/5] ✓ "${sceneOutline.sceneTitle.en}" passed validation`);
        return data;
      }

      lastErrors = errors.join('; ');
      console.warn(`  [Scene ${sceneNum}/5] Validation warnings: ${errors.join(', ')}`);
      if (attempt < config.maxRetries) console.log(`  Retrying with error feedback...`);

    } catch (err) {
      lastErrors = err.message;
      console.error(`  [Scene ${sceneNum}/5] Error: ${err.message}`);
      if (attempt < config.maxRetries) {
        console.log(`  Retrying...`);
        await sleep(1000 * (attempt + 1));
      } else {
        throw new Error(`Scene ${sceneNum} failed: ${err.message}`);
      }
    }
  }

  throw new Error(
    `Failed to generate valid scene ${sceneNum} after ${config.maxRetries + 1} attempts.\n` +
    `Last errors: ${lastErrors}`
  );
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
