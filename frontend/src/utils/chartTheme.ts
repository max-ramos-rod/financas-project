/**
 * chartTheme.ts · Finanças Cristãs
 * ----------------------------------------------------------------------------
 * Tema de gráficos coerente com o resto do produto.
 *
 * Uso (ApexCharts):
 *   import { getChartTheme } from '@/utils/chartTheme'
 *
 *   const options = {
 *     ...getChartTheme(),
 *     series: [...],
 *     // overrides específicos do gráfico
 *   }
 */

type ChartTheme = Record<string, unknown>

const FONT = '"Geist", "Helvetica Neue", Helvetica, Arial, sans-serif'

const xAxisFormatter = (value: string | number) => {
  const n = typeof value === 'string' ? parseFloat(value) : value
  if (!Number.isFinite(n)) return String(value)
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(n)
}

const lightTheme: ChartTheme = {
  chart: {
    background: 'transparent',
    toolbar: { show: false },
    foreColor: '#3d3d39',     // --ink-2
    fontFamily: FONT,
  },
  theme: { mode: 'light' },
  colors: [
    '#1F5C3A',   // brand
    '#2d7d4a',   // ok
    '#b53d2c',   // crit
    '#b57e2d',   // warn
    '#0f6c8a',   // info
    '#82827a',   // ink-3
  ],
  grid: {
    borderColor: '#d8d8d0',   // --rule
    strokeDashArray: 0,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
  },
  dataLabels: { enabled: false },
  stroke: { width: 2, lineCap: 'round', curve: 'smooth' },
  tooltip: {
    theme: 'light',
    style: { fontSize: '12px', fontFamily: FONT },
  },
  legend: {
    fontSize: '12px',
    fontFamily: FONT,
    labels: { colors: '#3d3d39' },
    markers: { width: 10, height: 10, radius: 2 },
    itemMargin: { horizontal: 12, vertical: 0 },
  },
  xaxis: {
    labels: { formatter: xAxisFormatter, style: { colors: '#82827a', fontSize: '11px', fontFamily: FONT } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { style: { colors: '#82827a', fontSize: '11px', fontFamily: FONT } },
  },
  plotOptions: {
    bar: { borderRadius: 3, columnWidth: '60%' },
  },
}

const darkTheme: ChartTheme = {
  chart: {
    background: 'transparent',
    toolbar: { show: false },
    foreColor: '#c8c0b6',
    fontFamily: FONT,
  },
  theme: { mode: 'dark' },
  colors: [
    '#8fc890',
    '#8fc890',
    '#e89a7e',
    '#d4ac6a',
    '#7ec3da',
    '#8a8278',
  ],
  grid: {
    borderColor: '#2a2622',
    strokeDashArray: 0,
    xaxis: { lines: { show: false } },
    yaxis: { lines: { show: true } },
  },
  dataLabels: { enabled: false },
  stroke: { width: 2, lineCap: 'round', curve: 'smooth' },
  tooltip: {
    theme: 'dark',
    style: { fontSize: '12px', fontFamily: FONT },
  },
  legend: {
    fontSize: '12px',
    fontFamily: FONT,
    labels: { colors: '#c8c0b6' },
    markers: { width: 10, height: 10, radius: 2 },
    itemMargin: { horizontal: 12, vertical: 0 },
  },
  xaxis: {
    labels: { formatter: xAxisFormatter, style: { colors: '#8a8278', fontSize: '11px', fontFamily: FONT } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { style: { colors: '#8a8278', fontSize: '11px', fontFamily: FONT } },
  },
  plotOptions: {
    bar: { borderRadius: 3, columnWidth: '60%' },
  },
}

export function getChartTheme(): ChartTheme {
  if (typeof document === 'undefined') return lightTheme
  const theme = document.documentElement.getAttribute('data-theme')
  return theme === 'dark' ? darkTheme : lightTheme
}

export const lightFintechTheme = lightTheme
export const darkFintechTheme = darkTheme

// Compatibilidade com o nome antigo
export default getChartTheme
