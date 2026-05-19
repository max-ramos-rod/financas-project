<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { getChartTheme } from '@/utils/chartTheme'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { categoria: string; planejado: number; gasto: number }[]
}>()

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const series = computed(() => [
  { name: 'Planejado', data: props.dados.map(d => d.planejado) },
  { name: 'Gasto',     data: props.dados.map(d => d.gasto) },
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

const chartOptions = computed(() => {
  const t = getChartTheme() as { [key: string]: any }
  return {
    ...t,
    chart: { ...t.chart, type: 'bar', animations: { enabled: false } },
    plotOptions: { bar: { ...t.plotOptions?.bar, horizontal: true, barHeight: '42%' } },
    xaxis: {
      ...t.xaxis,
      categories: props.dados.map(d => d.categoria),
      min: 0,
      max: maxValor.value,
      tickAmount: 4,
      labels: {
        ...t.xaxis?.labels,
        show: true,
        formatter: (value: number) => Number(value).toLocaleString('pt-BR'),
      },
    },
    yaxis: { ...t.yaxis },
    legend: { ...t.legend, position: 'bottom' },
    tooltip: { ...t.tooltip, y: { formatter: (value: number) => formatarMoeda(value) } },
    colors: ['#1F5C3A', '#b53d2c'],
    responsive: [
      { breakpoint: 1024, options: { plotOptions: { bar: { barHeight: '38%' } }, xaxis: { tickAmount: 3, max: maxValor.value } } },
      { breakpoint: 640,  options: { plotOptions: { bar: { barHeight: '34%' } }, xaxis: { tickAmount: 2, max: maxValor.value } } },
    ],
  }
})
</script>

<template>
  <ApexChart
    :height="chartHeight"
    type="bar"
    :options="chartOptions"
    :series="series"
  />
</template>
