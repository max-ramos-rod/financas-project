# Plano de Evolucao Arquitetural - financas-project

Data: 2026-03-12
Ultima atualizacao: 2026-05-29

## Status de execucao

| Fase | Item | Status |
|---|---|---|
| Fase 0 | auth-sessao-inatividade | Concluido |
| Fase 0 | rate limiting (slowapi) | Concluido |
| Fase 0 | recuperacao de senha | Concluido |
| Fase 0 | substituicao de alert/confirm | Em andamento |
| **Fase 1** | **Envelope padronizado de resposta** | **Concluido** |
| **Fase 1** | **Paginacao reutilizavel** | **Concluido** |
| **Fase 1** | **Fortalecer stores por dominio** | **Concluido** |
| Fase 2 | Service layer (TransacaoService) | Pendente |
| Fase 3 | Repositories explicitos | Pendente |
| Fase 4 | Testes unitarios de service | Pendente |

### O que foi entregue na Fase 1 (2026-05-29)

**Backend:**
- `app/core/pagination.py` — `PaginationParams`, `PageMeta`, `PaginationMetaBuilder`
- `app/core/responses.py` — `ResponseEnvelope[T]`, `PaginatedResponseEnvelope[T]`, alias `PagedResponse`
- `app/core/repositories.py` — `SQLAlchemyRepository[ModelT]` (infra para futura service layer)
- Todos os endpoints de listagem padronizados em `PagedResponse`: contas, categorias, orcamentos, transacoes, metas
- Removidos: `app/schemas/pagination.py` e `app/crud/base.py` (descontinuados)
- `app/crud/crud_meta.py` reescrito sem CRUDBase, alinhado ao padrao dos demais CRUDs

**Frontend:**
- Novas stores: `stores/orcamentos.ts`, `stores/metas.ts`, `stores/delegacoes.ts`
- Stores existentes (`contas.ts`, `categorias.ts`) atualizadas para extrair `.data` do envelope paginado
- `types/pagination.ts` atualizado com `has_next: boolean`
- Todas as views migradas: ListaCategoriasView, ListaContasView, FaturaCartaoView, ImportacaoView, ListaMetasView, ListaOrcamentosView, NovaTransacaoView, Dashboard/IndexView, Delegacoes/ConvitesView, Navbar

### Proximo passo recomendado

`feat/transacao-service` — criar `TransacaoService` como primeira service layer real, usando `SQLAlchemyRepository` como camada de persistencia. Ver Fase 2 abaixo.

## 1. Objetivo

Evoluir o `financas-project` para um patamar de robustez arquitetural semelhante ao `sm-project`, sem perder os fluxos de negocio ja maduros do produto e sem fazer reescrita big bang.

Premissas:
- O `financas-project` ja e funcionalmente maduro.
- O maior problema atual nao e falta de feature, e sim acoplamento no backend.
- O objetivo e reduzir risco de regressao e aumentar capacidade de crescimento.
- A migracao deve ser incremental e orientada a custo-beneficio.

## 2. O que vale preservar

Itens do `financas-project` que devem ser mantidos e tratados como ativos:

- autenticacao e autorizacao atuais
- `AccessContext`
- delegacao / impersonacao via `X-Act-As-User`
- route guards no frontend
- cliente HTTP central com interceptors
- modulos de negocio ja existentes
- regras ricas de transacoes, parcelamento, metas, orcamentos, cartao e relatorios
- base atual com FastAPI + SQLAlchemy sincronico + Alembic

Resumo:
- o projeto nao precisa ser refeito
- ele precisa ser desacoplado

## 3. Diagnostico arquitetural

### 3.1 Problemas atuais

1. A camada `crud_*` acumula responsabilidades demais:
- acesso a dados
- validacao
- regra de negocio
- recalculo de saldo
- impacto em metas
- impacto em orcamentos
- efeitos secundarios de dominio

2. Os endpoints dependem de uma camada intermediaria que nao esta claramente separada entre:
- persistencia
- dominio
- orquestracao de caso de uso

3. Regras criticas do sistema tendem a ficar acopladas:
- transacao
- saldo
- cartao
- meta
- orcamento
- dizimo

4. Falta padronizacao transversal forte para:
- envelope de resposta
- paginacao
- erros
- contratos entre camadas

5. O frontend esta melhor que o backend em organizacao pratica, mas ainda ha espaco para:
- stores mais fortes por dominio
- menos logica em views
- padronizacao de consumo da API

### 3.2 Forcas atuais

1. Produto mais pronto que o projeto de referencia
2. Regras de autenticacao/autorizacao melhores
3. Fluxos reais de negocio ja implementados
4. Boa base de frontend
5. Boa base de migracoes e persistencia com Alembic
6. Dominio real ja modelado

### 3.3 Gargalos de manutencao

1. Mudancas em transacoes tendem a ter alto risco
2. Testar regras de negocio sem banco ainda e caro
3. O acoplamento dificulta onboarding tecnico
4. A consistencia de API ainda depende de disciplina manual
5. O custo de crescimento tende a subir se nada for separado agora

## 4. O que copiar do sm-project, e o que nao copiar

### 4.1 Vale copiar

- arquitetura explicita em camadas: `api -> service -> repository -> db`
- repository pattern explicito
- service layer clara
- contratos com `Protocol`
- paginacao padronizada
- envelope `data/meta`
- erros no formato RFC 7807
- testes unitarios de service com fakes
- frontend mais orientado a dominio

### 4.2 Nao vale copiar agora

- migracao para async como prioridade
- abstracoes genericas antes de estabilizar o padrao real
- overengineering de formularios dinamicos por metadados como prioridade estrutural

Resumo:
- o melhor do `sm-project` e a separacao de camadas
- nao faz sentido copiar primeiro o aspecto tecnologico (`async`) sem antes resolver o aspecto arquitetural

## 5. Itens que ja estavam no radar do projeto

Antes do plano arquitetural, o projeto ja tinha algumas frentes relevantes em andamento ou discutidas:

1. `auth-sessao-inatividade`
- encerrar sessao por inatividade configuravel no `.env`

2. login com Google / OAuth
- autenticacao social integrada ao fluxo atual

3. substituicao de `alert()` e `confirm()`
- trocar por modais e feedbacks visuais com DaisyUI

4. melhoria de consistencia da interface
- navbar mais organizada
- dashboard mais limpo
- footer global

5. endurecimento de regras de transacao
- exemplo: restringir `entrada` a tipos corretos de conta

6. refinamento de filtros de transacoes
- regras mais ricas no backend
- frontend consumindo filtros do backend

Esses itens nao entram em conflito com o plano arquitetural, mas nem todos devem virar prioridade arquitetural numero 1.

## 6. `auth-sessao-inatividade` deve ser o primeiro item?

### Resposta curta

Sim, como entrega de branch atual, e uma escolha defensavel.

### Resposta estrategica

Ela **nao e a melhor primeira entrega da evolucao arquitetural**, mas **e uma boa primeira entrega de produto/seguranca**.

### Por que faz sentido fazer agora

- tem valor direto para seguranca
- tem valor visivel para o usuario
- melhora o comportamento de sessao em ambiente real
- pode ser feita sem reestruturar o backend inteiro

### Por que ela nao e a melhor primeira entrega arquitetural

Porque nao reduz o principal gargalo estrutural do projeto:
- acoplamento da regra de negocio
- falta de service layer
- falta de padronizacao de contratos

### Recomendacao pragmatica

Use esta ordem:

1. fechar `auth-sessao-inatividade` neste branch
2. depois abrir uma frente arquitetural separada
3. comecar a evolucao estrutural por padroes transversais e `TransacaoService`

Conclusao:
- como branch atual: boa escolha
- como ponto de partida da reforma arquitetural: nao e a melhor escolha

## 7. Direcao arquitetural recomendada

### Estado atual (2026-05-29)

`api -> crud_* -> db`

com infra pronta em `app/core/`: envelope de resposta padronizado, paginacao reutilizavel, `SQLAlchemyRepository` aguardando service layer.

### Estado alvo incremental

`api -> service -> repository -> db`

### Estrategia de migracao

1. padronizar contratos transversais da API
2. criar services por dominio
3. mover persistencia para repositories
4. testar services com fakes
5. extrair subservicos menores apenas onde o dominio ja estiver muito grande

## 8. Roadmap por fases

## Fase 0 - Entregas em curso / consolidacao

### Objetivo
Fechar as melhorias de produto e seguranca ja em andamento sem perder foco arquitetural.

### Tarefas
- implementar `auth-sessao-inatividade`
- manter endurecimento das regras de transacao
- concluir substituicao progressiva de `alert/confirm`
- consolidar ajustes de UX relevantes ja iniciados

### Impacto
- alto para produto

### Dificuldade
- baixa a media

### Risco
- baixo

## Fase 1 - Padroes transversais de API

### Objetivo
Criar contratos tecnicos unificados para backend e frontend.

### Tarefas
- criar `SuccessResponse`
- criar `PaginatedResponse`
- criar `PaginationMeta`
- criar `PaginationParams`
- criar `Page`
- padronizar erro com RFC 7807 / `problem+json`
- adaptar cliente HTTP do frontend

### Impacto
- alto

### Dificuldade
- media

### Risco
- baixo a medio

## Fase 2 - Service layer inicial

### Objetivo
Separar orquestracao de negocio da persistencia.

### Tarefas
- criar `TransacaoService`
- criar `ContaService`
- criar `OrcamentoService`
- fazer endpoints chamarem services
- reduzir regra dentro de `crud_*`

### Impacto
- muito alto

### Dificuldade
- media a alta

### Risco
- medio

## Fase 3 - Repositories e contratos

### Objetivo
Transformar `crud_*` em acesso a dados de verdade.

### Tarefas
- criar `repositories/`
- criar `Protocol` para repositories
- mover queries SQLAlchemy para repositories
- deixar services dependentes de contratos

### Impacto
- alto

### Dificuldade
- alta

### Risco
- medio

## Fase 4 - Testes unitarios de service

### Objetivo
Permitir evolucao segura das regras sem depender do banco.

### Tarefas
- criar fakes de repositories
- testar `TransacaoService`
- testar `ContaService`
- testar `OrcamentoService`
- cobrir cenarios de maior risco

### Impacto
- muito alto

### Dificuldade
- media

### Risco
- baixo

## Fase 5 - Refinamento de dominio

### Objetivo
Quebrar servicos grandes em componentes menores.

### Tarefas
- extrair `SaldoService`
- extrair politica de orcamento
- extrair atualizacao de metas
- extrair regras de dizimo
- extrair politica de cartao

### Impacto
- alto

### Dificuldade
- media a alta

### Risco
- medio

## Fase 6 - Observabilidade e modernizacao

### Objetivo
Melhorar operacao e preparar escala.

### Tarefas
- logs estruturados
- correlation id
- documentacao arquitetural
- avaliar migracao para async por modulo

### Impacto
- medio a alto

### Dificuldade
- media a alta

### Risco
- medio

## 9. Estrutura futura recomendada

## 9.1 Backend

```text
backend/app/
  api/
    deps.py
    error_handlers.py
    pagination.py
    response_envelopes.py
    v1/
      endpoints/
        auth.py
        contas.py
        transacoes.py
        orcamentos.py
        metas.py
        delegacoes.py
        relatorios.py

  core/
    config.py
    security.py
    exceptions.py
    logging.py

  db/
    session.py

  services/
    transacao_service.py
    conta_service.py
    orcamento_service.py
    meta_service.py
    delegacao_service.py

  repositories/
    transacao_repository.py
    conta_repository.py
    orcamento_repository.py
    meta_repository.py

  contracts/
    repositories.py

  domain/
    saldo.py
    dizimo.py
    orcamento.py
    metas.py

  models/
  schemas/
  tests/
```

Observacao:
- essa estrutura pode ser alcancada em duas etapas
- primeiro `services/` e `repositories/` globais
- depois, se fizer sentido, reorganizar por dominio

## 9.2 Frontend

```text
frontend/src/
  app/
    router/
    layouts/

  components/
    common/
      AppNavbar.vue
      AppFooter.vue
      AppAlert.vue
      AppModal.vue
      AppStatCard.vue

  domains/
    transacoes/
      api/
      stores/
      components/
      views/
    contas/
      api/
      stores/
      components/
      views/
    orcamentos/
      api/
      stores/
      components/
      views/
    metas/
      api/
      stores/
      components/
      views/
    delegacoes/
      api/
      stores/
      components/
      views/
    relatorios/
      api/
      stores/
      components/
      views/

  services/
    api.ts
    http.ts

  utils/
  types/
```

## 10. Backlog priorizado

### 1. Auth por sessao de inatividade
- descricao: expirar sessao com base em inatividade configuravel
- motivo: seguranca e comportamento real de produto
- dificuldade: media
- impacto: alto
- dependencias: nenhuma estrutural
- ordem recomendada: agora, neste branch

### 2. Envelope padronizado de resposta ✅ CONCLUIDO
- descricao: `ResponseEnvelope[T]`, `PaginatedResponseEnvelope[T]`, alias `PagedResponse`
- entregue em: 2026-05-29 — `app/core/responses.py`

### 3. RFC 7807 para erros
- descricao: padronizar erros como `problem+json`
- motivo: consistencia e melhor tratamento no frontend
- dificuldade: media
- impacto: alto
- dependencias: nenhuma
- ordem recomendada: proximo branch

### 4. Paginacao reutilizavel ✅ CONCLUIDO
- descricao: `PaginationParams`, `PageMeta`, `PaginationMetaBuilder`
- entregue em: 2026-05-29 — `app/core/pagination.py`

### 5. Fortalecer stores por dominio ✅ CONCLUIDO
- descricao: stores para contas, categorias, orcamentos, metas, delegacoes; views sem api.get direto
- entregue em: 2026-05-29 — `src/stores/*.ts`

### 6. Criar `TransacaoService`
- descricao: primeira service layer real
- motivo: atacar o modulo mais critico
- dificuldade: alta
- impacto: muito alto
- dependencias: itens 2, 3 e 4 recomendados
- ordem recomendada: primeira grande entrega arquitetural

### 7. Criar repositories explicitos
- descricao: mover SQLAlchemy para camada dedicada
- motivo: separar persistencia de dominio
- dificuldade: alta
- impacto: alto
- dependencias: item 6
- ordem recomendada: depois de `TransacaoService`

### 8. Criar contratos com `Protocol`
- descricao: services dependerem de interfaces
- motivo: desacoplamento e testabilidade
- dificuldade: media
- impacto: alto
- dependencias: item 7
- ordem recomendada: na mesma frente de repositories

### 9. Testes unitarios de service com fakes
- descricao: testar regras sem banco
- motivo: permitir evolucao segura
- dificuldade: media
- impacto: muito alto
- dependencias: itens 6, 7 e 8
- ordem recomendada: imediatamente apos a primeira service layer estabilizada

### 10. Extrair subservicos de dominio
- descricao: saldo, dizimo, orcamento, metas, cartao
- motivo: diminuir classes inchadas
- dificuldade: media a alta
- impacto: alto
- dependencias: item 9
- ordem recomendada: depois da consolidacao da service layer

### 11. Substituir `alert/confirm` por DaisyUI
- descricao: usar modal, alert e feedback visual consistente
- motivo: UX, padronizacao e previsibilidade
- dificuldade: media
- impacto: medio
- dependencias: nenhuma estrutural
- ordem recomendada: paralelo a fases de produto

### 12. Login com Google / OAuth
- descricao: autenticacao social integrada ao fluxo atual
- motivo: conveniencia e reducao de friccao
- dificuldade: media
- impacto: medio a alto
- dependencias: nenhuma estrutural
- ordem recomendada: apos a sessao por inatividade

### 13. Observabilidade e logs estruturados
- descricao: logs, correlation id e documentacao minima
- motivo: operacao e diagnostico
- dificuldade: media
- impacto: medio
- dependencias: nenhuma forte
- ordem recomendada: depois da fase inicial de services

### 14. Avaliar migracao async
- descricao: revisar se ha ganho real por modulo
- motivo: modernizacao e escalabilidade
- dificuldade: alta
- impacto: medio
- dependencias: arquitetura desacoplada
- ordem recomendada: por ultimo

## 11. Sequencia recomendada de execucao

### Sequencia pratica

1. ~~fechar `auth-sessao-inatividade`~~ ✅
2. ~~padronizar resposta da API~~ ✅
3. ~~adaptar frontend para novos contratos~~ ✅
4. ~~fortalecer stores por dominio~~ ✅
5. **→ criar `TransacaoService`** ← proximo passo
6. criar repositories + contracts
7. adicionar testes unitarios de service
8. extrair subservicos menores
9. padronizar erros com RFC 7807
10. melhorias adjacentes de produto (Google OAuth, feedbacks DaisyUI)
11. so depois avaliar async

## 12. Decisao recomendada para o branch atual

### Decisao

Pode seguir com `auth-sessao-inatividade` neste branch.

### Condicao

Nao transforme esse branch no branch da reforma arquitetural.

### Melhor proximo movimento depois dele

Abrir um branch separado para:

`feat/api-contracts-and-services-foundation`

Escopo desse proximo branch:
- envelope de resposta
- erro RFC 7807
- paginacao reutilizavel
- base para consumo no frontend

Isso cria fundacao tecnica com risco baixo e prepara a entrada da service layer.

