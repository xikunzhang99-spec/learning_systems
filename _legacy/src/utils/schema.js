export function validateThemeOutline(data) {
  const errors = [];

  if (!data.themeTitle?.en || !data.themeTitle?.zh) {
    errors.push('themeTitle missing en or zh');
  }
  if (!data.story?.en || !data.story?.zh) {
    errors.push('story missing en or zh');
  }

  if (!Array.isArray(data.scenes) || data.scenes.length !== 5) {
    errors.push(`scenes must have exactly 5 items, got ${data.scenes?.length}`);
  } else {
    for (let i = 0; i < data.scenes.length; i++) {
      const s = data.scenes[i];
      if (!s.sceneTitle?.en || !s.sceneTitle?.zh) {
        errors.push(`scenes[${i}] missing sceneTitle en/zh`);
      }
      if (!s.description) {
        errors.push(`scenes[${i}] missing description`);
      }
      if (!s.setting) {
        errors.push(`scenes[${i}] missing setting`);
      }
      if (!Array.isArray(s.keyElements) || s.keyElements.length < 15 || s.keyElements.length > 20) {
        errors.push(`scenes[${i}] keyElements must have 15-20 items, got ${s.keyElements?.length}`);
      }
      if (s.sceneNumber !== i + 1) {
        errors.push(`scenes[${i}] sceneNumber should be ${i + 1}, got ${s.sceneNumber}`);
      }
    }
  }

  return { valid: errors.length === 0, errors };
}

export function validateSceneData(data) {
  const errors = [];

  // SVG
  if (!data.sceneSvg || !data.sceneSvg.includes('<svg')) {
    errors.push('sceneSvg is missing or does not contain <svg> tag');
  }
  if (!data.sceneSvg || !data.sceneSvg.includes('data-word-id=')) {
    errors.push('sceneSvg must contain clickable elements with data-word-id attributes');
  }
  if (!data.sceneSvg || !data.sceneSvg.includes('viewBox')) {
    errors.push('sceneSvg must include a viewBox attribute');
  }

  // Vocabulary: 20 words, 6 easy + 6 medium + 8 hard
  if (!Array.isArray(data.vocabulary) || data.vocabulary.length !== 20) {
    errors.push(`vocabulary must have exactly 20 items, got ${data.vocabulary?.length}`);
  } else {
    const easyCount = data.vocabulary.filter(v => v.difficulty === 'easy').length;
    const mediumCount = data.vocabulary.filter(v => v.difficulty === 'medium').length;
    const hardCount = data.vocabulary.filter(v => v.difficulty === 'hard').length;

    if (easyCount !== 6) {
      errors.push(`vocabulary must have exactly 6 easy words, got ${easyCount}`);
    }
    if (mediumCount !== 6) {
      errors.push(`vocabulary must have exactly 6 medium words, got ${mediumCount}`);
    }
    if (hardCount !== 8) {
      errors.push(`vocabulary must have exactly 8 hard words, got ${hardCount}`);
    }

    const words = data.vocabulary.map(v => v.word?.toLowerCase());
    if (new Set(words).size !== words.length) {
      errors.push('vocabulary contains duplicate words');
    }

    for (let i = 0; i < data.vocabulary.length; i++) {
      const v = data.vocabulary[i];
      if (!v.word || !v.chinese || !v.pos || !v.difficulty) {
        errors.push(`vocabulary[${i}] missing required fields`);
      }
      if (!Array.isArray(v.examples) || v.examples.length < 2) {
        errors.push(`vocabulary[${i}] ("${v.word}") must have at least 2 examples, got ${v.examples?.length}`);
      } else {
        for (let j = 0; j < v.examples.length; j++) {
          if (!v.examples[j].en || !v.examples[j].zh) {
            errors.push(`vocabulary[${i}] example[${j}] missing en or zh`);
          }
        }
      }
    }
  }

  // Action Verbs: 8-12
  if (!Array.isArray(data.actionVerbs) || data.actionVerbs.length < 8 || data.actionVerbs.length > 12) {
    errors.push(`actionVerbs must have 8-12 items, got ${data.actionVerbs?.length}`);
  } else {
    for (let i = 0; i < data.actionVerbs.length; i++) {
      const v = data.actionVerbs[i];
      if (!v.verb || !v.chinese || !v.presentParticiple || !v.pastTense) {
        errors.push(`actionVerbs[${i}] missing required fields`);
      }
      if (!Array.isArray(v.examples) || v.examples.length < 2) {
        errors.push(`actionVerbs[${i}] ("${v.verb}") must have at least 2 examples, got ${v.examples?.length}`);
      } else {
        for (let j = 0; j < v.examples.length; j++) {
          if (!v.examples[j].en || !v.examples[j].zh) {
            errors.push(`actionVerbs[${i}] example[${j}] missing en or zh`);
          }
        }
      }
    }
  }

  // Expressions: 12-15
  if (!Array.isArray(data.expressions) || data.expressions.length < 12 || data.expressions.length > 15) {
    errors.push(`expressions must have 12-15 items, got ${data.expressions?.length}`);
  } else {
    for (let i = 0; i < data.expressions.length; i++) {
      const e = data.expressions[i];
      if (!e.english || !e.chinese || !e.context) {
        errors.push(`expressions[${i}] missing required fields`);
      }
    }
  }

  // Color Palette
  if (!data.colorPalette?.primary || !data.colorPalette?.secondary
      || !data.colorPalette?.accent || !data.colorPalette?.background) {
    errors.push('colorPalette missing required fields');
  }

  // Scene title
  if (!data.sceneTitle?.en) {
    errors.push('sceneTitle missing en');
  }

  return { valid: errors.length === 0, errors };
}
