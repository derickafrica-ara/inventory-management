---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical sidebar navigation on the left instead of a top nav bar, a consistent spacing and type scale, shared design tokens, and a polished professional look. Use this skill whenever the user wants to modernize, restyle, reskin or "make professional" a Vue app, replace a top navigation bar with a sidebar or left rail, build an admin or dashboard shell, or introduce design tokens and consistent spacing, even if they never say "SaaS" or "sidebar".
---

# Vue 3 SaaS-style redesign

Turn an existing Vue 3 app into a modern SaaS interface: a left sidebar for navigation, a content area with a consistent page header, and one set of design tokens that every view draws from. The app's behavior stays exactly as it is. This is a visual and layout change, so any redesign that alters data flow, routes or business logic has gone too far.

The workflow is **discover, propose, confirm, apply, verify**. Skipping the confirm step is the most common way this goes wrong: a redesign touches every screen, and the user's taste decides whether it landed, so get agreement on the direction before rewriting files.

## 1. Discover (read-only)

Learn the app before judging it. Read, in this order:

- `package.json` (Vue version, router, UI libraries, build tool, any CSS framework), and the project's `CLAUDE.md` or contribution notes. Project rules win over this skill: if it says "no emojis", "use this color palette", or "delegate .vue edits to a specific agent", follow that.
- The router setup (usually `main.js` or `router/`): the route list is the sidebar's menu.
- The app shell (usually `App.vue`): the current top nav, header widgets (language switcher, profile menu, search, notifications), global filters, modals mounted at the root.
- Where global CSS lives (an unscoped `<style>` in `App.vue`, `style.css`, `assets/`), and what shared classes views already use (`.card`, `.badge`, `.table-container`, ...). Restyling those shared classes restyles every view at once, which is far cheaper and safer than editing each view.
- Two or three views of different shape (a dashboard, a table page, a form) to see how much styling is local versus shared.
- Whether the app has i18n, dark mode, or currency/locale formatting. Navigation labels must keep going through the same i18n function.

Also run `git status`. Start from a clean tree on a feature branch so the redesign is one reviewable diff the user can discard.

Write down what you found as short notes. You need them for the proposal.

## 2. Propose

Present a short proposal before touching code. Keep it to what the user needs to decide:

- **Layout**: sidebar width (about 240-264px expanded), what goes in it (brand at top, nav items, optional user/profile block at the bottom), and where the header widgets move (typically a slim top bar inside the content area, or the sidebar footer). Say where global filters go. Filters that apply to every page usually sit in a toolbar directly above the page content.
- **Navigation map**: the existing routes as sidebar items, in the existing order unless there's a clear reason, with their current i18n keys. Note any hard-coded labels you will have to leave or fix.
- **Tokens**: the palette, type scale, spacing scale, radii and shadows you'll define (see `references/design-tokens.md`). Reuse the app's existing brand colors first; invent new ones only to fill gaps.
- **Scope**: which files change (shell, global CSS, which views), and what you will not touch.
- **Responsive behavior**: below about 768px the sidebar becomes an off-canvas drawer opened from a menu button.

Then ask the user to confirm or adjust, using the AskUserQuestion tool when it is available. Offer real alternatives for the decisions that are matters of taste (for example, collapsible icon-only rail versus always-expanded; light only versus light and dark), and recommend one. If the user asked only for the audit and proposal, stop here.

## 3. Apply

Work from the outside in, because each layer makes the next one smaller.

1. **Tokens first.** Add the design tokens as CSS custom properties on `:root` in the app's global stylesheet (`references/design-tokens.md`). Nothing should look different yet.
2. **Shell.** Build the sidebar layout (`references/sidebar-shell.md` has a working skeleton): a two-column grid with a fixed-width sidebar and a scrolling main column. Drive the nav items from a plain array of `{ to, labelKey, icon }` so adding a route is one line. Use `router-link` with its active class for the current-page state and add `aria-current="page"`. Move existing header widgets rather than rewriting them; keep their components, props and events intact.
3. **Shared primitives.** Restyle the classes views already share (cards, tables, buttons, badges, inputs, stat tiles, empty and loading states) using tokens. This is where most of the "polish" comes from.
4. **Page header pattern.** Give every page the same title, description and optional actions block, so spacing and hierarchy are identical from page to page.
5. **Views.** Only touch a view when it hard-codes values that fight the system (pixel margins, one-off colors, its own container width). Replace those with tokens. Leave scripts, templates' logic and data loading alone.
6. **Modals and popovers.** Check that they still layer correctly over the new shell (z-index and positioning), since a fixed sidebar changes stacking.

Rules that keep the result professional rather than merely different:

- One spacing scale on a 4px base. Every margin, padding and gap comes from it. If a value is not on the scale, that is usually a bug.
- Limited type scale (about 6 sizes) with consistent weights; body text 14-15px, tables slightly smaller, page titles 22-28px.
- Low-contrast borders and soft, small shadows instead of heavy ones. Cards get one radius, controls another, and both come from tokens.
- Color carries meaning. Neutral surfaces, one accent for primary actions and the active nav item, and status colors (green, blue, yellow, red) reserved for status.
- Every interactive element has a visible hover and a visible keyboard focus ring. Text contrast meets WCAG AA (4.5:1).
- Icons: inline SVG, 16-20px, one stroke width. Do not add an icon library or any other dependency without asking. Do not use emojis as icons.
- Do not leave dead code: delete the old top-nav markup and its CSS once the sidebar replaces it.

If the project says `.vue` edits must go through a particular subagent, delegate the shell and view edits to it and give it the approved proposal.

## 4. Verify

Evidence beats confidence here, because visual work looks fine in the diff and wrong in the browser.

- Build the app (`npm run build` or the project's equivalent) and fix any errors or new warnings.
- Run the dev server and open every route in a real browser (use a browser-automation tool such as Playwright if one is available). Take a screenshot of each at desktop width (about 1440px) and at phone width (about 390px).
- Check, per page: the active sidebar item matches the page, no horizontal page scroll, no overlapping or clipped content, tables and charts still fit their container, modals open above the sidebar, loading and empty states still look right.
- Check the app's other modes: every supported language (long labels can break a fixed-width sidebar), and dark mode if it exists.
- Read the browser console for new errors.
- Show the user before and after screenshots of the two or three most representative pages, and list anything you deliberately left alone.

Do not commit or push unless the user asks; follow the project's own git rules.

## Output

End with a short summary: what changed (shell, tokens, shared styles, which views), what you did not touch and why, how you verified it, and any follow-ups you noticed but left (for example, hard-coded labels that bypass i18n).
