<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { nome: string; valor: number }[]
}>()

const formatarMoedaEixo = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(valor)

const chartHeight = computed(() => {
  const dinamico = props.dados.length * 34
  return Math.min(360, Math.max(260, dinamico))
})

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
    toolbar: { show: false },
    animations: { enabled: false }
  },

  theme: { mode: 'dark' },

  plotOptions: {
    bar: {
      horizontal: true,
      borderRadius: 6,
      barHeight: '48%'
    }
  },

  dataLabels: { enabled: false },

  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },

  xaxis: {
    categories: props.dados.map(d => d.nome),
    min: 0,
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

  tooltip: {
    theme: 'dark',
    x: {
      formatter: (_: unknown, opts: any) => props.dados[opts.dataPointIndex]?.nome || ''
    },
    y: {
      formatter: (value: number) => formatarMoedaEixo(value)
    }
  },

  colors: ['#7C3AED'],

  responsive: [
    {
      breakpoint: 1024,
      options: {
        plotOptions: { bar: { barHeight: '42%' } },
        xaxis: { tickAmount: 3 }
      }
    },
    {
      breakpoint: 640,
      options: {
        plotOptions: { bar: { barHeight: '36%' } },
        xaxis: { tickAmount: 2 }
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
