<script setup lang="ts">
import Lockup from '@/components/layout/Lockup.vue'
</script>

<template>
  <div>
    <!-- Header público -->
    <header class="bg-base-100 border-b border-base-300 h-16 flex items-center px-6 lg:px-8 shrink-0">
      <Lockup size="sm" to="/" />
      <div class="flex-1"></div>
      <div class="flex items-center gap-4">
        <router-link to="/login" class="text-sm text-base-content/60 hover:text-base-content transition-colors">
          Entrar
        </router-link>
        <router-link to="/registro" class="btn btn-primary btn-sm">Criar conta</router-link>
      </div>
    </header>

    <!-- Hero -->
    <div class="container mx-auto px-6 lg:px-8 py-20 lg:py-24 grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20 items-center" style="min-height: 560px">

      <!-- Esquerda: pitch -->
      <div>
        <div class="mb-10 lg:mb-12">
          <Lockup size="lg" />
        </div>

        <h1 class="font-semibold text-[clamp(36px,4vw,56px)] leading-[1.05] tracking-[-0.03em]">
          Cada conta no lugar.<br>
          Cada categoria com <span class="text-primary">orçamento</span>.<br>
          Cada mês com plano.
        </h1>

        <p class="mt-6 text-lg leading-relaxed text-base-content/60 max-w-[40ch]">
          Uma ferramenta para colocar a vida financeira em ordem — sem dashboards barulhentos, sem promessas mágicas.
        </p>

        <div class="flex flex-wrap gap-3 mt-9">
          <router-link to="/registro" class="btn btn-primary">Criar minha conta</router-link>
          <router-link to="/login" class="btn btn-ghost">Já tenho conta</router-link>
        </div>

        <div class="flex flex-wrap items-center gap-3 mt-7 text-[11px] font-mono uppercase tracking-widest text-base-content/40">
          <span>Grátis pra começar</span>
          <span class="inline-block w-1 h-1 rounded-full bg-base-content/30"></span>
          <span>Sem cartão</span>
          <span class="inline-block w-1 h-1 rounded-full bg-base-content/30"></span>
          <span>Dados locais e criptografados</span>
        </div>
      </div>

      <!-- Direita: mini-dashboard decorativo -->
      <div class="hidden lg:block">
        <div class="card bg-base-100 border border-base-300 shadow-xl overflow-hidden">

          <!-- Mini-nav -->
          <div class="h-10 px-4 border-b border-base-300 bg-base-100 flex items-center justify-between">
            <span class="text-xs font-semibold">Finanças Cristãs</span>
            <div class="flex gap-3 text-[11px] text-base-content/40">
              <span class="text-base-content font-medium">Dashboard</span>
              <span>Transações</span>
              <span>Contas</span>
            </div>
            <div class="w-6 h-6 rounded-full bg-primary text-primary-content flex items-center justify-center text-[9px] font-semibold select-none">MR</div>
          </div>

          <!-- Mini-conteúdo -->
          <div class="p-5 bg-base-200 space-y-3">

            <!-- Hero stripe mini -->
            <div class="bg-base-100 border border-base-300 rounded-lg px-4 py-3 flex items-center justify-between">
              <div>
                <p class="text-[9px] font-mono uppercase tracking-widest text-base-content/40">Saldo total</p>
                <p class="text-2xl font-bold tabular-nums" style="letter-spacing: -0.02em">R$ 67.280,40</p>
              </div>
              <span class="badge badge-success badge-sm font-mono text-[10px]">+ 4,2% mês</span>
            </div>

            <!-- Mini KPIs -->
            <div class="grid grid-cols-4 gap-2">
              <div class="bg-base-100 border border-base-300 rounded px-3 py-2">
                <p class="text-[8px] font-mono uppercase tracking-wide text-base-content/40">Receitas</p>
                <p class="text-base font-bold tabular-nums text-success">R$ 14,8k</p>
              </div>
              <div class="bg-base-100 border border-base-300 rounded px-3 py-2">
                <p class="text-[8px] font-mono uppercase tracking-wide text-base-content/40">Despesas</p>
                <p class="text-base font-bold tabular-nums text-error">R$ 9,4k</p>
              </div>
              <div class="bg-base-100 border border-base-300 rounded px-3 py-2">
                <p class="text-[8px] font-mono uppercase tracking-wide text-base-content/40">Saldo mês</p>
                <p class="text-base font-bold tabular-nums text-success">R$ 5,3k</p>
              </div>
              <div class="bg-base-100 border border-base-300 rounded px-3 py-2">
                <p class="text-[8px] font-mono uppercase tracking-wide text-base-content/40">Cartão</p>
                <p class="text-base font-bold tabular-nums text-error">R$ 2,8k</p>
              </div>
            </div>

            <!-- Mini charts -->
            <div class="grid grid-cols-7 gap-2">

              <!-- Fluxo financeiro (mini barras) -->
              <div class="col-span-4 bg-base-100 border border-base-300 rounded p-3">
                <p class="text-[8px] font-mono uppercase tracking-widest text-base-content/40 mb-2">Fluxo financeiro</p>
                <div class="space-y-2">
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] font-mono text-base-content/40 w-5 shrink-0">abr</span>
                    <div class="flex-1 space-y-1">
                      <div class="h-2 rounded-sm bg-success" style="width: 65%"></div>
                      <div class="h-2 rounded-sm bg-error"   style="width: 42%"></div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] font-mono text-base-content/40 w-5 shrink-0">mai</span>
                    <div class="flex-1 space-y-1">
                      <div class="h-2 rounded-sm bg-success" style="width: 72%"></div>
                      <div class="h-2 rounded-sm bg-error"   style="width: 48%"></div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] font-mono text-base-content/40 w-5 shrink-0">jun</span>
                    <div class="flex-1 space-y-1">
                      <div class="h-2 rounded-sm bg-success opacity-40" style="width: 78%"></div>
                      <div class="h-2 rounded-sm bg-error   opacity-40" style="width: 52%"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Categorias (mini horizontal bars) -->
              <div class="col-span-3 bg-base-100 border border-base-300 rounded p-3">
                <p class="text-[8px] font-mono uppercase tracking-widest text-base-content/40 mb-2">Categorias</p>
                <div class="space-y-2">
                  <div>
                    <div class="flex justify-between text-[10px] mb-1">
                      <span class="text-base-content/60">Moradia</span>
                      <span class="font-semibold tabular-nums">R$ 2,8k</span>
                    </div>
                    <div class="h-1 rounded bg-base-300 overflow-hidden">
                      <div class="h-full rounded bg-primary" style="width: 92%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[10px] mb-1">
                      <span class="text-base-content/60">Alimentação</span>
                      <span class="font-semibold tabular-nums">R$ 1,9k</span>
                    </div>
                    <div class="h-1 rounded bg-base-300 overflow-hidden">
                      <div class="h-full rounded bg-primary" style="width: 62%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[10px] mb-1">
                      <span class="text-base-content/60">Transporte</span>
                      <span class="font-semibold tabular-nums">R$ 1,3k</span>
                    </div>
                    <div class="h-1 rounded bg-base-300 overflow-hidden">
                      <div class="h-full rounded bg-primary" style="width: 42%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-[10px] mb-1">
                      <span class="text-base-content/60">Lazer</span>
                      <span class="font-semibold tabular-nums">R$ 980</span>
                    </div>
                    <div class="h-1 rounded bg-base-300 overflow-hidden">
                      <div class="h-full rounded bg-primary" style="width: 32%"></div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
        <p class="mt-3 text-center text-[11px] font-mono uppercase tracking-widest text-base-content/30">
          Dashboard · maio 2026
        </p>
      </div>

    </div>
  </div>
</template>
