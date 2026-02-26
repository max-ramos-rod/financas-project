<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { nome: string; valor: number }[]
}>()

const series = computed(() => [
  {
    name: 'Despesas',
    data: props.dados.map(d => d.valor)
  }
])

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false }
  },

  theme: { mode: 'dark' },

  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 6,
      barHeight: '70%'
    }
  },

  dataLabels: { enabled: false },

  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },

  xaxis: {
    categories: props.dados.map(d => d.nome),
    labels: { style: { colors: '#9CA3AF' } },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },

  yaxis: {
    labels: { style: { colors: '#D1D5DB' } }
  },

  tooltip: {
    theme: 'dark'
  },

  colors: ['#7C3AED']
}))
</script>

<template>
  <ApexChart
    height="300"
    type="bar"
    :options="chartOptions"
    :series="series"
  />
</template>
