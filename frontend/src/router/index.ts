import { createRouter, createWebHistory } from 'vue-router'

import { useAuth } from '../composables/useAuth'
import { routes } from './routes'

export const router = createRouter({
  // Mantém URLs amigáveis na raiz (/login, /dashboard, ...)
  // enquanto os assets continuam sendo servidos em /static/dist.
  history: createWebHistory('/'),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)
  const needsGuest = to.matched.some((r) => r.meta.guest)

  if (needsAuth) {
    await auth.refreshMe()
    if (!auth.isAuthenticated.value) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  if (needsGuest) {
    await auth.refreshMe()
    if (auth.isAuthenticated.value) {
      return { path: '/dashboard' }
    }
  }

  const needsAdmin = to.matched.some((r) => r.meta.requiresAdmin)
  if (needsAdmin && auth.role.value !== 'admin') {
    return { path: '/dashboard' }
  }

  return true
})

export default router
