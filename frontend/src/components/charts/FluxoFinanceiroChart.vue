<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dadosMeses: {
    label: string
    recebidas: number
    aReceber: number
    pagas: number
    aPagar: number
    cartao: number
  }[]
}>()

const series = computed(() => [
  { name: 'Recebidas', data: props.dadosMeses.map(item => item.recebidas) },
  { name: 'A Receber', data: props.dadosMeses.map(item => item.aReceber) },
  { name: 'Pagas', data: props.dadosMeses.map(item => item.pagas) },
  { name: 'A Pagar', data: props.dadosMeses.map(item => item.aPagar) },
  { name: 'Cartao', data: props.dadosMeses.map(item => item.cartao) }
])

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)

const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    stacked: true,
    background: 'transparent',
    toolbar: { show: false }
  },

  theme: { mode: 'dark' },

  plotOptions: {
    bar: {
      borderRadius: 6,
      columnWidth: '40%'
    }
  },

  dataLabels: { enabled: false },

  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },

  xaxis: {
    categories: props.dadosMeses.map(item => item.label),
    labels: { style: { colors: '#9CA3AF' } },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },

  yaxis: {
    labels: {
      formatter: (value: number) => formatarMoeda(value),
      style: { colors: '#9CA3AF' }
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

  colors: [
    '#22C55E',
    '#F59E0B',
    '#64748B',
    '#F59E0B',
    '#EF4444'
  ],

  responsive: [
    {
      breakpoint: 1024,
      options: {
        plotOptions: {
          bar: { columnWidth: '48%' }
        }
      }
    },
    {
      breakpoint: 640,
      options: {
        plotOptions: {
          bar: { columnWidth: '58%' }
        }
      }
    }
  ]
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
