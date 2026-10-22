<template>
  <div class="app-shell" :class="{ 'sidebar-open': sidebarOpen }">
    <aside id="app-sidebar" class="sidebar" :aria-label="t('nav.companyName')">
      <div class="sidebar-brand">
        <span class="sidebar-brand-name" :title="t('nav.companyName')">{{ t('nav.companyName') }}</span>
        <span class="sidebar-brand-sub" :title="t('nav.subtitle')">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <!-- Only '/' needs exact matching: as a prefix it would match every route -->
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :active-class="item.to === '/' ? '' : 'is-active'"
          exact-active-class="is-active"
          :title="t(item.labelKey)"
        >
          <svg
            class="sidebar-icon"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path :d="item.icon" />
          </svg>
          <span class="sidebar-link-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>
    </aside>

    <div class="sidebar-backdrop" @click="sidebarOpen = false"></div>

    <div class="app-main">
      <header class="topbar">
        <button
          class="menu-button"
          type="button"
          aria-label="Toggle navigation"
          aria-controls="app-sidebar"
          :aria-expanded="sidebarOpen"
          @click="sidebarOpen = !sidebarOpen"
        >
          <svg
            viewBox="0 0 20 20"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M3 5h14M3 10h14M3 15h14" />
          </svg>
        </button>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <main class="content">
        <FilterBar />
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const sidebarOpen = ref(false)
    const route = useRoute()

    // Close the phone drawer on any navigation, including browser back/forward
    watch(() => route.path, () => { sidebarOpen.value = false })

    // One entry per route, in display order. Icons are 20x20 stroke paths.
    const navItems = [
      { to: '/', labelKey: 'nav.overview', icon: 'M3 3h5.5v5.5H3zM11.5 3H17v5.5h-5.5zM3 11.5h5.5V17H3zM11.5 11.5H17V17h-5.5z' },
      { to: '/inventory', labelKey: 'nav.inventory', icon: 'M3 6.5L10 3l7 3.5v7L10 17l-7-3.5zM3 6.5l7 3.5 7-3.5M10 10v7' },
      { to: '/orders', labelKey: 'nav.orders', icon: 'M7 3h6v2.5H7zM13 4h2.5A1.5 1.5 0 0117 5.5v11a1.5 1.5 0 01-1.5 1.5h-11A1.5 1.5 0 013 16.5v-11A1.5 1.5 0 014.5 4H7M7 10h6M7 13.5h4' },
      { to: '/spending', labelKey: 'nav.finance', icon: 'M10 2.5v15M13.5 6H8.25a2.25 2.25 0 000 4.5h3.5a2.25 2.25 0 010 4.5H6' },
      { to: '/demand', labelKey: 'nav.demandForecast', icon: 'M2.5 14l5-5 3 3 6-6.5M12.5 5.5H17V10' },
      { to: '/restocking', labelKey: 'nav.restocking', icon: 'M16.5 10a6.5 6.5 0 01-11.3 4.4M3.5 10a6.5 6.5 0 0111.3-4.4M15 2.5V6h-3.5M5 17.5V14h3.5' },
      { to: '/reports', labelKey: 'nav.reports', icon: 'M5 2.5h6.5L16 7v10.5H5zM11.5 2.5V7H16M7.5 11h5M7.5 14h5' }
    ]

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      sidebarOpen,
      navItems,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  /* Atari 2600 "Classic" palette */
  --atari-orange: #e8761c;
  --atari-yellow: #f2c230;
  --atari-green: #4caf50;
  --atari-blue: #3a6fd8;
  --atari-red: #d8382c;
  --atari-black: #000000;

  /* Surfaces */
  --color-bg: #0b0b10;
  --color-surface: #15151d;
  --color-surface-muted: #1f1f2a;
  --color-sidebar-bg: #3a2416;
  --color-sidebar-text: #f0e2d0;
  --color-sidebar-text-muted: #d9c3a8;
  --color-sidebar-text-active: #000000;
  --color-sidebar-hover: rgba(242, 194, 48, 0.18);
  --color-sidebar-active: #e8761c;

  /* Text */
  --color-text: #f2efe6;
  --color-text-body: #e0dccf;
  --color-text-muted: #a9a79f;
  --color-text-subtle: #8c8a84;

  /* Lines */
  --color-border: #3a3a4a;
  --color-border-strong: #5a5a70;

  /* Accent */
  --color-accent: #e8761c;
  --color-accent-hover: #f58a30;
  --color-accent-soft: #2b1a0c;
  --color-focus-ring: #f2c230;
  --color-focus-ring-on-dark: #f2c230;

  /* Status: strong value colors plus solid badge blocks with dark text */
  --color-success: #5cc460;
  --color-success-soft: #4caf50;
  --color-success-text: #000000;
  --color-info: #6b97f0;
  --color-info-soft: #3a6fd8;
  --color-info-text: #ffffff;
  --color-warning: #f2c230;
  --color-warning-soft: #f2c230;
  --color-warning-text: #000000;
  --color-danger: #ff6a5c;
  --color-danger-soft: #d8382c;
  --color-danger-text: #ffffff;
  --color-danger-bg: #2a1210;
  --color-stable-soft: #8a8a9a;
  --color-stable-text: #000000;

  /* Spacing (4px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Typography */
  --font-sans: ui-monospace, 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
  --font-display: ui-monospace, 'SF Mono', Menlo, Consolas, 'Courier New', monospace;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 16px;
  --text-lg: 20px;
  --text-xl: 26px;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
  --leading-tight: 1.25;
  --leading-normal: 1.5;

  /* Radius and shadow */
  --radius-sm: 0;
  --radius-md: 0;
  --radius-lg: 0;
  --border-width: 2px;
  --shadow-sm: 3px 3px 0 #000;
  --shadow-md: 4px 4px 0 #000;
  --shadow-lg: 6px 6px 0 #000;

  /* Layout */
  --sidebar-width: 248px;
  --topbar-height: 56px;
  --content-max-width: 1440px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Faint static scanlines over the page background */
body::after {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 100;
  pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(255, 255, 255, 0.025) 0, rgba(255, 255, 255, 0.025) 1px, transparent 1px, transparent 3px);
}

/* Shared controls */
button, select, input, textarea {
  border-radius: 0;
}

input:not([type='range']):not([type='checkbox']):not([type='radio']),
select,
textarea {
  background: var(--color-surface-muted);
  color: var(--color-text);
  border: var(--border-width) solid var(--color-border-strong);
  font-family: inherit;
}

input[type='checkbox'],
input[type='radio'] {
  accent-color: var(--atari-orange);
}

select option {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

button:active:not(:disabled) {
  transform: translate(2px, 2px) !important;
  box-shadow: none !important;
}

button:not(:disabled) {
  font-family: var(--font-display);
}

h1, h2, h3 {
  font-family: var(--font-display);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

input[type='range'] {
  -webkit-appearance: none;
  appearance: none;
  height: 12px;
  background: var(--color-surface-muted);
  border: var(--border-width) solid var(--color-border-strong);
  border-radius: 0;
  cursor: pointer;
}

input[type='range']::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 22px;
  background: var(--atari-orange);
  border: 2px solid #000;
  border-radius: 0;
  box-shadow: 2px 2px 0 #000;
  cursor: pointer;
}

input[type='range']::-moz-range-thumb {
  width: 18px;
  height: 22px;
  background: var(--atari-orange);
  border: 2px solid #000;
  border-radius: 0;
  box-shadow: 2px 2px 0 #000;
  cursor: pointer;
}

/* Atari logo: four palette blocks */
.atari-logo {
  display: inline-flex;
  gap: 3px;
}

.atari-logo i {
  display: block;
  width: 10px;
  height: 10px;
  border: 1px solid #000;
}
.atari-logo i:nth-child(1) { background: var(--atari-red); }
.atari-logo i:nth-child(2) { background: var(--atari-orange); }
.atari-logo i:nth-child(3) { background: var(--atari-yellow); }
.atari-logo i:nth-child(4) { background: var(--atari-blue); }

/* Shell */
.app-shell {
  display: grid;
  /* minmax(0, 1fr) lets wide tables shrink and scroll instead of stretching the page */
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  padding: var(--space-5) var(--space-3);
  background:
    repeating-linear-gradient(90deg, rgba(0, 0, 0, 0.14) 0, rgba(0, 0, 0, 0.14) 2px, transparent 2px, transparent 7px),
    var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  overflow-y: auto;
  border-right: 4px solid #000;
  border-left: 4px solid #c9a06a;
}

.sidebar-brand {
  padding: 0 var(--space-3) var(--space-5);
  margin-bottom: var(--space-3);
  border-bottom: 3px solid #000;
  min-width: 0;
}

/* CSS-drawn logo: four palette squares */
.sidebar-brand::before {
  content: '';
  display: block;
  width: 12px;
  height: 12px;
  margin-bottom: var(--space-3);
  background: var(--atari-red);
  border: 1px solid #000;
  box-shadow: 15px 0 0 0 var(--atari-orange), 30px 0 0 0 var(--atari-yellow), 45px 0 0 0 var(--atari-blue);
}

.sidebar-brand-name,
.sidebar-brand-sub {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-brand-name {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  color: #fff;
}

.sidebar-brand-sub {
  margin-top: var(--space-1);
  font-size: var(--text-xs);
  color: var(--color-sidebar-text-muted);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-sidebar-text);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  border: 2px solid transparent;
  transition: background-color 120ms ease, color 120ms ease;
}

.sidebar-link:hover {
  background: var(--color-sidebar-hover);
  border-color: var(--atari-yellow);
  color: #fff;
}

.sidebar-link.is-active {
  background: var(--color-sidebar-active);
  border-color: #000;
  box-shadow: 3px 3px 0 #000;
  color: var(--color-sidebar-text-active);
  font-weight: var(--weight-bold);
}

.sidebar-link:focus-visible,
.menu-button:focus-visible {
  outline: 2px solid var(--color-focus-ring-on-dark);
  outline-offset: 1px;
}

.sidebar-icon {
  width: 18px;
  height: 18px;
  flex: none;
}

/* Truncate long (e.g. Japanese) labels instead of wrapping the row */
.sidebar-link-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-backdrop {
  display: none;
}

.app-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* No overflow:hidden here: the language and profile dropdowns open below the bar */
.topbar {
  position: sticky;
  top: 0;
  z-index: 15;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-6);
  background: var(--color-surface);
  border-bottom: 3px solid #000;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.menu-button {
  display: none;
  margin-right: auto;
  padding: var(--space-2);
  border: 2px solid var(--color-border-strong);
  border-radius: 0;
  background: none;
  color: var(--color-text);
  cursor: pointer;
}

.menu-button:hover {
  border-color: var(--atari-yellow);
}

.content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-6);
}

@media (max-width: 768px) {
  .app-shell {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    width: min(var(--sidebar-width), 85vw);
    transform: translateX(-100%);
    transition: transform 180ms ease;
  }

  .sidebar-open .sidebar {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 20;
    background: rgba(0, 0, 0, 0.7);
    opacity: 0;
    pointer-events: none;
    transition: opacity 180ms ease;
  }

  .sidebar-open .sidebar-backdrop {
    opacity: 1;
    pointer-events: auto;
  }

  .menu-button {
    display: inline-flex;
  }

  .topbar {
    padding: 0 var(--space-4);
  }

  .content {
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar-backdrop,
  .sidebar-link {
    transition: none;
  }
}

/* Page header */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-tight);
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.page-header h2::before {
  content: '';
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: var(--space-3);
  vertical-align: baseline;
  background: var(--atari-orange);
  border: 2px solid #000;
  box-shadow: 14px 0 0 -1px var(--atari-yellow), 28px 0 0 -1px var(--atari-green), 42px 0 0 -1px var(--atari-blue);
  margin-right: 56px;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

/* Stat tiles */
.stats-grid {
  display: grid;
  /* min() keeps a single column from overflowing narrow phones */
  grid-template-columns: repeat(auto-fit, minmax(min(240px, 100%), 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: var(--border-width) solid var(--color-border-strong);
  box-shadow: var(--shadow-md);
  transition: border-color 0.15s ease;
}

.stat-card:hover {
  border-color: var(--atari-yellow);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
  color: var(--color-text);
  font-family: var(--font-display);
  letter-spacing: 0.02em;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

/* Cards */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: var(--border-width) solid var(--color-border-strong);
  box-shadow: var(--shadow-md);
  margin-bottom: var(--space-5);
  min-width: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: var(--border-width) solid var(--color-border-strong);
}

.card-title {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-tight);
  color: var(--color-text);
}

/* Tables scroll horizontally inside their card */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-surface-muted);
  border-bottom: var(--border-width) solid var(--color-border-strong);
}

th {
  font-family: var(--font-display);
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-body);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: rgba(242, 194, 48, 0.1);
}

/* Badges */
.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border: 2px solid #000;
  border-radius: 0;
  font-family: var(--font-display);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-normal);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-text);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
}

.badge.info,
.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info-text);
}

.badge.stable {
  background: var(--color-stable-soft);
  color: var(--color-stable-text);
}

/* Loading and error states */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--color-danger-bg);
  border: var(--border-width) solid var(--color-danger-soft);
  color: #ffd2cc;
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
