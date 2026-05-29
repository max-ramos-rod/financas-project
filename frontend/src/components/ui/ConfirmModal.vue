<script setup lang="ts">
import { ref, watch, computed } from 'vue'

interface Props {
  open: boolean
  severity?: 'simple' | 'cascade' | 'warn' | 'type-to-confirm'
  title: string
  description?: string
  impacts?: string[]
  confirmLabel?: string
  cancelLabel?: string
  confirmWord?: string
}

const props = withDefaults(defineProps<Props>(), {
  severity: 'simple',
  confirmLabel: 'Confirmar',
  cancelLabel: 'Cancelar',
  impacts: () => [],
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  'confirm': []
  'cancel': []
}>()

const typed = ref('')

watch(() => props.open, (isOpen) => {
  if (!isOpen) typed.value = ''
})

const confirmReady = computed(() => {
  if (props.severity !== 'type-to-confirm') return true
  return typed.value === props.confirmWord
})

function close() {
  emit('update:open', false)
  emit('cancel')
}
function confirm() {
  if (!confirmReady.value) return
  emit('confirm')
  emit('update:open', false)
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) close()
}
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', onKeydown)
}

const iconClass = computed(() => {
  return props.severity === 'warn' ? 'warn' : 'danger'
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="open" class="modal-overlay" @click.self="close" role="dialog" aria-modal="true">
        <div class="modal-box" @click.stop>
          <div class="modal-body">
            <div class="modal-icon" :class="iconClass">
              <svg v-if="iconClass === 'danger'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M6 6l1 14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-14"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 9v4M12 17v.5M3.5 19l8-14a1 1 0 0 1 1.7 0l8 14a1 1 0 0 1-.8 1.5h-16a1 1 0 0 1-.8-1.5z"/>
              </svg>
            </div>
            <h2 class="modal-title">{{ title }}</h2>
            <p v-if="description" class="modal-desc">{{ description }}</p>

            <div v-if="impacts.length > 0" class="impact-list">
              <ul>
                <li v-for="(item, i) in impacts" :key="i">{{ item }}</li>
              </ul>
            </div>

            <div v-if="severity === 'type-to-confirm'" class="confirm-field">
              <label class="lbl">
                Digite <b>{{ confirmWord }}</b> para confirmar
              </label>
              <input
                v-model="typed"
                type="text"
                class="input input-bordered"
                :placeholder="confirmWord"
                autofocus
              />
            </div>
          </div>

          <div class="modal-actions">
            <button class="btn btn-ghost" @click="close">{{ cancelLabel }}</button>
            <button
              class="btn"
              :class="severity === 'warn' ? 'btn-warning' : 'btn-error'"
              :disabled="!confirmReady"
              @click="confirm"
            >
              {{ confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; z-index: 100;
  background: rgba(31, 31, 28, 0.55);
  backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  padding: 32px;
}

.modal-box {
  background: var(--surface);
  border-radius: var(--r-xl, 14px);
  width: 460px; max-width: 100%;
  box-shadow: var(--shadow-modal);
  overflow: hidden;
}

.modal-body { padding: 28px 28px 0; }

.modal-icon {
  width: 44px; height: 44px;
  border-radius: var(--r-md, 8px);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.modal-icon.danger { background: var(--crit-tint); color: var(--crit); }
.modal-icon.warn   { background: var(--warn-tint); color: var(--warn); }
.modal-icon :deep(svg) { width: 22px; height: 22px; }

.modal-title {
  font-family: var(--font-sans); font-weight: 600;
  font-size: 20px; line-height: 1.2; letter-spacing: -0.02em;
  color: var(--ink); margin: 0 0 8px;
}

.modal-desc {
  font-size: 14px; line-height: 1.5;
  color: var(--ink-2); margin: 0;
}

.impact-list {
  margin-top: 14px;
  background: var(--bg);
  border-radius: var(--r-md, 8px);
  padding: 14px 16px;
  font-size: 13px; color: var(--ink-2); line-height: 1.6;
}
.impact-list ul { margin: 0; padding: 0; list-style: none; }
.impact-list li { padding-left: 18px; position: relative; }
.impact-list li::before {
  content: "—"; position: absolute; left: 0; color: var(--ink-3);
}

.confirm-field { margin-top: 18px; }
.confirm-field .lbl {
  display: block;
  font-family: var(--font-mono); font-size: 11px;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--ink-3); margin-bottom: 6px;
}
.confirm-field .lbl b { color: var(--ink); }

.modal-actions {
  margin-top: 24px; padding: 18px 28px;
  background: var(--bg);
  border-top: 1px solid var(--rule);
  display: flex; justify-content: flex-end; gap: 10px;
}

.modal-enter-active, .modal-leave-active { transition: opacity 0.15s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
