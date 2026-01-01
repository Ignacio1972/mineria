<script setup lang="ts">
import DashboardStats from '@/components/dashboard/DashboardStats.vue'
import RecentAnalysis from '@/components/dashboard/RecentAnalysis.vue'
import QuickActions from '@/components/dashboard/QuickActions.vue'
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Dashboard</h1>

    <!-- Estadisticas -->
    <DashboardStats class="mb-8" />

    <!-- Grid principal -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Acciones rapidas -->
      <div class="lg:col-span-1">
        <QuickActions />
      </div>

      <!-- Analisis recientes -->
      <div class="lg:col-span-2">
        <RecentAnalysis />
      </div>
    </div>
  </div>
</template>
