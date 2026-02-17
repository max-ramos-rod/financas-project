import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/Auth/LoginView.vue') },
    { path: '/convites/confirmar', name: 'confirmar-convite', component: () => import('@/views/Delegacoes/ConfirmarConviteView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/Dashboard/IndexView.vue'), meta: { requiresAuth: true } },
    { path: '/registro', name: 'registro', component: () => import('@/views/Auth/RegistroView.vue'), meta: { requiresAuth: false } },
    { 
      path: '/transacoes', 
      name: 'transacoes', 
      component: () => import('@/views/Transacoes/ListaTransacoesView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/transacoes/nova', 
      name: 'nova-transacao', 
      component: () => import('@/views/Transacoes/NovaTransacaoView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/transacoes/:id/editar', 
      name: 'editar-transacao', 
      component: () => import('@/views/Transacoes/NovaTransacaoView.vue'), 
      meta: { requiresAuth: true } 
    },    
    { 
      path: '/contas', 
      name: 'contas', 
      component: () => import('@/views/Contas/ListaContasView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/contas/nova', 
      name: 'nova-conta', 
      component: () => import('@/views/Contas/NovaContaView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/contas/:id/editar', 
      name: 'editar-conta', 
      component: () => import('@/views/Contas/NovaContaView.vue'), 
      meta: { requiresAuth: true } 
    },
    {
      path: '/contas/:id/fatura',
      name: 'fatura-cartao',
      component: () => import('@/views/Contas/FaturaCartaoView.vue'),
      meta: { requiresAuth: true }
    },
    { 
      path: '/metas', 
      name: 'metas', 
      component: () => import('@/views/Metas/ListaMetasView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/metas/nova', 
      name: 'nova-meta', 
      component: () => import('@/views/Metas/NovaMetaView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/metas/:id/editar', 
      name: 'editar-meta', 
      component: () => import('@/views/Metas/NovaMetaView.vue'), 
      meta: { requiresAuth: true } 
    },      
    { 
      path: '/orcamentos', 
      name: 'orcamentos', 
      component: () => import('@/views/Orcamentos/ListaOrcamentosView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/orcamentos/novo', 
      name: 'novo-orcamento', 
      component: () => import('@/views/Orcamentos/NovoOrcamentoView.vue'), 
      meta: { requiresAuth: true } 
    },
    { 
      path: '/orcamentos/:id/editar', 
      name: 'editar-orcamento', 
      component: () => import('@/views/Orcamentos/NovoOrcamentoView.vue'), 
      meta: { requiresAuth: true } 
    },    
    { 
      path: '/relatorios', 
      name: 'relatorios', 
      component: () => import('@/views/Relatorios/ListaRelatoriosView.vue'), 
      meta: { requiresAuth: true } 
    },
    {
      path: '/categorias',
      name: 'categorias',
      component: () => import('@/views/Categorias/ListaCategoriasView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/delegacoes/convidar',
      name: 'delegacoes-convidar',
      component: () => import('@/views/Delegacoes/ConvidarDelegacaoView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/delegacoes/convites',
      name: 'delegacoes-convites',
      component: () => import('@/views/Delegacoes/ConvitesView.vue'),
      meta: { requiresAuth: true }
    },
  ]
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const goingToLogin = to.path === '/login'

  // Reidrata o usuário quando existe token persistido, sem depender de 401 para navegação.
  if (authStore.token && !authStore.user) {
    await authStore.fetchUser()
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath }
    }
  }

  if (goingToLogin && authStore.isAuthenticated) {
    return { path: '/dashboard' }
  }

  return true
})

export default router
