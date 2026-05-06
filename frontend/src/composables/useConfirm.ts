import { ref } from 'vue'

const open = ref(false)
const message = ref('')
let pending: ((accepted: boolean) => void) | null = null

export function useConfirm() {
  function requestConfirm(text: string): Promise<boolean> {
    message.value = text
    open.value = true
    return new Promise((resolve) => {
      pending = resolve
    })
  }

  function accept(): void {
    open.value = false
    pending?.(true)
    pending = null
  }

  function dismiss(): void {
    open.value = false
    pending?.(false)
    pending = null
  }

  return {
    open,
    message,
    requestConfirm,
    accept,
    dismiss,
  }
}
