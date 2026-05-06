import { computed, ref } from 'vue'

import { apiJson, apiJsonNoBody } from './useApi'

export interface Me {
  user_id: string
  role: string
}

const me = ref<Me | null | undefined>(undefined)

export function useAuth() {
  const isReady = computed(() => me.value !== undefined)
  const isAuthenticated = computed(() => me.value !== undefined && me.value !== null)
  const role = computed(() => me.value?.role ?? null)
  const isAdmin = computed(() => role.value === 'admin')

  async function refreshMe(): Promise<void> {
    try {
      const r = await fetch('/api/auth/me', { credentials: 'include' })
      if (r.status === 401) {
        me.value = null
        return
      }
      if (!r.ok) {
        me.value = null
        return
      }
      me.value = (await r.json()) as Me
    } catch {
      me.value = null
    }
  }

  function clearMe(): void {
    me.value = null
  }

  async function login(email: string, password: string): Promise<void> {
    const m = await apiJson<Me>('/api/auth/session', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    me.value = m
  }

  async function logout(): Promise<void> {
    await apiJsonNoBody('/api/auth/logout', { method: 'POST', body: '{}' })
    me.value = null
  }

  async function register(name: string, email: string, password: string): Promise<void> {
    await apiJson('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    })
  }

  return {
    me,
    isReady,
    isAuthenticated,
    role,
    isAdmin,
    refreshMe,
    clearMe,
    login,
    logout,
    register,
  }
}
