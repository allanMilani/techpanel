import { ref } from 'vue'

type ToastType = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: number
  message: string
  type: ToastType
}

const toasts = ref<ToastMessage[]>([])
let toastCounter = 0

function removeToast(id: number): void {
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

function showToast(message: string, type: ToastType = 'info', durationMs = 3500): void {
  toastCounter += 1
  const id = toastCounter
  toasts.value = [...toasts.value, { id, message, type }]

  window.setTimeout(() => {
    removeToast(id)
  }, durationMs)
}

export function useToast() {
  return {
    toasts,
    showToast,
    removeToast,
  }
}
