<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { nome: string; valor: number }[]
}>()

const formatarMoedaCompacta = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(valor)

const chartHeight = computed(() => Math.max(300, props.dados.length * 46))

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
    labels: {
      formatter: (value: number) => formatarMoedaCompacta(value),
      style: { colors: '#9CA3AF' }
    },
    tickAmount: 4,
    axisBorder: { show: false },
    axisTicks: { show: false }
  },

  yaxis: {
    labels: { style: { colors: '#D1D5DB' } }
  },

  tooltip: {
    theme: 'dark',
    x: {
      formatter: (_: unknown, opts: any) => props.dados[opts.dataPointIndex]?.nome || ''
    },
    y: {
      formatter: (value: number) =>
        new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
    }
  },

  colors: ['#7C3AED'],

  responsive: [
    {
      breakpoint: 1024,
      options: {
        plotOptions: { bar: { barHeight: '62%' } },
        xaxis: { tickAmount: 3 }
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
