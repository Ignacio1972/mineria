import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  // Dashboard
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Dashboard' }
  },

  // Clientes
  {
    path: '/clientes',
    name: 'clientes',
    component: () => import('@/views/ClientesView.vue'),
    meta: { title: 'Clientes' }
  },
  {
    path: '/clientes/nuevo',
    name: 'cliente-nuevo',
    component: () => import('@/views/ClienteFormView.vue'),
    meta: { title: 'Nuevo Cliente' }
  },
  {
    path: '/clientes/:id',
    name: 'cliente-detalle',
    component: () => import('@/views/ClienteDetalleView.vue'),
    meta: { title: 'Detalle Cliente' }
  },
  {
    path: '/clientes/:id/editar',
    name: 'cliente-editar',
    component: () => import('@/views/ClienteFormView.vue'),
    meta: { title: 'Editar Cliente' }
  },

  // Proyectos
  {
    path: '/proyectos',
    name: 'proyectos',
    component: () => import('@/views/ProyectosView.vue'),
    meta: { title: 'Proyectos' }
  },
  {
    path: '/proyectos/nuevo',
    name: 'proyecto-nuevo',
    component: () => import('@/views/ProyectoFormView.vue'),
    meta: { title: 'Nuevo Proyecto' }
  },
  {
    path: '/proyectos/:id',
    name: 'proyecto-detalle',
    component: () => import('@/views/ProyectoDetalleView.vue'),
    meta: { title: 'Detalle Proyecto' }
  },
  {
    path: '/proyectos/:id/editar',
    name: 'proyecto-editar',
    component: () => import('@/views/ProyectoFormView.vue'),
    meta: { title: 'Editar Proyecto' }
  },
  {
    path: '/proyectos/:id/mapa',
    name: 'proyecto-mapa',
    component: () => import('@/views/ProyectoMapaView.vue'),
    meta: { title: 'Editar Ubicacion' }
  },
  {
    path: '/proyectos/:id/analisis',
    name: 'proyecto-analisis',
    component: () => import('@/views/ProyectoAnalisisView.vue'),
    meta: { title: 'Analisis' }
  },

  // Analisis global
  {
    path: '/analisis',
    name: 'analisis-historial',
    component: () => import('@/views/AnalisisHistorialView.vue'),
    meta: { title: 'Historial de Analisis' }
  },

  // Corpus Legal RAG
  {
    path: '/corpus',
    name: 'corpus',
    component: () => import('@/views/CorpusView.vue'),
    meta: { title: 'Corpus Legal' }
  },

  // Asistente IA
  {
    path: '/asistente',
    name: 'asistente',
    component: () => import('@/views/AsistenteView.vue'),
    meta: { title: 'Asistente IA' }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: 'No encontrado' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string | undefined
  document.title = title
    ? `${title} | Sistema de Prefactibilidad Ambiental Minera`
    : 'Sistema de Prefactibilidad Ambiental Minera'
  next()
})

export default router
