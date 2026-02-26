<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)
const props = defineProps<{
  recebidas: number
  aReceber: number
  pagas: number
  aPagar: number
  cartao: number
}>()

const series = computed(() => [
  { name: 'Recebidas', data: [props.recebidas] },
  { name: 'A Receber', data: [props.aReceber] },
  { name: 'Pagas', data: [props.pagas] },
  { name: 'A Pagar', data: [props.aPagar] },
  { name: 'Cartão', data: [props.cartao] }
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
      columnWidth: '50%'
    }
  },

  dataLabels: { enabled: false },

  grid: {
    borderColor: '#1F2933',
    strokeDashArray: 4
  },

  xaxis: {
    categories: ['Fluxo do Mês'],
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
