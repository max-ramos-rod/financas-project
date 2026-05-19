<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { getChartTheme } from '@/utils/chartTheme'

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
  { name: 'Cartão', data: props.dadosMeses.map(item => item.cartao) }
])

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const chartOptions = computed(() => {
  const t = getChartTheme() as { [key: string]: any }
  return {
    ...t,
    chart: { ...t.chart, type: 'bar', stacked: true },
    plotOptions: { bar: { ...t.plotOptions?.bar, columnWidth: '40%' } },
    xaxis: { ...t.xaxis, categories: props.dadosMeses.map(item => item.label) },
    yaxis: {
      ...t.yaxis,
      labels: { ...t.yaxis?.labels, formatter: (value: number) => formatarMoeda(value) },
    },
    legend: { ...t.legend, position: 'bottom' },
    tooltip: { ...t.tooltip, y: { formatter: (value: number) => formatarMoeda(value) } },
    colors: ['#2d7d4a', '#b57e2d', '#82827a', '#b57e2d', '#b53d2c'],
    responsive: [
      { breakpoint: 1024, options: { plotOptions: { bar: { columnWidth: '48%' } } } },
      { breakpoint: 640,  options: { plotOptions: { bar: { columnWidth: '58%' } } } },
    ],
  }
})
</script>

<template>
  <ApexChart
    height="300"
    type="bar"
    :options="chartOptions"
    :series="series"
  />
</template>
