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

const chartHeight = computed(() => {
  const dinamico = props.dados.length * 44
  return Math.min(340, Math.max(220, dinamico))
})

const maxValor = computed(() => {
  const valores = props.dados.flatMap(d => [d.planejado, d.gasto])
  const max = Math.max(...valores, 0)
  const magnitude = Math.pow(10, Math.floor(Math.log10(max || 1)))
  return Math.ceil(max / magnitude) * magnitude
})

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    background: 'transparent',
    toolbar: { show: false },
    animations: { enabled: false }
  },
  theme: { mode: 'dark' },
  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 6,
      barHeight: '42%'
    }
  },
  dataLabels: { enabled: false },
  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },
  xaxis: {
    categories: props.dados.map(d => d.categoria),
    min: 0,
    max: maxValor.value,
    tickAmount: 4,
    labels: {
      show: true,
      formatter: (value: number) => Number(value).toLocaleString('pt-BR'),
      style: { colors: '#9CA3AF' }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },
  yaxis: {
    labels: { style: { colors: '#D1D5DB' } }
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
  colors: ['#3B82F6', '#EF4444'],
  responsive: [
    {
      breakpoint: 1024,
      options: {
        plotOptions: { bar: { barHeight: '38%' } },
        xaxis: { tickAmount: 3, max: maxValor.value }
      }
    },
    {
      breakpoint: 640,
      options: {
        plotOptions: { bar: { barHeight: '34%' } },
        xaxis: { tickAmount: 2, max: maxValor.value }
      }
    }
  ]
}))
</script>

<template>
  <ApexChart
    :height="chartHeight"
    type="bar"
    :options="chartOptions"
    :series="series"
  />
</template>
