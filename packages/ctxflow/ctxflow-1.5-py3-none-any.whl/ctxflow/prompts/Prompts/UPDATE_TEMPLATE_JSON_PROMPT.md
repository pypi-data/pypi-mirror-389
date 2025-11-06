# Template JSON Update Prompt

Use this prompt for any new template project to ensure consistent and accurate `template.json` updates.

---

## Prompt

Update the `template.json` file with comprehensive and accurate information about this project. Analyze the codebase to extract all relevant details.

### Requirements

**DO NOT modify these fields:**

- `id`
- `name`
- `category`
- `version`
- `featured`
- `preview.thumbnail`
- `preview.demoUrl`

**DO update these fields:**

1. **`description`**: Write a detailed 2-3 sentence description that includes:
   - The template's primary purpose and theme
   - Key visual/design characteristics
   - Main sections and features (high-level overview)
   - Target audience or ideal use cases

2. **`features`**: Provide a comprehensive list (10-20 items) covering:
   - Responsive design capabilities
   - SEO and accessibility features
   - Design theme and visual characteristics
   - Interactive components (modals, carousels, animations, etc.)
   - Navigation and user experience features
   - Form functionality
   - Typography and font usage
   - Image optimization techniques
   - Any unique or standout features

3. **`techStack`**: List all major technologies and libraries used:
   - Framework and version (e.g., "Next.js 14", "React 18")
   - Language (e.g., "TypeScript")
   - CSS framework (e.g., "Tailwind CSS")
   - Icon libraries (e.g., "Lucide React Icons")
   - Font sources (e.g., "Google Fonts")
   - Any other significant dependencies

4. **`colors`**: Extract and specify the exact hex values for:
   - `primary`: Main background or primary brand color
   - `secondary`: Secondary background or supporting color
   - `accent`: Highlight or call-to-action color

   _Check `tailwind.config.ts` or CSS files for accurate values_

5. **`pages`**: List all pages/routes available in the template
   - For single-page templates, list `["Home"]`
   - For multi-page templates, list all route names

### Example Output Structure

```json
{
  "description": "[Theme] template with [design style]. Features [main sections]. Perfect for [target audience/use cases].",
  "features": [
    "Fully responsive mobile-first design",
    "SEO optimized with [specific approach]",
    "[Design theme] with [color scheme]",
    "[Animation/interaction feature]",
    "[Component 1] with [specific functionality]",
    "[Component 2] with [specific functionality]",
    "...additional features..."
  ],
  "techStack": [
    "[Framework] [version]",
    "[Language]",
    "[CSS framework]",
    "[Icon library]",
    "[Font source]",
    "...additional tech..."
  ],
  "colors": {
    "primary": "#hexcode",
    "secondary": "#hexcode",
    "accent": "#hexcode"
  },
  "pages": ["[Page 1]", "[Page 2]", "..."]
}
```

### Analysis Steps

1. **Read the following files** to gather information:
   - `template.json` (current state)
   - `package.json` (dependencies and tech stack)
   - `tailwind.config.ts` or `tailwind.config.js` (color scheme)
   - `app/layout.tsx` or root layout (metadata, fonts, structure)
   - `app/page.tsx` or main page (sections and components)
   - Component files in `components/` directory (features and functionality)

2. **Extract information**:
   - Theme and design style from component names and styling
   - All interactive features from component code
   - Color values from Tailwind config
   - Tech stack from package.json and import statements
   - Page structure from routing files

3. **Write descriptions**:
   - Use clear, professional language
   - Be specific about functionality, not just generic descriptions
   - Highlight unique or standout features
   - Focus on what makes this template valuable

4. **Verify accuracy**:
   - Ensure all listed features actually exist in the codebase
   - Confirm color hex codes match the Tailwind config
   - Verify tech stack versions match package.json
   - Double-check that preserved fields remain unchanged

### Quality Checklist

- [ ] Description is 2-3 sentences and clearly explains the template's purpose
- [ ] Features list contains 10-20 specific, accurate items
- [ ] Tech stack includes all major dependencies with versions
- [ ] Color hex codes are exact matches from Tailwind config
- [ ] Pages list is complete and accurate
- [ ] All preserved fields remain unchanged
- [ ] JSON is valid and properly formatted
- [ ] Information is factual and based on actual codebase analysis

---

## Usage

Simply provide this prompt to Claude when you need to update `template.json` for a new project:

```
Update the template.json file with comprehensive and accurate information about this project following the UPDATE_TEMPLATE_JSON_PROMPT.md guidelines.
```

Claude will analyze the codebase and update the file consistently and accurately.
