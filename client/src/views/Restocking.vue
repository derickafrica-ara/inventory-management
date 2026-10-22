<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
        </div>
        <input
          id="restock-budget"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="budgetStep"
          :aria-label="t('restocking.budget')"
          :disabled="maxBudget === 0"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
        </div>
        <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalSpend') }}</div>
          <div class="stat-value">{{ formatCurrency(totalSpend, currentCurrency) }}</div>
        </div>
        <div :class="['stat-card', isOverBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrency(remaining, currentCurrency) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: longestLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="orderSuccess" class="notice notice-success" role="status">
        <span>{{ orderSuccess }}</span>
        <router-link to="/orders" class="notice-link">{{ t('nav.orders') }}</router-link>
      </div>
      <div v-if="orderError" class="notice notice-error" role="alert">{{ orderError }}</div>
      <div v-if="isOverBudget" class="notice notice-error" role="alert">
        {{ t('restocking.overBudget') }}
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ rows.length }})</h3>
          <button
            class="place-order-btn"
            type="button"
            :disabled="!canSubmit"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="rows.length === 0" class="empty-state">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.select') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.item_sku">
                <td>
                  <input
                    type="checkbox"
                    :checked="row.selected"
                    :aria-label="t('restocking.table.select') + ' ' + row.item_sku"
                    @change="selection[row.item_sku] = $event.target.checked"
                  />
                </td>
                <td><strong>{{ row.item_sku }}</strong></td>
                <td>{{ translateProductName(row.item_name) }}</td>
                <td>{{ row.supplier }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                </td>
                <td>
                  <input
                    class="qty-input"
                    type="number"
                    min="1"
                    :max="row.gap"
                    step="1"
                    :value="row.quantity"
                    :aria-label="t('restocking.table.quantity') + ' ' + row.item_sku"
                    @change="onQuantityChange(row, $event)"
                  />
                </td>
                <td>{{ formatCurrencyWithDecimals(row.unit_cost, currentCurrency, 2) }}</td>
                <td><strong>{{ formatCurrencyWithDecimals(row.lineCost, currentCurrency, 2) }}</strong></td>
                <td>{{ t('restocking.days', { count: row.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Trend priority for ranking: increasing demand is restocked first
const TREND_RANK = { increasing: 0, stable: 1, decreasing: 2 }

const toCents = (usd) => Math.round(usd * 100)
const fromCents = (cents) => cents / 100

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])

    // Budget is always in USD; display converts via formatCurrency
    const budget = ref(0)

    // Per-SKU user state; reset whenever recommendations change
    const selection = reactive({})
    const quantities = reactive({})

    const submitting = ref(false)
    const orderSuccess = ref('')
    const orderError = ref('')

    // Forecasts that need restocking, with sanitized numeric fields.
    // Rows with non-finite or non-positive cost/gap are dropped so bad data cannot produce NaN totals.
    const needy = computed(() => {
      return forecasts.value
        .map(f => {
          const current = Number(f.current_demand)
          const forecasted = Number(f.forecasted_demand)
          const unitCost = Number(f.unit_cost)
          const gap = Math.floor(forecasted - current)
          return { ...f, gap, unit_cost: unitCost, lead_time_days: Number(f.lead_time_days) || 0 }
        })
        .filter(f => Number.isFinite(f.gap) && f.gap > 0 && Number.isFinite(f.unit_cost) && f.unit_cost > 0)
    })

    // Cost of fully restocking every item with a positive gap (slider upper bound basis)
    const fullRestockCents = computed(() => {
      return needy.value.reduce((sum, f) => sum + f.gap * toCents(f.unit_cost), 0)
    })

    // Step scales with the total so the slider stays usable for small and large catalogs
    const budgetStep = computed(() => {
      const total = fromCents(fullRestockCents.value)
      if (total >= 100000) return 1000
      if (total >= 10000) return 100
      return 10
    })

    // Round the max up to a clean multiple of the step
    const maxBudget = computed(() => {
      const total = fromCents(fullRestockCents.value)
      return Math.ceil(total / budgetStep.value) * budgetStep.value
    })

    // Greedy fill in rank order: increasing trend first, then larger gap.
    // All arithmetic in integer cents to avoid float drift.
    const recommendations = computed(() => {
      const ranked = [...needy.value].sort((a, b) => {
        const ra = TREND_RANK[a.trend] ?? 3
        const rb = TREND_RANK[b.trend] ?? 3
        if (ra !== rb) return ra - rb
        return b.gap - a.gap
      })

      let remainingCents = toCents(budget.value)
      const result = []
      for (const item of ranked) {
        const costCents = toCents(item.unit_cost)
        const qty = Math.min(item.gap, Math.floor(remainingCents / costCents))
        if (qty <= 0) continue
        remainingCents -= qty * costCents
        result.push({ ...item, quantity: qty })
      }
      return result
    })

    // Reset user edits to the recommendation (on budget change, new data, or after ordering)
    const resetSelection = () => {
      for (const key of Object.keys(selection)) delete selection[key]
      for (const key of Object.keys(quantities)) delete quantities[key]
      for (const item of recommendations.value) {
        selection[item.item_sku] = true
        quantities[item.item_sku] = item.quantity
      }
    }

    watch(recommendations, resetSelection, { immediate: true })

    // Table rows merge recommendation with the user's current selection/quantity
    const rows = computed(() => {
      return recommendations.value.map(item => {
        const quantity = quantities[item.item_sku] ?? item.quantity
        return {
          ...item,
          quantity,
          selected: selection[item.item_sku] !== false,
          lineCost: fromCents(quantity * toCents(item.unit_cost))
        }
      })
    })

    const selectedRows = computed(() => rows.value.filter(r => r.selected))

    const totalSpendCents = computed(() => {
      return selectedRows.value.reduce((sum, r) => sum + r.quantity * toCents(r.unit_cost), 0)
    })
    const totalSpend = computed(() => fromCents(totalSpendCents.value))
    const remaining = computed(() => fromCents(toCents(budget.value) - totalSpendCents.value))
    const isOverBudget = computed(() => totalSpendCents.value > toCents(budget.value))

    const longestLeadTime = computed(() => {
      return selectedRows.value.reduce((max, r) => Math.max(max, r.lead_time_days), 0)
    })

    // Edited quantities are clamped to 1..gap; the budget check is separate (warning + disabled button)
    const onQuantityChange = (row, event) => {
      let value = parseInt(event.target.value, 10)
      if (!Number.isFinite(value)) value = row.quantity
      value = Math.min(Math.max(value, 1), row.gap)
      quantities[row.item_sku] = value
      // Write back so the input shows the clamped value even if state did not change
      event.target.value = value
    }

    const canSubmit = computed(() => {
      return selectedRows.value.length > 0 && !isOverBudget.value && !submitting.value
    })

    const placeOrder = async () => {
      if (!canSubmit.value) return
      submitting.value = true
      orderSuccess.value = ''
      orderError.value = ''
      try {
        const order = await api.createRestockOrder({
          items: selectedRows.value.map(r => ({ sku: r.item_sku, quantity: r.quantity })),
          budget: budget.value
        })
        orderSuccess.value = t('restocking.orderPlaced', {
          number: order.order_number,
          days: order.lead_time_days
        })
        resetSelection()
      } catch (err) {
        orderError.value = err.response?.data?.detail || t('restocking.orderFailed')
        console.error('Place order error:', err)
      } finally {
        submitting.value = false
      }
    }

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        // Start at half of full restock cost so the initial recommendation is non-trivial
        budget.value = Math.round(maxBudget.value / 2 / budgetStep.value) * budgetStep.value
      } catch (err) {
        error.value = t('common.error') + ': ' + err.message
      } finally {
        loading.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      loading,
      error,
      budget,
      maxBudget,
      budgetStep,
      selection,
      rows,
      totalSpend,
      remaining,
      isOverBudget,
      longestLeadTime,
      submitting,
      canSubmit,
      orderSuccess,
      orderError,
      onQuantityChange,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
}

.budget-slider {
  width: 100%;
  height: 6px;
  margin: 0.5rem 0;
  appearance: none;
  -webkit-appearance: none;
  background: var(--color-border-strong);
  border-radius: 0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 0;
  background: var(--atari-orange);
  border: 2px solid white;
  box-shadow: 4px 4px 0 #000;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 0;
  background: var(--atari-orange);
  border: 2px solid white;
  box-shadow: 4px 4px 0 #000;
}

.budget-slider:focus-visible {
  box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.budget-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: var(--color-text-muted);
}

.budget-help {
  margin: 0.75rem 0 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.qty-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 2px solid var(--color-border-strong);
  border-radius: 0;
  color: var(--color-text);
  font-size: 0.875rem;
}

.qty-input:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 1px;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: var(--atari-orange);
  box-shadow: 4px 4px 0 #000;
  border: 2px solid #000 !important;
  color: #000;
  border: none;
  border-radius: 0;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--atari-yellow);
}

.place-order-btn:disabled {
  background: #8c8a84;
  color: #000;
  cursor: not-allowed;
}

.notice {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  border-radius: 0;
  border: 1px solid;
  font-size: 0.875rem;
  font-weight: 500;
}

.notice-success {
  background: var(--atari-green);
  border-color: var(--atari-green);
  color: #000;
}

.notice-error {
  background: var(--atari-red);
  border-color: var(--atari-red);
  color: #fff;
}

.notice-link {
  margin-left: auto;
  color: inherit;
  font-weight: 700;
  text-decoration: underline;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
}
</style>
