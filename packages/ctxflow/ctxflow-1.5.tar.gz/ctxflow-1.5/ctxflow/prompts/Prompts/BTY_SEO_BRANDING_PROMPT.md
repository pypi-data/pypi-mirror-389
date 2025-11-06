# BTY Technology SEO Branding Implementation

Use this prompt to add BTY Technology branding to SEO metadata for any template or website project:

---

## Task

Update the SEO metadata in the root layout file to include BTY Technology branding consistently across all pages.

## Requirements

### 1. Page Titles

Add `| BTY Technology` suffix to all page titles:

- **Default title**: Append `| BTY Technology` to the existing default title
  - Example: `${companyInfo.name} - ${companyInfo.tagline} | BTY Technology`

- **Title template**: Ensure all dynamic pages include BTY Technology branding
  - Format: `%s | ${companyInfo.name} | BTY Technology`
  - This ensures individual pages follow the pattern: `[Page Name] | [Company Name] | BTY Technology`

### 2. Favicon Configuration

Set all favicon references to use the BTY Technology logo (`/btyfavi.svg`):

```typescript
icons: {
  icon: '/btyfavi.svg',
  shortcut: '/btyfavi.svg',
  apple: '/btyfavi.svg',
},
```

## Implementation Location

- **Next.js App Router**: Update `app/layout.tsx` in the `metadata` export
- **Next.js Pages Router**: Update `pages/_app.tsx` or create/update `pages/_document.tsx`

## Example Implementation

```typescript
export const metadata: Metadata = {
  title: {
    default: `${companyInfo.name} - ${companyInfo.tagline} | BTY Technology`,
    template: `%s | ${companyInfo.name} | BTY Technology`,
  },
  icons: {
    icon: "/btyfavi.svg",
    shortcut: "/btyfavi.svg",
    apple: "/btyfavi.svg",
  },
  // ... rest of metadata
};
```

## Verification Checklist

- [ ] Default title includes `| BTY Technology` suffix
- [ ] Title template includes `| BTY Technology` suffix for dynamic pages
- [ ] All favicon icons reference `/btyfavi.svg`
- [ ] BTY Technology logo file exists at `public/btyfavi.svg`
- [ ] Browser tab displays BTY Technology favicon
- [ ] Page title in browser tab shows BTY Technology branding

## Notes

- Maintain existing company-specific metadata (description, keywords, Open Graph, etc.)
- Only modify title and icons fields
- Ensure `/btyfavi.svg` exists in the public directory before implementation
- Test on multiple pages to verify template is working correctly
