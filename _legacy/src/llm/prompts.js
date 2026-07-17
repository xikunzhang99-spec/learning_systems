// ===== Style System =====

const STYLE_PRESETS = {
  'american comic': `AMERICAN COMIC STYLE (美漫风格)
- Modern American comic book illustration with rich details and realistic proportions
- BOLD black outlines on everything: stroke="black" stroke-width="3" to stroke-width="5"
- Dynamic lighting and cinematic composition with dramatic shadows and depth
- Vibrant, saturated colors with bold outlines — similar visual quality to modern Marvel comics and animated TV series
- Highly interactive environment with multiple recognizable objects and rich background details
- Layered depth and perspective with clean object separation for clickable hotspots
- Energetic, professional mood — realistic but stylized characters and settings
- Wide landscape composition (viewBox="0 0 800 600"), 16:9 aspect ratio
- Professional storytelling artwork with original designs, not based on copyrighted characters
- Use <g class="clickable" data-word-id="..."> for interactive elements`,

  'pixel art': `PIXEL ART STYLE (像素风格)
- Modern pixel art inspired by 32-bit RPG game graphics and Stardew Valley
- Blocky, grid-based shapes built from small rectangles with crisp, hard edges
- Use shape-rendering="crispEdges" — no anti-aliasing, no curves
- Rich environmental storytelling with pixel-perfect design
- Cozy, creative, and friendly atmosphere
- Interactive objects clearly visible with layered environment
- Multiple workstations and items creating an educational game atmosphere
- Landscape scene optimized for HTML learning applications
- Bold, readable pixel text for labels
- High-detail pixel artwork with elements snapping to an implied grid`,

  'hand-drawn sketch': `HAND-DRAWN SKETCH STYLE (手绘素描风格)
- Professional architectural sketch aesthetic with pencil drawing and ink outlines
- White paper background — clean notebook aesthetic
- THIN, varied stroke widths: stroke-width="1" to stroke-width="2.5", dark gray (#333 to #555) or black ink
- Every object clearly labeled with annotation lines — educational infographic style
- Minimalist background with high readability suitable for learning
- Academic, organized, and intelligent mood
- Wide composition (viewBox="0 0 800 600") with HTML educational interface ready
- Use subtle hatching/cross-hatching patterns in <defs> for shading and texture
- Hand-drawn imperfections for authentic sketch feel — slightly irregular lines`,

  'cinematic concept art': `CINEMATIC CONCEPT ART STYLE (电影概念设计风格)
- Hollywood concept art quality with ultra-detailed environment
- Photorealistic textures and realistic lighting with soft cinematic feel
- Movie-quality composition with rich environmental storytelling
- Professional workplace settings with multiple interactive objects
- Realistic humans and equipment with natural shadows and depth
- Use feDropShadow and feGaussianBlur for cinematic depth of field effects
- Soft cinematic lighting with natural, gradual shadows
- Professional, modern, and inspiring mood
- 16:9 ratio (viewBox="0 0 800 600"), ultra HD quality
- Semantic <g> layers with clear foreground, midground, background separation`,

  'flat design': `MODERN FLAT ILLUSTRATION STYLE (现代扁平插画风格)
- SaaS product illustration quality with clean vector graphics
- Smooth gradients and minimalist modern design
- Soft blue and purple accent colors on white background
- Rounded corners (rx="8" to rx="16") on all rectangular elements
- Business workspace with multiple interactive elements
- Clean object hierarchy with UI-friendly composition
- Professional, innovative, and efficient mood
- Dashboard-style composition suitable for HTML applications
- 16:9 ratio (viewBox="0 0 800 600")
- Subtle drop shadows for depth: <filter> with feDropShadow, dx="0" dy="2" stdDeviation="3"
- Clean sans-serif typography for labels and signs`,
};

function getStylePrompt(style) {
  const lower = (style || '').toLowerCase().trim();
  // Check preset
  for (const [key, desc] of Object.entries(STYLE_PRESETS)) {
    if (lower.includes(key)) return desc;
  }
  // Custom style — pass through directly
  return `CUSTOM STYLE: ${style}
Apply the following visual style to ALL scene illustrations: ${style}`;
}

// ===== Theme Outline Schema =====

const THEME_OUTLINE_PROPERTIES = {
  themeTitle: {
    type: 'object',
    description: 'Overall theme title in English and Chinese',
    properties: {
      en: { type: 'string', description: 'English theme title' },
      zh: { type: 'string', description: 'Chinese (Simplified) theme title' },
    },
    required: ['en', 'zh'],
  },
  story: {
    type: 'object',
    description: 'A cohesive narrative that connects all 5 scenes into one story',
    properties: {
      en: { type: 'string', description: 'Story in English (4-8 sentences, connecting all scenes)' },
      zh: { type: 'string', description: 'Story in Chinese (Simplified)' },
    },
    required: ['en', 'zh'],
  },
  scenes: {
    type: 'array',
    description: 'Exactly 5 scene outlines that together tell the complete story',
    minItems: 5,
    maxItems: 5,
    items: {
      type: 'object',
      properties: {
        sceneNumber: { type: 'integer', description: 'Scene number 1-5' },
        sceneTitle: {
          type: 'object',
          properties: {
            en: { type: 'string', description: 'English scene title' },
            zh: { type: 'string', description: 'Chinese (Simplified) scene title' },
          },
          required: ['en', 'zh'],
        },
        description: { type: 'string', description: 'What happens in this scene (2-3 sentences in English)' },
        setting: { type: 'string', description: 'Where this scene takes place (e.g., "A sandy beach with umbrellas")' },
        keyElements: {
          type: 'array',
          description: '15-20 key visual elements/objects that MUST appear in this scene (use these for vocabulary)',
          minItems: 15,
          maxItems: 20,
          items: { type: 'string' },
        },
      },
      required: ['sceneNumber', 'sceneTitle', 'description', 'setting', 'keyElements'],
    },
  },
};

const THEME_OUTLINE_TOOL_NAME = 'output_theme_outline';
const THEME_OUTLINE_TOOL_DESCRIPTION = 'Output the theme story and 5 scene outlines.';

export const THEME_OUTLINE_ANTHROPIC_TOOL = {
  name: THEME_OUTLINE_TOOL_NAME,
  description: THEME_OUTLINE_TOOL_DESCRIPTION,
  input_schema: {
    type: 'object',
    properties: THEME_OUTLINE_PROPERTIES,
    required: ['themeTitle', 'story', 'scenes'],
  },
};

export const THEME_OUTLINE_OPENAI_TOOL = {
  type: 'function',
  function: {
    name: THEME_OUTLINE_TOOL_NAME,
    description: THEME_OUTLINE_TOOL_DESCRIPTION,
    parameters: {
      type: 'object',
      properties: THEME_OUTLINE_PROPERTIES,
      required: ['themeTitle', 'story', 'scenes'],
    },
  },
};

// ===== Scene Content Schema (per scene) =====

const SCENE_PROPERTIES = {
  sceneTitle: {
    type: 'object',
    description: 'Scene title in English and Chinese',
    properties: {
      en: { type: 'string', description: 'English title' },
      zh: { type: 'string', description: 'Chinese (Simplified) title' },
    },
    required: ['en', 'zh'],
  },
  sceneSvg: {
    type: 'string',
    description: 'COMPLETE SVG markup as a string. viewBox="0 0 800 600". Follow the specified art style EXACTLY. Include <defs> with relevant filters/patterns for the style. Use semantic <g> layers (background, midground, foreground, labels). Include 10-15 clickable elements with <g class="clickable" data-word-id="...">. Each data-word-id MUST EXACTLY MATCH a vocabulary word. Include English labels/signs where natural. The scene should feel like a complete illustration, not a diagram.',
  },
  vocabulary: {
    type: 'array',
    description: 'Exactly 20 vocabulary words: 6 easy (CEFR A1-A2) + 6 medium (CEFR B1) + 8 hard (CEFR B2+). ALL words MUST be NOUNS (concrete things/objects/people visible in this scene).',
    minItems: 20,
    maxItems: 20,
    items: {
      type: 'object',
      properties: {
        word: { type: 'string', description: 'English NOUN (lowercase, singular). Must be a concrete thing visible in this scene.' },
        chinese: { type: 'string', description: 'Chinese (Simplified) translation' },
        pos: { type: 'string', enum: ['noun'] },
        difficulty: { type: 'string', enum: ['easy', 'medium', 'hard'] },
        examples: {
          type: 'array',
          description: 'At least 2 example sentences using this word naturally in context',
          minItems: 2,
          maxItems: 3,
          items: {
            type: 'object',
            properties: {
              en: { type: 'string', description: 'Natural English sentence' },
              zh: { type: 'string', description: 'Chinese translation' },
            },
            required: ['en', 'zh'],
          },
        },
      },
      required: ['word', 'chinese', 'pos', 'difficulty', 'examples'],
    },
  },
  actionVerbs: {
    type: 'array',
    description: '8-12 verb phrases describing actions visible in this scene',
    minItems: 8,
    maxItems: 12,
    items: {
      type: 'object',
      properties: {
        verb: { type: 'string', description: 'Verb phrase (verb + object/complement, e.g., "build a sandcastle", NOT just "build")' },
        chinese: { type: 'string' },
        presentParticiple: { type: 'string', description: '-ing form (e.g., "building a sandcastle")' },
        pastTense: { type: 'string', description: 'Past tense form (e.g., "built a sandcastle")' },
        examples: {
          type: 'array',
          description: 'At least 2 example sentences using this verb phrase',
          minItems: 2,
          maxItems: 3,
          items: {
            type: 'object',
            properties: {
              en: { type: 'string', description: 'Natural English sentence' },
              zh: { type: 'string', description: 'Chinese translation' },
            },
            required: ['en', 'zh'],
          },
        },
      },
      required: ['verb', 'chinese', 'presentParticiple', 'pastTense', 'examples'],
    },
  },
  expressions: {
    type: 'array',
    description: '12-15 common English expressions or sentences for this scene',
    minItems: 12,
    maxItems: 15,
    items: {
      type: 'object',
      properties: {
        english: { type: 'string' },
        chinese: { type: 'string' },
        context: { type: 'string', description: 'Brief note on when to use this expression' },
      },
      required: ['english', 'chinese', 'context'],
    },
  },
  colorPalette: {
    type: 'object',
    description: 'Four hex colors for this scene',
    properties: {
      primary: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
      secondary: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
      accent: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
      background: { type: 'string', pattern: '^#[0-9A-Fa-f]{6}$' },
    },
    required: ['primary', 'secondary', 'accent', 'background'],
  },
};

const SCENE_TOOL_NAME = 'output_scene_content';
const SCENE_TOOL_DESCRIPTION = 'Output complete interactive scene data including SVG, vocabulary, verbs, expressions, and color palette.';

export const SCENE_ANTHROPIC_TOOL = {
  name: SCENE_TOOL_NAME,
  description: SCENE_TOOL_DESCRIPTION,
  input_schema: {
    type: 'object',
    properties: SCENE_PROPERTIES,
    required: ['sceneTitle', 'sceneSvg', 'vocabulary', 'actionVerbs', 'expressions', 'colorPalette'],
  },
};

export const SCENE_OPENAI_TOOL = {
  type: 'function',
  function: {
    name: SCENE_TOOL_NAME,
    description: SCENE_TOOL_DESCRIPTION,
    parameters: {
      type: 'object',
      properties: SCENE_PROPERTIES,
      required: ['sceneTitle', 'sceneSvg', 'vocabulary', 'actionVerbs', 'expressions', 'colorPalette'],
    },
  },
};

// ===== System Prompts =====

export function buildThemeOutlineSystemPrompt(style) {
  const styleDesc = getStylePrompt(style);

  return `You are a creative English teacher and story designer. You create engaging theme-based stories for Chinese speakers learning English.

## YOUR TASK
Given a theme name, create a cohesive story and outline 5 scenes that tell that story visually. Each scene will later become an interactive English-learning illustration. Output ONLY by calling the ${THEME_OUTLINE_TOOL_NAME} function. Do not output any other text.

## STORY REQUIREMENTS
- Create a simple, engaging narrative (4-8 sentences) that flows naturally through 5 visual scenes
- The story should feature 1-2 main characters doing activities related to the theme
- Each scene should be a distinct "moment" in the story with a clear setting and action
- Scenes should progress logically (beginning → middle → end, or step-by-step through an experience)
- The story should naturally introduce 15-20 concrete nouns per scene

## SCENE OUTLINE REQUIREMENTS
- Each of the 5 scenes needs: title (en/zh), description, setting, and 15-20 key visual elements
- Key elements MUST be concrete nouns (objects, people, things) visible in that scene
- These key elements become the vocabulary words — choose a mix of easy and advanced nouns
- Scene settings should be visually rich and varied enough to support an illustration
- Each scene's description should make clear what action/activity is happening

## STYLE CONTEXT
The illustrations will use this style: ${styleDesc}`;
}

export function buildThemeOutlineUserPrompt(themeName) {
  return `Create a 5-scene English-learning theme for: **"${themeName}"**

Please:
1. Give this theme an appropriate English and Chinese title
2. Write a simple, engaging story (in both English and Chinese) that connects all 5 scenes
3. Outline 5 scenes that together tell this visual story
4. For each scene, provide:
   - A scene title (en/zh)
   - A description of what happens
   - The specific setting/location
   - 15-20 key concrete nouns/objects that should appear in the illustration

The scenes should progress naturally like pages in a picture book. Make each scene visually distinct with different compositions and focal activities.

Generate the complete outline by calling the ${THEME_OUTLINE_TOOL_NAME} function.`;
}

export function buildSceneSystemPrompt(style, themeTitle, storySummary, sceneOutline) {
  const styleDesc = getStylePrompt(style);

  return `You are a professional illustrator and English teacher. You create interactive SVG illustrations that help Chinese speakers learn English.

## YOUR TASK
Generate ONE interactive English-learning scene. Output ONLY by calling the ${SCENE_TOOL_NAME} function. Do not output any other text.

## THEME CONTEXT
Theme: "${themeTitle}"
Story: ${storySummary}
This scene: Scene #${sceneOutline.sceneNumber} — "${sceneOutline.sceneTitle.en}" (${sceneOutline.sceneTitle.zh})
Setting: ${sceneOutline.setting}
What happens: ${sceneOutline.description}
Key elements to include: ${sceneOutline.keyElements.join(', ')}

## ART STYLE
${styleDesc}

## SVG TECHNICAL REQUIREMENTS
- viewBox="0 0 800 600"
- <defs> with style-appropriate filters/patterns
- Semantic <g> layers: id="background", id="midground", id="foreground", id="labels"
- Each interactive element: <g class="clickable" data-word-id="word_here">
- CRITICAL: data-word-id MUST EXACTLY MATCH a "word" field in the vocabulary array (character-by-character, lowercase, singular form). If a word is "sunscreen", use data-word-id="sunscreen", NOT "sunscreens" or "sunscreen bottle".
- 10-15 clickable elements total, spread across different layers
- Before outputting, verify EVERY data-word-id has a matching vocabulary word
- Include English text labels/signs where natural in the scene
- The illustration should feel complete and polished, not like a rough sketch

## EDUCATIONAL CONTENT RULES

### Vocabulary (20 words: EXACTLY 6 easy + 6 medium + 8 hard)
- ALL 20 words MUST be NOUNS (concrete things, objects, people visible in the scene)
- Easy (CEFR A1-A2): Common everyday nouns, 6 words
- Medium (CEFR B1): Moderately common nouns, 6 words
- Hard (CEFR B2+): Specific, less common nouns, 8 words
- Every data-word-id in the SVG MUST match a "word" field here character-for-character
- Each word MUST have at least 2 example sentences (en + zh)

### Action Verbs (8-12 verb phrases)
- Each "verb" MUST be a VERB PHRASE (verb + object/complement), NOT a single word
- Good: "apply sunscreen", "ride a wave", "collect seashells"
- Bad: "apply", "ride", "collect"
- Each verb phrase MUST have at least 2 example sentences (en + zh)

### Expressions (12-15)
- Common, natural English expressions/sentences for this specific scene
- Include chinese translation and usage context

### Translation Quality
- Accurate Simplified Chinese (简体中文)
- Natural, idiomatic sentences in BOTH languages`;
}

export function buildSceneUserPrompt(sceneOutline, themeName) {
  return `Create the interactive English-learning scene for:
Theme: "${themeName}"
Scene ${sceneOutline.sceneNumber}: "${sceneOutline.sceneTitle.en}" (${sceneOutline.sceneTitle.zh})
Setting: ${sceneOutline.setting}
Description: ${sceneOutline.description}
Key elements to visualize: ${sceneOutline.keyElements.join(', ')}

Generate the complete scene by calling the ${SCENE_TOOL_NAME} function.

IMPORTANT:
- All 20 vocabulary words MUST be concrete NOUNS visible in this scene
- EXACTLY 6 easy + 6 medium + 8 hard words
- Every data-word-id MUST match a vocabulary word exactly
- Each word needs 2+ example sentences
- 8-12 verb phrases with 2+ examples each
- 12-15 expressions
- Follow the specified art style precisely`;
}
