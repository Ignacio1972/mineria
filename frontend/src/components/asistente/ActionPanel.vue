<script setup lang="ts">
import { computed } from 'vue'
import type { AccionPendiente, NotificacionProactiva } from '@/types'

interface Props {
  accionesPendientes?: AccionPendiente[]
  notificaciones?: NotificacionProactiva[]
}

const props = withDefaults(defineProps<Props>(), {
  accionesPendientes: () => [],
  notificaciones: () => [],
})

const emit = defineEmits<{
  (e: 'confirmar-accion', accionId: string): void
  (e: 'cancelar-accion', accionId: string): void
  (e: 'ver-notificacion', notificacion: NotificacionProactiva): void
  (e: 'descartar-notificacion', notificacionId: string): void
}>()

const tieneAcciones = computed(() => props.accionesPendientes.length > 0)
const tieneNotificaciones = computed(() => props.notificaciones.length > 0)

function formatearFecha(fecha: string): string {
  const now = new Date()
  const date = new Date(fecha)
  const diffMs = date.getTime() - now.getTime()
  const diffMins = Math.round(diffMs / 60000)

  if (diffMins < 0) return 'Expirada'
  if (diffMins < 1) return 'Expira pronto'
  if (diffMins < 60) return `Expira en ${diffMins} min`
  return `Expira en ${Math.round(diffMins / 60)} h`
}
</script>

<template>
  <div v-if="tieneAcciones || tieneNotificaciones" class="border-t border-base-300 bg-base-200/50 p-4 space-y-4">
    <!-- Acciones pendientes -->
    <div v-if="tieneAcciones">
      <h4 class="text-sm font-semibold mb-2 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Acciones pendientes
      </h4>

      <div class="space-y-2">
        <div
          v-for="accion in accionesPendientes"
          :key="accion.id"
          class="card bg-base-100 shadow-sm"
        >
          <div class="card-body p-3">
            <div class="flex items-start gap-3">
              <!-- Icono -->
              <div class="bg-primary/10 rounded-lg p-2">
                <svg v-if="accion.tipo === 'crear_proyecto'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <svg v-else-if="accion.tipo === 'ejecutar_analisis'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>

              <!-- Contenido -->
              <div class="flex-1 min-w-0">
                <p class="font-medium text-sm">{{ accion.descripcion }}</p>
                <p class="text-xs text-base-content/60 mt-1">
                  {{ formatearFecha(accion.expires_at) }}
                </p>

                <!-- Parametros -->
                <div v-if="Object.keys(accion.parametros).length > 0" class="mt-2">
                  <details class="collapse collapse-arrow bg-base-200 rounded">
                    <summary class="collapse-title text-xs py-1 min-h-0">
                      Ver parametros
                    </summary>
                    <div class="collapse-content text-xs">
                      <pre class="whitespace-pre-wrap">{{ JSON.stringify(accion.parametros, null, 2) }}</pre>
                    </div>
                  </details>
                </div>
              </div>
            </div>

            <!-- Botones de accion -->
            <div class="card-actions justify-end mt-2">
              <button
                class="btn btn-sm btn-ghost"
                @click="emit('cancelar-accion', accion.id)"
              >
                Cancelar
              </button>
              <button
                class="btn btn-sm btn-primary"
                :disabled="!accion.puede_confirmarse"
                @click="emit('confirmar-accion', accion.id)"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Notificaciones proactivas -->
    <div v-if="tieneNotificaciones">
      <h4 class="text-sm font-semibold mb-2 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-info" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        Notificaciones
      </h4>

      <div class="space-y-2">
        <div
          v-for="notif in notificaciones"
          :key="notif.id"
          class="alert shadow-sm cursor-pointer"
          @click="emit('ver-notificacion', notif)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div class="flex-1">
            <p class="text-sm">{{ notif.mensaje }}</p>
            <p v-if="notif.proyecto_nombre" class="text-xs opacity-70">
              Proyecto: {{ notif.proyecto_nombre }}
            </p>
          </div>
          <button
            class="btn btn-ghost btn-sm btn-circle"
            @click.stop="emit('descartar-notificacion', notif.id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
