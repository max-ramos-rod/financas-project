<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { categoria: string; planejado: number; gasto: number }[]
}>()

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)

const series = computed(() => [
  {
    name: 'Planejado',
    data: props.dados.map(d => d.planejado)
  },
  {
    name: 'Gasto',
    data: props.dados.map(d => d.gasto)
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
      horizontal: false,
      borderRadius: 6,
      columnWidth: '38%'
    }
  },
  dataLabels: { enabled: false },
  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },
  xaxis: {
    categories: props.dados.map(d => d.categoria),
    labels: { style: { colors: '#9CA3AF' }, rotate: -25, trim: true, hideOverlappingLabels: true },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: {
      formatter: (value: number) => formatarMoeda(value),
      style: { colors: '#D1D5DB' }
    }
  },
  legend: {
    position: 'bottom',
    labels: { colors: '#D1D5DB' }
  },
  tooltip: {
    theme: 'dark',
    y: {
      formatter: (value: number) => formatarMoeda(value)
    }
  },
  colors: ['#3B82F6', '#EF4444']
  ,
  responsive: [
    {
      breakpoint: 1024,
      options: {
        plotOptions: { bar: { columnWidth: '55%' } },
        xaxis: { labels: { rotate: -40 } }
      }
    },
    {
      breakpoint: 640,
      options: {
        plotOptions: { bar: { columnWidth: '68%' } },
        xaxis: { labels: { rotate: -50 } }
      }
    }
  ]
}))
</script>

<template>
  <ApexChart
    height="360"
    type="bar"
    :options="chartOptions"
    :series="series"
  />
</template>
