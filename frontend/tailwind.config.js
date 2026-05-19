/** @type {import('tailwindcss').Config} */

// Token de marca Finanças Cristãs · v1 · 18 mai 2026
// Direção 02 · Geométrica · Forest #1F5C3A

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Geist"', '"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
        mono: ['"Geist Mono"', 'ui-monospace', '"SF Mono"', 'Menlo', 'monospace'],
      },
      // Escala tipográfica semântica (substitui text-xs/sm/base/lg/xl/2xl/3xl ad-hoc)
      fontSize: {
        // [size, { lineHeight, letterSpacing, fontWeight }]
        'label':   ['11px',  { lineHeight: '1.4',  letterSpacing: '0.08em' }], // monospace uppercase
        'meta':    ['13px',  { lineHeight: '1.45' }],                          // ajudas, descrições secundárias
        'body':    ['15px',  { lineHeight: '1.5'  }],                          // corpo padrão
        'lg':      ['18px',  { lineHeight: '1.45' }],                          // h2, card titles em destaque
        'xl':      ['22px',  { lineHeight: '1.3',  letterSpacing: '-0.01em' }],
        '2xl':     ['28px',  { lineHeight: '1.15', letterSpacing: '-0.02em' }],
        '3xl':     ['36px',  { lineHeight: '1.05', letterSpacing: '-0.025em' }], // h1 das views
        'display': ['56px',  { lineHeight: '1.02', letterSpacing: '-0.03em' }],  // hero, login pitch
        'mega':    ['96px',  { lineHeight: '0.95', letterSpacing: '-0.04em' }],  // Home hero
      },
      letterSpacing: {
        // Garantia de tabular para números
        'tabular': '0',
      },
      borderRadius: {
        'xs': '4px',
        'sm': '6px',
        'md': '8px',   // padrão de botões, inputs, badges
        'lg': '10px',  // padrão de cards
        'xl': '14px',  // modais
        '2xl': '20px', // F mark, mobile frames
      },
      boxShadow: {
        // Sombras quase invisíveis para fintech sério
        'card':   '0 1px 0 rgba(255,255,255,0.5) inset, 0 1px 2px rgba(0,0,0,0.03)',
        'lifted': '0 1px 0 rgba(255,255,255,0.5) inset, 0 10px 40px rgba(0,0,0,0.06)',
        'modal':  '0 20px 60px rgba(0,0,0,0.25)',
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        // Tema light — cravado para "Finanças Cristãs"
        light: {
          // === MARCA ===
          'primary': '#1F5C3A',           // Forest · cor da marca
          'primary-focus': '#155F3C',     // hover
          'primary-content': '#ffffff',

          // === ACENTOS SEMÂNTICOS ===
          // Dessaturados em vez de neons. Olho de fintech sério.
          'secondary': '#3D3D39',         // ink-2 (usar com parcimônia)
          'secondary-content': '#ffffff',
          'accent': '#1F5C3A',            // mesmo que primary por padrão
          'accent-content': '#ffffff',
          'neutral': '#1f1f1c',           // ink
          'neutral-content': '#f3f3ef',

          // === BASES ===
          'base-100': '#ffffff',          // surface · cards
          'base-200': '#f3f3ef',          // bg · página
          'base-300': '#e6e6df',          // paper-2 · estados pressed, dividers fortes
          'base-content': '#1f1f1c',      // ink

          // === STATUS ===
          // Dessaturados: green forest, red brick, mustard.
          'info': '#0f6c8a',
          'info-content': '#ffffff',
          'success': '#2d7d4a',           // ok
          'success-content': '#ffffff',
          'warning': '#b57e2d',           // warn (mostarda, não amarelo neon)
          'warning-content': '#ffffff',
          'error': '#b53d2c',             // crit (brick, não coral)
          'error-content': '#ffffff',

          // === MOTION ===
          '--rounded-box': '0.625rem',    // 10px · cards
          '--rounded-btn': '0.5rem',      // 8px · botões
          '--rounded-badge': '999px',     // pílulas
          '--animation-btn': '0',         // sem animação de "press"
          '--animation-input': '0',
          '--btn-text-case': 'none',      // sem uppercase forçado
          '--navbar-padding': '0.75rem',
          '--border-btn': '1px',
          '--tab-border': '1px',
          '--tab-radius': '0.5rem',
        },
      },
    ],
    base: true,
    styled: true,
    utils: true,
    rtl: false,
    prefix: '',
    logs: false,
  },
}
