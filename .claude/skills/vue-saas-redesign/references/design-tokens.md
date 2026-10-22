# Design tokens

Define these once on `:root` in the app's global stylesheet and reference them everywhere. Adapt the values to the app's existing brand colors before inventing new ones: map the app's current primary, text and border colors onto these names rather than replacing them.

## Contents
- Color
- Spacing
- Typography
- Radius and shadow
- Layout constants
- Dark mode

## Color

Neutral surfaces do most of the work; one accent marks primary actions and the active nav item; status colors mean status.

```css
:root {
  /* Surfaces */
  --color-bg: #f8fafc;            /* app background behind cards */
  --color-surface: #ffffff;       /* cards, tables, popovers */
  --color-surface-muted: #f1f5f9; /* table headers, hover rows, inputs at rest */
  --color-sidebar-bg: #0f172a;    /* or a light surface; see note below */
  --color-sidebar-text: #cbd5e1;
  --color-sidebar-text-active: #ffffff;
  --color-sidebar-hover: rgba(255, 255, 255, 0.06);
  --color-sidebar-active: rgba(255, 255, 255, 0.12);

  /* Text */
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-text-subtle: #94a3b8;

  /* Lines */
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;

  /* Accent */
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-soft: #eff6ff;   /* tinted backgrounds for selected rows, light active nav */
  --color-focus-ring: rgba(37, 99, 235, 0.4);

  /* Status */
  --color-success: #16a34a;
  --color-info: #2563eb;
  --color-warning: #ca8a04;
  --color-danger: #dc2626;
}
```

A dark sidebar on a light content area is the common SaaS look and gives the shell a clear anchor. A light sidebar with a border is the quieter alternative. Offer both when the user hasn't decided; the tokens above make switching one block of variables.

Check contrast: muted text on the page background and sidebar text on the sidebar background must both reach 4.5:1.

## Spacing

4px base. Use only these.

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
}
```

Conventions: card padding `--space-5` or `--space-6`; gap between cards `--space-4` or `--space-6`; page padding `--space-6` on desktop and `--space-4` on phones; gap between a label and its control `--space-2`.

## Typography

```css
:root {
  --font-sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --text-xs: 12px;    /* captions, badges, table headers (uppercase optional) */
  --text-sm: 13px;    /* table cells, secondary text */
  --text-base: 14px;  /* body */
  --text-md: 16px;    /* card titles */
  --text-lg: 20px;    /* section headings */
  --text-xl: 26px;    /* page titles */
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --leading-tight: 1.25;
  --leading-normal: 1.5;
}
```

Only use fonts that are already loaded or are system fonts; adding a web font is a dependency decision to raise with the user.

## Radius and shadow

```css
:root {
  --radius-sm: 6px;   /* inputs, buttons, badges */
  --radius-md: 10px;  /* cards, popovers */
  --radius-lg: 14px;  /* modals */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.14);
}
```

Cards use a 1px `--color-border` plus `--shadow-sm`. Reserve `--shadow-lg` for modals and menus.

## Layout constants

```css
:root {
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 56px;
  --content-max-width: 1280px;
}
```

## Dark mode

Only add this when the app already has dark mode or the user asks. Redefine the same variable names under `@media (prefers-color-scheme: dark)` and under an explicit `[data-theme="dark"]` selector so a manual toggle can win; never branch on theme inside components.
