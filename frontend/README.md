# Frontend - Financas Cristas

Vue 3 + TypeScript + TailwindCSS + DaisyUI

## Instalacao

```bash
npm install
```

## Configuracao

```bash
cp .env.example .env
```

## Desenvolvimento

```bash
npm run dev
```

## Build

```bash
npm run build
```

Frontend: http://localhost:5173

## Validacao Local (Dia 5)

```bash
npm install
npm run lint
npm run test
```

## Backlog Tecnico / UX

### Substituir `alert()` e `confirm()` nativos

Motivacao:
- remover feedback nativo do navegador;
- padronizar UX com DaisyUI;
- melhorar consistencia visual e comportamento em mobile.

Diretriz:
- usar `modal` DaisyUI para confirmacoes e acoes destrutivas;
- usar `alert` visual ou toast interno para erros e sucessos nao bloqueantes.

Levantamento atual:
- `frontend/src/views/Orcamentos/NovoOrcamentoView.vue`
- `frontend/src/views/Transacoes/NovaTransacaoView.vue`
- `frontend/src/views/Relatorios/ListaRelatoriosView.vue`
- `frontend/src/views/Categorias/ListaCategoriasView.vue`
- `frontend/src/views/Contas/NovaContaView.vue`
