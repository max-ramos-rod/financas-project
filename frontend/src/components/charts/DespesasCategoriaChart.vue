<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'
import { getChartTheme } from '@/utils/chartTheme'

const ApexChart = defineAsyncComponent(() =>
  import('vue3-apexcharts')
)

const props = defineProps<{
  dados: { nome: string; valor: number }[]
}>()

const formatarMoedaEixo = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const chartHeight = computed(() => {
  const dinamico = props.dados.length * 34
  return Math.min(360, Math.max(260, dinamico))
})

const series = computed(() => [
  { name: 'Despesas', data: props.dados.map(d => d.valor) }
])

const chartOptions = computed(() => {
  const t = getChartTheme() as { [key: string]: any }
  return {
    ...t,
    chart: { ...t.chart, type: 'bar', animations: { enabled: false } },
    plotOptions: { bar: { ...t.plotOptions?.bar, horizontal: true, barHeight: '48%' } },
    xaxis: {
      ...t.xaxis,
      min: 0,
      tickAmount: 4,
      labels: {
        ...t.xaxis?.labels,
        formatter: (v: number | string) =>
          `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(Number(v))}`,
      },
    },
    yaxis: {
      ...t.yaxis,
      categories: props.dados.map(d => d.nome),
    },
    tooltip: {
      ...t.tooltip,
      x: { formatter: (_: unknown, opts: any) => props.dados[opts.dataPointIndex]?.nome || '' },
      y: { formatter: (value: number) => formatarMoedaEixo(value) },
    },
    colors: ['#b53d2c'],
    responsive: [
      { breakpoint: 1024, options: { plotOptions: { bar: { barHeight: '42%' } }, xaxis: { tickAmount: 3 } } },
      { breakpoint: 640,  options: { plotOptions: { bar: { barHeight: '36%' } }, xaxis: { tickAmount: 2 } } },
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
