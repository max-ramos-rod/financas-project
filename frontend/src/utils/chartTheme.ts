export const darkFintechTheme = {
  chart: {
    background: 'transparent',
    toolbar: { show: false },
    foreColor: '#9CA3AF', // cinza elegante
    fontFamily: 'Inter, system-ui, sans-serif'
  },

  theme: {
    mode: 'dark'
  },

  grid: {
    borderColor: '#1F2933', // quase invisível
    strokeDashArray: 4
  },

  dataLabels: {
    enabled: false
  },

  stroke: {
    width: 2
  },

  tooltip: {
    theme: 'dark',
    style: {
      fontSize: '12px'
    }
  },

  legend: {
    labels: {
      colors: '#D1D5DB'
    }
  },

  xaxis: {
    labels: {
      style: {
        colors: '#9CA3AF'
      }
    },
    axisBorder: { show: false },
    axisTicks: { show: false }
  },

  yaxis: {
    labels: {
      style: {
        colors: '#9CA3AF'
      }
    }
  }
}
