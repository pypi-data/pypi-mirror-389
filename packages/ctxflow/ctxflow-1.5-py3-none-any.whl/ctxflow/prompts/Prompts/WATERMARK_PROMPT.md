# BTY Technology Watermark Implementation Prompt

Use this prompt to add the BTY Technology watermark to any template or website project:

---

Add a fixed watermark component in the bottom-right corner of the website with the following specifications:

**Component Requirements:**

- Create a new component file at `components/Watermark.tsx` (or appropriate path for the project structure)
- Component should be a client component (`'use client'` directive if using Next.js App Router)

**Visual & Functional Specifications:**

- Fixed position: bottom-right corner (bottom-4 right-4)
- High z-index (z-50) to stay on top of other elements
- Dark background (bg-neutral-900) with subtle white border (border-white/5)
- Rounded corners (rounded-xl)
- Padding: p-1 px-2, height: h-10
- Contains BTY Technology logo (use `/btyfavi.svg` or appropriate logo path)
- Logo dimensions: h-5 w-5 with mix-blend-screen
- Text: "Made by BTY Technology" in 11px font, medium weight, neutral-300 color
- Links to: https://btytechnology.com
- Opens in new tab (target="\_blank" rel="noopener noreferrer")
- Smooth transitions (duration-500 with cubic-bezier easing)
- Hover effect: opacity-80 on hover

**Integration:**

- Import the Watermark component in the root layout file (e.g., `app/layout.tsx` or `pages/_app.tsx`)
- Place the component after the Footer and before closing the main providers/wrappers
- Ensure it renders on all pages

**Styling Classes:**

```
Container: fixed bottom-4 right-4 z-50
Inner wrapper: group bg-neutral-900 transition-colors duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] border border-white/5 rounded-xl p-1 px-2 h-10 flex items-center gap-0 shadow-strong overflow-hidden
Link: flex items-center gap-1 hover:opacity-80 transition-opacity
Logo: h-5 w-5 mix-blend-screen
Text: text-[11px] font-medium text-neutral-300 mr-2
```

**Important:**

- Verify the logo file exists at `/btyfavi.svg` in the public directory before implementation
- If using TypeScript, ensure proper typing for the component
- Component should be minimalist with no additional buttons or features
- Match the exact styling and behavior of the reference implementation
