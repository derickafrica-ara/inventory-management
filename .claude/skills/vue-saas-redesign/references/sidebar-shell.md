# Sidebar shell skeleton

A working starting point for the app shell. Adapt names, routes, i18n function and existing header widgets to the app; do not paste it blind. It assumes Vue 3, vue-router 4 and the tokens in `design-tokens.md`.

## Contents
- Structure
- Template and script
- Styles
- Details that are easy to miss

## Structure

```
.app-shell                (grid: sidebar | main)
├── aside.sidebar         (brand, nav list, footer)
├── .sidebar-backdrop     (phone only, closes the drawer)
└── .app-main
    ├── header.topbar     (menu button on phones, page-level widgets: language, profile)
    ├── .toolbar          (optional: global filters shared by every page)
    └── main.content      (router-view, padded, max-width)
```

## Template and script

Drive the nav from data. Reuse the app's existing i18n function and the existing header components.

```vue
<template>
  <div class="app-shell" :class="{ 'sidebar-open': sidebarOpen }">
    <aside class="sidebar" aria-label="Primary">
      <div class="sidebar-brand">
        <span class="sidebar-brand-name">{{ t('nav.companyName') }}</span>
        <span class="sidebar-brand-sub">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          active-class="is-active"
          exact-active-class="is-active"
          @click="sidebarOpen = false"
        >
          <svg class="sidebar-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="item.icon" />
          </svg>
          <span>{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- Move the existing profile menu here, or into the topbar -->
      </div>
    </aside>

    <div class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <div class="app-main">
      <header class="topbar">
        <button class="menu-button" type="button" aria-label="Open navigation"
                :aria-expanded="sidebarOpen" @click="sidebarOpen = !sidebarOpen">
          <svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
            <path d="M3 5h14M3 10h14M3 15h14" />
          </svg>
        </button>
        <div class="topbar-spacer"></div>
        <!-- Existing LanguageSwitcher / ProfileMenu components, unchanged -->
      </header>

      <!-- Existing global filter bar, if the app has one -->

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'AppShell',
  setup() {
    const sidebarOpen = ref(false)
    const route = useRoute()

    // Close the phone drawer on navigation, including browser back/forward.
    watch(() => route.path, () => { sidebarOpen.value = false })

    // One entry per existing route, in the existing order. Icon paths are 20x20 stroke paths.
    const navItems = [
      { to: '/', labelKey: 'nav.overview', icon: 'M3 10l7-7 7 7M5 8.5V17h10V8.5' }
      // ...
    ]

    return { sidebarOpen, navItems }
  }
}
</script>
```

Use `exact-active-class` only for the root route (`/`), otherwise `/` stays highlighted on every page; give sub-routes `active-class`. Keep whatever `t` the app already uses and import it as the app does.

## Styles

```css
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr); /* minmax(0) lets wide tables shrink instead of stretching the page */
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
  font-size: var(--text-base);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: var(--space-5) var(--space-3);
  background: var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  overflow-y: auto;
}

.sidebar-brand { padding: 0 var(--space-3) var(--space-5); }
.sidebar-brand-name { display: block; font-size: var(--text-md); font-weight: var(--weight-semibold); color: var(--color-sidebar-text-active); }
.sidebar-brand-sub { display: block; font-size: var(--text-xs); opacity: 0.7; }

.sidebar-nav { display: flex; flex-direction: column; gap: var(--space-1); }

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: inherit;
  text-decoration: none;
  font-weight: var(--weight-medium);
  transition: background-color 120ms ease, color 120ms ease;
}
.sidebar-link:hover { background: var(--color-sidebar-hover); }
.sidebar-link.is-active { background: var(--color-sidebar-active); color: var(--color-sidebar-text-active); }
.sidebar-link:focus-visible { outline: 2px solid var(--color-focus-ring); outline-offset: 2px; }
.sidebar-icon { width: 18px; height: 18px; flex: none; }

.sidebar-footer { margin-top: auto; padding-top: var(--space-4); }

.app-main { display: flex; flex-direction: column; min-width: 0; }

.topbar {
  position: sticky; top: 0; z-index: 10;
  display: flex; align-items: center; gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}
.topbar-spacer { flex: 1; }
.menu-button { display: none; }

.content {
  width: 100%;
  max-width: var(--content-max-width);
  padding: var(--space-6);
}

.sidebar-backdrop { display: none; }

@media (max-width: 768px) {
  .app-shell { grid-template-columns: minmax(0, 1fr); }

  .sidebar {
    position: fixed; inset: 0 auto 0 0; z-index: 30;
    width: min(var(--sidebar-width), 85vw);
    transform: translateX(-100%);
    transition: transform 180ms ease;
  }
  .sidebar-open .sidebar { transform: translateX(0); }

  .sidebar-backdrop {
    position: fixed; inset: 0; z-index: 20;
    background: rgba(15, 23, 42, 0.45);
    opacity: 0; pointer-events: none;
    transition: opacity 180ms ease;
  }
  .sidebar-open .sidebar-backdrop { display: block; opacity: 1; pointer-events: auto; }

  .menu-button { display: inline-flex; padding: var(--space-2); border: 0; background: none; color: inherit; }
  .topbar { padding: 0 var(--space-4); }
  .content { padding: var(--space-4); }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar, .sidebar-backdrop, .sidebar-link { transition: none; }
}
```

## Details that are easy to miss

- **Stacking.** The old top nav may have used `position: sticky` with its own z-index, and existing modals may rely on a z-index that now sits under the sidebar or topbar. Modals should be above the topbar (z-index 10) and the phone drawer (30); popovers opened from the topbar need to be above the topbar.
- **Long labels.** Japanese, German and other translations can be longer than English. Let sidebar labels truncate with an ellipsis and a `title` rather than wrapping the row to two lines.
- **Page header.** Give pages one shared block, for example `.page-header` with an `h1`/`h2` at `--text-xl`, a muted description at `--text-base`, and an actions slot on the right, so titles are identical across pages.
- **Tables.** Wrap wide tables in a container with `overflow-x: auto` so they scroll inside their card instead of widening the page on a phone.
- **Hard-coded nav text.** If the old nav had a label that bypassed i18n, point it out in the summary; fixing it means adding a key to every locale file.
- **Unscoped global styles.** If the app's shared classes live in an unscoped `<style>` block in `App.vue`, keep them there, or move them to one global stylesheet. Restyling them there reaches every view.
