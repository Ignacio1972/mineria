<script setup lang="ts">
import { useRoute } from 'vue-router'
import { CorpusManager } from '@/components/corpus'

const route = useRoute()

// Obtener documento ID de query params para navegación directa
const documentoIdInicial = route.query.doc ? Number(route.query.doc) : undefined
</script>

<template>
  <div class="h-[calc(100vh-4rem)]">
    <CorpusManager :documento-id-inicial="documentoIdInicial" />
  </div>
</template>
