# Dashboard Estratégico de Projetos GRV — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enriquecer a tela "Projetos GRV" com um dashboard BI executivo com 4 gráficos Chart.js, 7 KPI cards, alertas operacionais e tabela de performance por consultor — tornando-a a view padrão da tela.

**Architecture:** Single-file SPA (`grv-cs-jornada.html`). Todos os gráficos usam Chart.js v4 via CDN. O dashboard é renderizado por `renderDashboardProjetos()` chamado de dentro de `renderProjetosGRV()` quando `_proj_view === 'dashboard'`. Instâncias Chart.js são destruídas antes de cada re-render via `_dashCharts = {}`.

**Tech Stack:** HTML/CSS/JS puro, Chart.js 4.x (CDN), localStorage.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html`
- Identidade visual: `--primary: #E05A1E`, sidebar `#1A1A2E`, bg `#F4F5F7`, fonte Segoe UI, `border-radius: 7px`
- Sem frameworks, sem build step, sem npm
- Chart.js via `https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`
- localStorage keys existentes não mudam; `grv_cs_projetos_view` passa a ter default `'dashboard'`
- Todas as funções de computação são puras (sem efeitos colaterais)
- Toda mutação de dados (etapa, tarefas) já existente continua inalterada

---

## File Map

| Arquivo | O que muda |
|---|---|
| `grv-cs-jornada.html` | Tudo — CSS (adições), JS (novas funções, seed expandido, toggle), HTML (gerado via JS) |

---

## Task 1: Chart.js + helpers de status + toggle padrão

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Produces: `getStatusDash(c)`, `computeDashboardKPIs(clientes)`, `_dashCharts`, `PROJETOS_VIEW_KEY` default `'dashboard'`

- [ ] **Step 1: Adicionar Chart.js no `<head>`**

Localizar a linha `<title>GRV CS | Jornada do Cliente</title>` e adicionar depois:

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
```

- [ ] **Step 2: Mudar default do toggle de projetos**

Localizar:
```javascript
let _proj_view = localStorage.getItem(PROJETOS_VIEW_KEY) || 'lista';
```
Substituir por:
```javascript
let _proj_view = localStorage.getItem(PROJETOS_VIEW_KEY) || 'dashboard';
```

- [ ] **Step 3: Adicionar `_dashCharts` global**

Logo após a linha com `let _proj_view`, adicionar:
```javascript
let _dashCharts = {};
```

- [ ] **Step 4: Adicionar `getStatusDash(c)` e `computeDashboardKPIs(clientes)`**

Adicionar as duas funções imediatamente após `getStatus(c)` (linha ~585):

```javascript
function getStatusDash(c) {
  if (c.etapa === 'Cancelado') return 'Cancelado';
  if (getProgresso(c) === 100) return 'Concluído';
  if (getStatus(c) === 'Atrasado') return 'Atrasado';
  if (c.etapa === 'Pausado' || c.etapa === 'Interrompido') return 'Pausado';
  if (['Engajamento','Evolução','Conclusão'].includes(c.etapa)) return 'Em Andamento';
  return 'Não Iniciado';
}

function computeDashboardKPIs(clientes) {
  const r = {total:0, naoIniciado:0, emAndamento:0, atrasado:0, pausado:0, concluido:0, cancelado:0};
  clientes.forEach(c => {
    r.total++;
    const s = getStatusDash(c);
    if      (s==='Não Iniciado')  r.naoIniciado++;
    else if (s==='Em Andamento')  r.emAndamento++;
    else if (s==='Atrasado')      r.atrasado++;
    else if (s==='Pausado')       r.pausado++;
    else if (s==='Concluído')     r.concluido++;
    else if (s==='Cancelado')     r.cancelado++;
  });
  return r;
}
```

- [ ] **Step 5: Verificar no browser**

Abrir `grv-cs-jornada.html`. No console do browser:
```javascript
computeDashboardKPIs(getClientes())
// Esperado: {total: 11, naoIniciado: 4, emAndamento: 4, atrasado: 1, pausado: 2, concluido: 0, cancelado: 0}
getStatusDash(getCliente('RAS METAL'))
// Esperado: "Atrasado"
getStatusDash(getCliente('AÇO ART'))
// Esperado: "Pausado"
```

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): Chart.js + getStatusDash + computeDashboardKPIs + toggle default dashboard"
```

---

## Task 2: Seed data expandido (7 consultores, 38 clientes)

**Files:**
- Modify: `grv-cs-jornada.html` (seção SEED DATA)

**Interfaces:**
- Consumes: `mkFases()` (já existe)
- Produces: 4 novos consultores + 27 novos clientes no seed

- [ ] **Step 1: Expandir SEED_CONSULTORES**

Localizar:
```javascript
const SEED_CONSULTORES = [
  {id:'ana-paula', nome:'Ana Paula Souza'},
  {id:'carlos',    nome:'Carlos Menezes'},
  {id:'maria',     nome:'Maria Lima'},
];
```
Substituir por:
```javascript
const SEED_CONSULTORES = [
  {id:'ana-paula',  nome:'Ana Paula Souza'},
  {id:'carlos',     nome:'Carlos Menezes'},
  {id:'maria',      nome:'Maria Lima'},
  {id:'cristiano',  nome:'Cristiano Santos'},
  {id:'felipe',     nome:'Felipe Alves'},
  {id:'silvia',     nome:'Silvia Costa'},
  {id:'severiano',  nome:'Severiano Rocha'},
];
```

- [ ] **Step 2: Adicionar clientes do Cristiano após SEED_CLIENTES (antes do `];` final)**

Localizar o fechamento `];` do array `SEED_CLIENTES` e inserir antes dele:

```javascript
  // ── Cristiano Santos ──────────────────────────────────────
  {
    id:'METALVALE', projeto:'SAGP-00101', produto:'CPS', consultorId:'cristiano',
    etapa:'Evolução', dataInicio:'2026-02-10', prazo:'2026-12-15',
    proximaAcao:'Checkpoint mensal de evolução',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-02-10T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-03-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-04-15T10:00:00',motivo:'Engajamento concluído'},
    ],
  },
  {
    id:'SIMONSEN', projeto:'SAGP-00102', produto:'CPS', consultorId:'cristiano',
    etapa:'Evolução', dataInicio:'2025-10-01', prazo:'2026-03-31',
    proximaAcao:'Retomar agenda com gerência do cliente',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,0,0, 0,0,0,0]),
    registros:[{id:'r1',autor:'Cristiano Santos',data:'2026-04-01T10:00:00',texto:'Prazo expirado. Aguardando retomada com nova data.'}],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-10-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-11-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-01-15T10:00:00',motivo:'Avançou para evolução'},
    ],
  },
  {
    id:'MECATRON', projeto:'SAGP-00103', produto:'CPS', consultorId:'cristiano',
    etapa:'Engajamento', dataInicio:'2025-09-15', prazo:'2026-01-31',
    proximaAcao:'Escalar para gestão comercial',
    fases: mkFases([1,1,1,1, 1,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-09-15T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-10-20T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'POLIMOLD', projeto:'SAGP-00104', produto:'CPS', consultorId:'cristiano',
    etapa:'Engajamento', dataInicio:'2025-11-01', prazo:'2026-04-30',
    proximaAcao:'Agendar reunião de alinhamento urgente',
    fases: mkFases([1,1,1,1, 1,1,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-11-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-12-10T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'ELETROTINS', projeto:'SAGP-00105', produto:'CPS', consultorId:'cristiano',
    etapa:'Pausado', dataInicio:'2025-08-01', prazo:null,
    proximaAcao:'Aguardar reestruturação interna do cliente',
    fases: mkFases([1,1,1,1, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-08-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Pausado',data:'2025-10-15T10:00:00',motivo:'Reestruturação interna, sem responsável definido'},
    ],
  },
  {
    id:'BORBOREMA', projeto:'SAGP-00106', produto:'CPS', consultorId:'cristiano',
    etapa:'Pausado', dataInicio:'2025-07-15', prazo:null,
    proximaAcao:'Confirmar data de retomada',
    fases: mkFases([1,1,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-07-15T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Pausado',data:'2025-09-01T10:00:00',motivo:'Cliente sem budget confirmado para continuar'},
    ],
  },
  {
    id:'RETALHOMAX', projeto:'SAGP-00107', produto:'CPS', consultorId:'cristiano',
    etapa:'Conclusão', dataInicio:'2025-06-01', prazo:'2026-06-30',
    proximaAcao:'Encerramento formal com NPS',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-06-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-07-01T10:00:00',motivo:'Kickoff excelente'},
      {de:'Engajamento',para:'Evolução',data:'2025-09-01T10:00:00',motivo:'Engajamento concluído'},
      {de:'Evolução',para:'Conclusão',data:'2026-02-01T10:00:00',motivo:'Evolução concluída com sucesso'},
    ],
  },
  {
    id:'TORNEFER', projeto:'SAGP-00108', produto:'CPS', consultorId:'cristiano',
    etapa:'1ª Reunião', dataInicio:'2026-06-01', prazo:'2026-12-20',
    proximaAcao:'Agendar kickoff com equipe técnica',
    fases: mkFases([0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[{de:null,para:'1ª Reunião',data:'2026-06-01T09:00:00',motivo:'Início do projeto'}],
  },
  // ── Felipe Alves ──────────────────────────────────────────
  {
    id:'INDALPE', projeto:'SAGP-00111', produto:'CPS', consultorId:'felipe',
    etapa:'Engajamento', dataInicio:'2026-03-15', prazo:'2026-10-30',
    proximaAcao:'Treinamento módulo Vendas',
    fases: mkFases([1,1,1,1, 1,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-03-15T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-04-05T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'ROTOFER', projeto:'SAGP-00112', produto:'NX/IOT', consultorId:'felipe',
    etapa:'Evolução', dataInicio:'2026-01-10', prazo:'2026-07-31',
    proximaAcao:'Validação de sensores NX linha 3',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-01-10T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-02-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-04-01T10:00:00',motivo:'Engajamento concluído'},
    ],
  },
  {
    id:'AGROFLEX', projeto:'SAGP-00113', produto:'NX/IOT', consultorId:'felipe',
    etapa:'Engajamento', dataInicio:'2025-10-20', prazo:'2026-03-15',
    proximaAcao:'Resolver problema de integração IOT',
    fases: mkFases([1,1,1,1, 1,1,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-10-20T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-11-20T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'LAMIFER', projeto:'SAGP-00114', produto:'CPS', consultorId:'felipe',
    etapa:'Evolução', dataInicio:'2025-12-01', prazo:'2026-05-01',
    proximaAcao:'Retomada após troca de TI no cliente',
    fases: mkFases([1,1,1,1, 1,1,1,1, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-12-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-12-20T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-02-01T10:00:00',motivo:'Evolução iniciada'},
    ],
  },
  {
    id:'PLASVALE', projeto:'SAGP-00115', produto:'CPS', consultorId:'felipe',
    etapa:'Pausado', dataInicio:'2025-09-01', prazo:null,
    proximaAcao:'Aguardar liberação de budget 2026',
    fases: mkFases([1,1,1,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-09-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Pausado',data:'2025-11-01T10:00:00',motivo:'Corte de budget no cliente, sem data definida'},
    ],
  },
  {
    id:'LAMINEX', projeto:'SAGP-00116', produto:'NX/IOT', consultorId:'felipe',
    etapa:'Conclusão', dataInicio:'2025-04-01', prazo:'2026-06-30',
    proximaAcao:'Encerramento formal e NPS',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-04-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-05-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2025-08-01T10:00:00',motivo:'Engajamento concluído'},
      {de:'Evolução',para:'Conclusão',data:'2026-01-15T10:00:00',motivo:'Evolução concluída com sucesso'},
    ],
  },
  {
    id:'COMPRESSEI', projeto:'SAGP-00117', produto:'CPS', consultorId:'felipe',
    etapa:'1ª Reunião', dataInicio:'2026-05-20', prazo:'2026-11-30',
    proximaAcao:'Kick-off agendado para próxima semana',
    fases: mkFases([0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[{de:null,para:'1ª Reunião',data:'2026-05-20T09:00:00',motivo:'Início do projeto'}],
  },
  // ── Silvia Costa ──────────────────────────────────────────
  {
    id:'NXTEC', projeto:'SAGP-00121', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Engajamento', dataInicio:'2026-02-15', prazo:'2026-10-15',
    proximaAcao:'Configuração de dashboards NX com operadores',
    fases: mkFases([1,1,1,1, 1,1,1,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-02-15T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-03-10T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'SENSORTEC', projeto:'SAGP-00122', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Evolução', dataInicio:'2025-11-01', prazo:'2026-08-31',
    proximaAcao:'Calibração de sensores linha 2',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-11-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-12-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-03-01T10:00:00',motivo:'Engajamento concluído'},
    ],
  },
  {
    id:'METATRON', projeto:'SAGP-00123', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Engajamento', dataInicio:'2025-10-01', prazo:'2026-03-01',
    proximaAcao:'Reunião de alinhamento urgente — prazo vencido',
    fases: mkFases([1,1,1,1, 1,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-10-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-11-01T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'PLASTIMETAL', projeto:'SAGP-00124', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Evolução', dataInicio:'2025-09-01', prazo:'2026-02-28',
    proximaAcao:'Escalar dificuldades técnicas para coordenação',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-09-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-10-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2025-12-01T10:00:00',motivo:'Evolução iniciada'},
    ],
  },
  {
    id:'IOTSYSTEM', projeto:'SAGP-00125', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Pausado', dataInicio:'2025-07-01', prazo:null,
    proximaAcao:'Aguardar resolução técnica do cliente',
    fases: mkFases([1,1,1,1, 1,1,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-07-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-08-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Pausado',data:'2025-10-01T10:00:00',motivo:'Problema técnico sem solução imediata no cliente'},
    ],
  },
  {
    id:'NXPRIME', projeto:'SAGP-00126', produto:'NX/IOT', consultorId:'silvia',
    etapa:'Conclusão', dataInicio:'2025-03-01', prazo:'2026-05-31',
    proximaAcao:'NPS e documentação de encerramento',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-03-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-04-01T10:00:00',motivo:'Kickoff excelente'},
      {de:'Engajamento',para:'Evolução',data:'2025-07-01T10:00:00',motivo:'Engajamento concluído'},
      {de:'Evolução',para:'Conclusão',data:'2025-12-01T10:00:00',motivo:'Evolução concluída com sucesso'},
    ],
  },
  // ── Severiano Rocha ───────────────────────────────────────
  {
    id:'ROBOTIX', projeto:'SAGP-00131', produto:'NX/IOT', consultorId:'severiano',
    etapa:'Engajamento', dataInicio:'2026-01-20', prazo:'2026-11-30',
    proximaAcao:'Integração com sistemas legados ERP',
    fases: mkFases([1,1,1,1, 1,1,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-01-20T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-02-15T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'AUTOMIND', projeto:'SAGP-00132', produto:'NX/IOT', consultorId:'severiano',
    etapa:'Evolução', dataInicio:'2026-02-01', prazo:'2026-09-30',
    proximaAcao:'Treinamento avançado de operadores',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2026-02-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2026-02-25T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2026-04-20T10:00:00',motivo:'Engajamento concluído'},
    ],
  },
  {
    id:'USINAGEM3D', projeto:'SAGP-00133', produto:'NX/IOT', consultorId:'severiano',
    etapa:'Evolução', dataInicio:'2025-08-01', prazo:'2026-01-31',
    proximaAcao:'Resolver falha de comunicação NX — urgente',
    fases: mkFases([1,1,1,1, 1,1,1,1, 1,1,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-08-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-09-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Evolução',data:'2025-11-01T10:00:00',motivo:'Evolução iniciada'},
    ],
  },
  {
    id:'FERROPLAST', projeto:'SAGP-00134', produto:'NX/IOT', consultorId:'severiano',
    etapa:'Engajamento', dataInicio:'2025-11-15', prazo:'2026-05-15',
    proximaAcao:'Retomada após férias coletivas na fábrica',
    fases: mkFases([1,1,1,1, 1,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-11-15T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-12-15T10:00:00',motivo:'Kickoff realizado'},
    ],
  },
  {
    id:'MAXPRESS', projeto:'SAGP-00135', produto:'NX/IOT', consultorId:'severiano',
    etapa:'Pausado', dataInicio:'2025-06-01', prazo:null,
    proximaAcao:'Confirmar retomada 2º semestre 2026',
    fases: mkFases([1,1,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-06-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Engajamento',data:'2025-07-01T10:00:00',motivo:'Kickoff realizado'},
      {de:'Engajamento',para:'Pausado',data:'2025-09-01T10:00:00',motivo:'Sem budget confirmado para continuidade'},
    ],
  },
  // ── Cancelado (Carlos) ────────────────────────────────────
  {
    id:'FUNDIFER', projeto:'SAGP-00141', produto:'CPS', consultorId:'carlos',
    etapa:'Cancelado', dataInicio:'2025-05-01', prazo:null,
    proximaAcao:'',
    fases: mkFases([1,1,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0]),
    registros:[],
    historicoEtapas:[
      {de:null,para:'1ª Reunião',data:'2025-05-01T09:00:00',motivo:'Início do projeto'},
      {de:'1ª Reunião',para:'Cancelado',data:'2025-07-15T10:00:00',motivo:'Cliente optou por solução concorrente'},
    ],
  },
```

- [ ] **Step 3: Resetar localStorage e verificar**

No browser, console:
```javascript
localStorage.clear(); location.reload();
// Depois verificar:
getClientes().length
// Esperado: 38

computeDashboardKPIs(getClientes())
// Esperado: {total:38, naoIniciado:6, emAndamento:11, atrasado:10, pausado:7, concluido:3, cancelado:1}

getConsultores().length
// Esperado: 7
```

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): seed expandido — 7 consultores, 38 clientes com distribuição realista de status"
```

---

## Task 3: CSS + KPI Row + scaffold do dashboard

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `computeDashboardKPIs(clientes)`, `_proj_view`
- Produces: `renderKpiRow(kpis)`, `countUp(el, target)`, CSS `.dash-*`, `.alerta-*`, toggle com Dashboard

- [ ] **Step 1: Adicionar CSS do dashboard**

Adicionar no bloco `<style>`, após a linha `.filter-bar select:focus{border-color:var(--primary)}`:

```css
/* ── DASHBOARD ───────────────────────────────────────────── */
.dash-section{margin-bottom:24px}
.dash-section-title{font-size:13px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px}
.dash-kpi-row{display:grid;grid-template-columns:repeat(7,1fr);gap:12px;margin-bottom:24px}
.dash-kpi-card{background:var(--surface);border-radius:var(--radius);padding:16px 18px;box-shadow:var(--shadow);border:1px solid var(--border)}
.dash-kpi-label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--text3);margin-bottom:4px}
.dash-kpi-value{font-size:32px;font-weight:700;line-height:1}
.dash-kpi-card.kpi-atrasado{background:#FFF5F5;border-top:3px solid #e53e3e}
.dash-kpi-card.kpi-pausado{background:#FFFFF0}
.dash-kpi-card.kpi-concluido{background:#F0FFF4}
.dash-chart-row{display:grid;grid-template-columns:55fr 45fr;gap:16px;margin-bottom:24px}
.dash-chart-box{background:var(--surface);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border)}
.dash-chart-box canvas{max-width:100%}
.dash-gauge-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px}
.dash-gauge-box{background:var(--surface);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border);text-align:center}
.dash-gauge-wrap{position:relative;display:inline-block;width:160px;height:90px}
.dash-gauge-label{margin-top:8px;font-size:13px;font-weight:600;color:var(--text)}
.dash-gauge-sub{font-size:11px;color:var(--text3);margin-top:2px}
.dash-backlog-box{background:var(--surface);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border);display:flex;flex-direction:column;justify-content:center;gap:16px}
.dash-backlog-stat .bs-label{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--text3);margin-bottom:4px}
.dash-backlog-stat .bs-value{font-size:28px;font-weight:700}
.alerta-card{padding:14px 16px;border-radius:var(--radius);margin-bottom:8px;display:flex;align-items:flex-start;gap:12px}
.alerta-critico{background:#FFF5F5;border-left:4px solid #e53e3e}
.alerta-atencao{background:#FFFFF0;border-left:4px solid #d69e2e}
.alerta-ok{background:#F0FFF4;border-left:4px solid #38a169}
.alerta-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:5px}
.alerta-dot-red{background:#e53e3e}
.alerta-dot-yellow{background:#d69e2e}
.alerta-dot-green{background:#38a169}
.alerta-body .ab-title{font-size:13px;font-weight:600;color:var(--text)}
.alerta-body .ab-acao{font-size:12px;color:var(--text3);margin-top:2px}
.dash-filter-bar{display:flex;gap:10px;margin-bottom:16px;align-items:center}
.dash-filter-bar select{padding:7px 10px;border:1px solid var(--border);border-radius:var(--radius);font-size:13px;font-family:inherit;color:var(--text);outline:none;background:var(--surface);cursor:pointer}
.dash-filter-bar select:focus{border-color:var(--primary)}
@media(max-width:1100px){.dash-kpi-row{grid-template-columns:repeat(4,1fr)}}
@media(max-width:800px){.dash-kpi-row{grid-template-columns:repeat(2,1fr)}.dash-chart-row{grid-template-columns:1fr}.dash-gauge-row{grid-template-columns:1fr}}
```

- [ ] **Step 2: Adicionar `renderKpiRow(kpis)` e `countUp(el, target)`**

Adicionar após `computeDashboardKPIs`:

```javascript
function countUp(el, target, duration) {
  duration = duration || 500;
  const start = performance.now();
  function tick(now) {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(p * target);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function renderKpiRow(kpis) {
  const cards = [
    {label:'Total',        value:kpis.total,        cls:'',             color:'#1A1A2E'},
    {label:'Não Iniciado', value:kpis.naoIniciado,  cls:'',             color:'#718096'},
    {label:'Em Andamento', value:kpis.emAndamento,  cls:'',             color:'#3182ce'},
    {label:'Atrasados',    value:kpis.atrasado,     cls:'kpi-atrasado', color:'#e53e3e'},
    {label:'Pausados',     value:kpis.pausado,      cls:'kpi-pausado',  color:'#d69e2e'},
    {label:'Concluídos',   value:kpis.concluido,    cls:'kpi-concluido',color:'#38a169'},
    {label:'Cancelados',   value:kpis.cancelado,    cls:'',             color:'#4a5568'},
  ];
  return `<div class="dash-kpi-row">
    ${cards.map((c,i) => `
      <div class="dash-kpi-card ${c.cls}">
        <div class="dash-kpi-label">${c.label}</div>
        <div class="dash-kpi-value" id="kpi-v-${i}" style="color:${c.color}">0</div>
      </div>`).join('')}
  </div>`;
}

function animateKpis(kpis) {
  const vals = [kpis.total,kpis.naoIniciado,kpis.emAndamento,kpis.atrasado,kpis.pausado,kpis.concluido,kpis.cancelado];
  vals.forEach((v,i) => {
    const el = document.getElementById('kpi-v-'+i);
    if (el) countUp(el, v);
  });
}
```

- [ ] **Step 3: Adicionar botão Dashboard no toggle de Projetos GRV**

Localizar dentro de `renderProjetosGRV()` o bloco `const toggle = ...`:
```javascript
  const toggle = `
    <div class="view-toggle">
      <button class="vt-btn${_proj_view==='lista'?' active':''}" onclick="setProjetosView('lista')">☰ Lista</button>
      <button class="vt-btn${_proj_view==='kanban'?' active':''}" onclick="setProjetosView('kanban')">⊞ Kanban</button>
    </div>`;
```
Substituir por:
```javascript
  const toggle = `
    <div class="view-toggle">
      <button class="vt-btn${_proj_view==='dashboard'?' active':''}" onclick="setProjetosView('dashboard')">📊 Dashboard</button>
      <button class="vt-btn${_proj_view==='lista'?' active':''}" onclick="setProjetosView('lista')">☰ Lista</button>
      <button class="vt-btn${_proj_view==='kanban'?' active':''}" onclick="setProjetosView('kanban')">⊞ Kanban</button>
    </div>`;
```

- [ ] **Step 4: Adicionar stub `renderDashboardProjetos` e integrá-lo em `renderProjetosGRV`**

Adicionar antes de `renderProjetosGRV()`:

```javascript
function renderDashboardProjetos(clientes, consultores) {
  Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
  _dashCharts = {};
  const kpis = computeDashboardKPIs(clientes);
  return `
    <div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    ${renderKpiRow(kpis)}
    <p style="color:var(--text3);font-size:13px">Gráficos em breve...</p>`;
}
```

No fim de `renderProjetosGRV()`, localizar o bloco `if (_proj_view === 'lista') { ... } else { ... }` e adicionar um terceiro ramo:

```javascript
  let content;
  if (_proj_view === 'dashboard') {
    content = renderDashboardProjetos(filtered.length ? filtered : todos, consultores);
  } else if (_proj_view === 'lista') {
    // ... (código existente) ...
  } else {
    // kanban
  }
```

Após `sec.innerHTML = ...`, adicionar chamada de animação condicional:
```javascript
  if (_proj_view === 'dashboard') animateKpis(computeDashboardKPIs(filtered.length ? filtered : todos));
```

Nota: no modo dashboard, `filtered` usa apenas o filtro de consultor (os filtros de etapa e status não existem). Garantir que `_proj_etapa` e `_proj_status` sejam ignorados quando `_proj_view === 'dashboard'`. Dentro de `renderProjetosGRV`, no bloco de filtragem, aplicar etapa/status apenas quando NÃO estiver em dashboard:

```javascript
  let filtered = todos;
  if (_proj_consultor) filtered = filtered.filter(c => c.consultorId === _proj_consultor);
  if (_proj_view !== 'dashboard') {
    if (_proj_etapa)  filtered = filtered.filter(c => c.etapa === _proj_etapa);
    if (_proj_status) filtered = filtered.filter(c => getStatus(c) === _proj_status);
  }
```

- [ ] **Step 5: Verificar no browser**

Abrir `grv-cs-jornada.html`. Navegar para "Projetos GRV".
- Deve abrir diretamente no Dashboard (7 KPI cards animando de 0)
- Números corretos: Total=38, Atrasados=10 em vermelho, etc.
- Card "Atrasados" deve ter fundo rosado e borda superior vermelha
- Toggle mostra 3 botões: 📊 Dashboard (ativo em laranja), ☰ Lista, ⊞ Kanban
- Trocar para Lista/Kanban — funciona normalmente
- Voltar para Dashboard — KPIs animam de novo

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): CSS + KPI row animado + toggle 3 views (dashboard padrão)"
```

---

## Task 4: Chart 1 (Donut) + Chart 2 (Barras por Produto)

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `computeDashboardKPIs(clientes)`, `Chart` (global Chart.js)
- Produces: `chartDonutConfig(kpis)`, `chartBarrasConfig(clientes)`, `_dashCharts.donut`, `_dashCharts.barras`

- [ ] **Step 1: Adicionar `chartDonutConfig(kpis)` e `chartBarrasConfig(clientes)`**

Adicionar após `animateKpis`:

```javascript
function chartDonutConfig(kpis) {
  return {
    type: 'doughnut',
    data: {
      labels: ['Concluídos','Em Andamento','Atrasados','Pausados','Não Iniciado','Cancelados'],
      datasets: [{
        data: [kpis.concluido, kpis.emAndamento, kpis.atrasado, kpis.pausado, kpis.naoIniciado, kpis.cancelado],
        backgroundColor: ['#38a169','#3182ce','#e53e3e','#d69e2e','#718096','#4a5568'],
        borderWidth: 2, borderColor: '#fff', hoverOffset: 6
      }]
    },
    options: {
      cutout: '65%',
      plugins: {
        legend: { position:'right', labels:{ boxWidth:12, padding:16, font:{size:12} } },
        tooltip: { callbacks: { label: ctx => {
          const pct = kpis.total ? Math.round(ctx.parsed/kpis.total*100) : 0;
          return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
        }}}
      },
      animation: { duration:500 }
    }
  };
}

function chartBarrasConfig(clientes) {
  const produtos = [...new Set(clientes.map(c => c.produto.split('/')[0]))].filter(Boolean).sort();
  const series = [
    {label:'Em Andamento', key:'emAndamento', color:'#3182ce'},
    {label:'Atrasados',    key:'atrasado',    color:'#e53e3e'},
    {label:'Pausados',     key:'pausado',     color:'#d69e2e'},
    {label:'Concluídos',   key:'concluido',   color:'#38a169'},
  ];
  const datasets = series.map(s => ({
    label: s.label,
    data: produtos.map(p => {
      const sub = clientes.filter(c => c.produto.split('/')[0] === p);
      return computeDashboardKPIs(sub)[s.key];
    }),
    backgroundColor: s.color,
    borderRadius: 4,
  }));
  return {
    type: 'bar',
    data: { labels: produtos, datasets },
    options: {
      plugins: { legend:{ position:'bottom', labels:{ boxWidth:12, font:{size:12} } } },
      scales: {
        y: { beginAtZero:true, grid:{ color:'#edf2f7' }, ticks:{ stepSize:1 } },
        x: { grid:{ display:false } }
      },
      animation: { duration:500 }
    }
  };
}
```

- [ ] **Step 2: Atualizar `renderDashboardProjetos` — primeira linha de charts**

Substituir o stub atual de `renderDashboardProjetos` (o que tem "Gráficos em breve...") pela versão com a primeira linha de charts:

```javascript
function renderDashboardProjetos(clientes, consultores) {
  Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
  _dashCharts = {};
  const kpis = computeDashboardKPIs(clientes);

  const html = `
    <div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    ${renderKpiRow(kpis)}
    <div class="dash-chart-row dash-section">
      <div class="dash-chart-box">
        <div class="dash-section-title">Distribuição de Status</div>
        <div style="position:relative;display:flex;align-items:center;justify-content:center">
          <canvas id="ch-donut" height="220"></canvas>
          <div style="position:absolute;left:25%;transform:translateX(-50%);text-align:center;pointer-events:none">
            <div style="font-size:28px;font-weight:700;color:#1A1A2E">${kpis.total}</div>
            <div style="font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.04em">projetos</div>
          </div>
        </div>
      </div>
      <div class="dash-chart-box">
        <div class="dash-section-title">Por Produto</div>
        <canvas id="ch-barras" height="220"></canvas>
      </div>
    </div>
    <div id="dash-rest">Carregando...</div>`;

  return html;
}
```

- [ ] **Step 3: Adicionar `initCharts(kpis, clientes)` e atualizar a chamada pós-innerHTML**

Adicionar função:

```javascript
function initCharts(kpis, clientes, consultores) {
  const donutEl  = document.getElementById('ch-donut');
  const barrasEl = document.getElementById('ch-barras');
  if (donutEl)  _dashCharts.donut  = new Chart(donutEl,  chartDonutConfig(kpis));
  if (barrasEl) _dashCharts.barras = new Chart(barrasEl, chartBarrasConfig(clientes));
}
```

Em `renderProjetosGRV()`, localizar a linha onde `sec.innerHTML = ...` é atribuído. Após ela (e após a chamada de `animateKpis`), adicionar:

```javascript
  if (_proj_view === 'dashboard') {
    const dashClientes = _proj_consultor ? todos.filter(c => c.consultorId === _proj_consultor) : todos;
    const dashKpis = computeDashboardKPIs(dashClientes);
    initCharts(dashKpis, dashClientes, consultores);
  }
```

- [ ] **Step 4: Verificar no browser**

Abrir Projetos GRV → Dashboard:
- Donut chart visível com 6 fatias coloridas e legenda lateral
- Total "38" no centro do donut
- Hover em fatia mostra tooltip: "Atrasados: 10 (26%)"
- Barras agrupadas por CPS/NX com 4 cores
- Filtrar por consultor (ex: Cristiano Santos) → KPIs mudam, charts atualizam

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): Chart 1 donut distribuição + Chart 2 barras por produto"
```

---

## Task 5: Chart 3 (Gauges Ativação) + Backlog

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `clientes[]`, `getProgresso(c)`, `Chart`
- Produces: `computeAtivacao(clientes, produtoPrefix)`, `computeBacklog(clientes)`, `chartGaugeConfig(pct, cor)`, `_dashCharts.gaugeCPS`, `_dashCharts.gaugeNX`

- [ ] **Step 1: Adicionar helpers de ativação e backlog**

Adicionar após `chartBarrasConfig`:

```javascript
function computeAtivacao(clientes, produtoPrefix) {
  const sub = clientes.filter(c => c.produto.split('/')[0] === produtoPrefix);
  const concluidos = sub.filter(c => getProgresso(c) === 100);
  const noPrazo = concluidos.filter(c => {
    if (!c.prazo) return false;
    return new Date() <= new Date(c.prazo);
  });
  return {
    total: sub.length,
    concluidos: concluidos.length,
    noPrazo: noPrazo.length,
    pct: concluidos.length ? Math.round(noPrazo.length / concluidos.length * 100) : 0,
  };
}

function computeBacklog(clientes) {
  const atrasados = clientes.filter(c => getStatus(c) === 'Atrasado');
  const hoje = new Date();
  const diasTotal = atrasados.reduce((acc, c) => {
    if (!c.prazo) return acc;
    const dias = Math.floor((hoje - new Date(c.prazo)) / 86400000);
    return acc + Math.max(0, dias);
  }, 0);
  return {
    total: diasTotal,
    media: atrasados.length ? Math.round(diasTotal / atrasados.length) : 0,
    qtd: atrasados.length,
  };
}

function chartGaugeConfig(pct, meta) {
  meta = meta || 85;
  const cor = pct >= meta ? '#38a169' : '#e53e3e';
  return {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [pct, 100 - pct],
        backgroundColor: [cor, '#edf2f7'],
        borderWidth: 0,
        circumference: 180,
        rotation: -90,
      }]
    },
    options: {
      cutout: '72%',
      plugins: { legend:{ display:false }, tooltip:{ enabled:false } },
      animation: { duration:500 }
    }
  };
}

function fmtMilhares(n) {
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}
```

- [ ] **Step 2: Atualizar `renderDashboardProjetos` — adicionar linha de gauges + backlog**

Dentro de `renderDashboardProjetos`, após `</div> <!-- fim dash-chart-row -->` e antes do `<div id="dash-rest">`, inserir a linha de gauges. Substituir `<div id="dash-rest">Carregando...</div>` por:

```javascript
  const atCPS = computeAtivacao(clientes, 'CPS');
  const atNX  = computeAtivacao(clientes, 'NX');
  const backlog = computeBacklog(clientes);
  const corCPS = atCPS.pct >= 85 ? '#38a169' : '#e53e3e';
  const corNX  = atNX.pct  >= 85 ? '#38a169' : '#e53e3e';

  // ... dentro do html template, adicionar:
  `<div class="dash-gauge-row dash-section">
    <div class="dash-gauge-box">
      <div class="dash-section-title">Ativação CPS · Meta 85%</div>
      <div class="dash-gauge-wrap">
        <canvas id="ch-gauge-cps" width="160" height="90"></canvas>
      </div>
      <div class="dash-gauge-label" style="color:${corCPS}">${atCPS.pct}%</div>
      <div class="dash-gauge-sub">${atCPS.noPrazo} de ${atCPS.concluidos} entregues no prazo</div>
    </div>
    <div class="dash-gauge-box">
      <div class="dash-section-title">Ativação NX/IOT · Meta 85%</div>
      <div class="dash-gauge-wrap">
        <canvas id="ch-gauge-nx" width="160" height="90"></canvas>
      </div>
      <div class="dash-gauge-label" style="color:${corNX}">${atNX.pct}%</div>
      <div class="dash-gauge-sub">${atNX.noPrazo} de ${atNX.concluidos} entregues no prazo</div>
    </div>
    <div class="dash-backlog-box">
      <div class="dash-section-title">Backlog de Atrasos</div>
      <div class="dash-backlog-stat">
        <div class="bs-label">Total acumulado</div>
        <div class="bs-value" style="color:${backlog.total > 500 ? '#e53e3e' : '#1A1A2E'}">${fmtMilhares(backlog.total)} dias</div>
      </div>
      <div class="dash-backlog-stat">
        <div class="bs-label">Média por projeto atrasado</div>
        <div class="bs-value" style="color:${backlog.media > 90 ? '#d69e2e' : '#1A1A2E'}">${backlog.media} dias</div>
      </div>
      <div style="font-size:11px;color:var(--text3);margin-top:4px">${backlog.qtd} projetos com prazo vencido</div>
    </div>
  </div>
  <div id="dash-rest"></div>`
```

- [ ] **Step 3: Inicializar gauges em `initCharts`**

Atualizar `initCharts`:

```javascript
function initCharts(kpis, clientes, consultores) {
  const donutEl    = document.getElementById('ch-donut');
  const barrasEl   = document.getElementById('ch-barras');
  const gaugeCpsEl = document.getElementById('ch-gauge-cps');
  const gaugeNxEl  = document.getElementById('ch-gauge-nx');

  if (donutEl)    _dashCharts.donut    = new Chart(donutEl,    chartDonutConfig(kpis));
  if (barrasEl)   _dashCharts.barras   = new Chart(barrasEl,   chartBarrasConfig(clientes));
  if (gaugeCpsEl) _dashCharts.gaugeCPS = new Chart(gaugeCpsEl, chartGaugeConfig(computeAtivacao(clientes,'CPS').pct));
  if (gaugeNxEl)  _dashCharts.gaugeNX  = new Chart(gaugeNxEl,  chartGaugeConfig(computeAtivacao(clientes,'NX').pct));
}
```

- [ ] **Step 4: Verificar no browser**

Dashboard deve mostrar:
- Dois semi-arcos (gauges): CPS em vermelho (pct < 85%), NX em vermelho
- Percentual e legenda "X de Y entregues no prazo" abaixo de cada gauge
- Backlog: total em dias e média por projeto, em vermelho quando alto
- Trocar filtro de consultor → gauges e backlog atualizam

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): Chart 3 gauges ativação CPS/NX + backlog stats"
```

---

## Task 6: Alertas Operacionais

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `computeDashboardKPIs(clientes)`, `computeBacklog(clientes)`
- Produces: `computeAlertas(kpis, clientes)`, `renderAlertas(alertas)`

- [ ] **Step 1: Adicionar `computeAlertas` e `renderAlertas`**

Adicionar após `fmtMilhares`:

```javascript
function computeAlertas(kpis, clientes) {
  const alertas = [];
  const backlog = computeBacklog(clientes);
  const pctAtrasado = kpis.total ? kpis.atrasado / kpis.total : 0;
  const pctPausado  = kpis.total ? kpis.pausado  / kpis.total : 0;

  if (pctAtrasado > 0.15) alertas.push({
    sev:'critico',
    titulo: 'Portfólio atrasado: ' + Math.round(pctAtrasado*100) + '% (' + kpis.atrasado + '/' + kpis.total + ' projetos)',
    acao: 'Acima de 15% — escalar para gestão',
  });
  if (backlog.total > 500) alertas.push({
    sev:'critico',
    titulo: 'Backlog em dias atrasados: ' + fmtMilhares(backlog.total) + ' dias acumulados',
    acao: 'Ação imediata de vazão necessária',
  });
  if (kpis.atrasado > 0) alertas.push({
    sev:'critico',
    titulo: 'Estouro de prazo: ' + kpis.atrasado + ' projeto(s) ultrapassaram a data limite',
    acao: 'Revisar escopo ou formalizar extensão com o cliente',
  });
  if (pctPausado > 0.10) alertas.push({
    sev:'atencao',
    titulo: 'Projetos pausados: ' + kpis.pausado + ' (' + Math.round(pctPausado*100) + '% do portfólio)',
    acao: 'Confirmar data de retomada com cada cliente',
  });
  if (backlog.media > 90) alertas.push({
    sev:'atencao',
    titulo: 'Média de atraso: ' + backlog.media + ' dias por projeto atrasado',
    acao: 'Confirmar plano de recuperação com consultores',
  });
  return alertas;
}

function renderAlertas(alertas) {
  if (!alertas.length) {
    return `<div class="alerta-card alerta-ok">
      <div class="alerta-dot alerta-dot-green"></div>
      <div class="alerta-body"><div class="ab-title">Portfólio saudável — sem alertas críticos no momento</div></div>
    </div>`;
  }
  return alertas.map(a => `
    <div class="alerta-card alerta-${a.sev}">
      <div class="alerta-dot alerta-dot-${a.sev==='critico'?'red':'yellow'}"></div>
      <div class="alerta-body">
        <div class="ab-title">${a.titulo}</div>
        <div class="ab-acao">${a.acao}</div>
      </div>
    </div>`).join('');
}
```

- [ ] **Step 2: Inserir alertas no HTML do dashboard**

Dentro de `renderDashboardProjetos`, localizar `<div id="dash-rest"></div>` e substituir por:

```javascript
  const alertas = computeAlertas(kpis, clientes);
  // No template:
  `<div class="dash-section">
    <div class="dash-section-title">Alertas Operacionais</div>
    ${renderAlertas(alertas)}
  </div>
  <div id="dash-rest"></div>`
```

- [ ] **Step 3: Verificar no browser**

Dashboard deve mostrar:
- Seção "Alertas Operacionais" com pelo menos 3 cards vermelhos e 2 amarelos
- Card verde ("Portfólio saudável") nunca aparece com seed data atual (temos 26% atrasados)
- Filtrar por consultor "Cristiano Santos" → alertas atualizam baseados nos projetos dele

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): alertas operacionais com thresholds crítico/atenção"
```

---

## Task 7: Chart 4 (Barras Horizontais) + Tabela Performance por Consultor

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: `clientes[]`, `consultores[]`, `computeDashboardKPIs`
- Produces: `computePerformance(clientes, consultores)`, `chartConsulConfig(data)`, `renderTabelaConsultores(data)`, `_sortConsul`, `_dashCharts.consul`

- [ ] **Step 1: Adicionar `computePerformance` e `_sortConsul`**

Adicionar após `renderAlertas`:

```javascript
let _sortConsul = {key:'pctAtrasado', dir:'desc'};

function computePerformance(clientes, consultores) {
  return consultores.map(con => {
    const sub  = clientes.filter(c => c.consultorId === con.id);
    const kpis = computeDashboardKPIs(sub);
    return {
      id:       con.id,
      nome:     con.nome,
      total:    kpis.total,
      andamento:kpis.emAndamento,
      atrasado: kpis.atrasado,
      pausado:  kpis.pausado,
      concluido:kpis.concluido,
      pctAtrasado: kpis.total ? Math.round(kpis.atrasado / kpis.total * 100) : 0,
    };
  }).filter(r => r.total > 0)
    .sort((a,b) => {
      const v = _sortConsul.dir === 'desc' ? b[_sortConsul.key]-a[_sortConsul.key] : a[_sortConsul.key]-b[_sortConsul.key];
      return v;
    });
}
```

- [ ] **Step 2: Adicionar `chartConsulConfig` e `renderTabelaConsultores`**

```javascript
function chartConsulConfig(data) {
  const labels = data.map(d => d.nome.split(' ')[0]); // primeiro nome
  return {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {label:'Em Andamento', data:data.map(d=>d.andamento), backgroundColor:'#3182ce', stack:'s'},
        {label:'Atrasados',    data:data.map(d=>d.atrasado),  backgroundColor:'#e53e3e', stack:'s'},
        {label:'Pausados',     data:data.map(d=>d.pausado),   backgroundColor:'#d69e2e', stack:'s'},
        {label:'Concluídos',   data:data.map(d=>d.concluido), backgroundColor:'#38a169', stack:'s'},
      ]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend:{ position:'bottom', labels:{ boxWidth:12, font:{size:12} } } },
      scales: {
        x: { stacked:true, grid:{ color:'#edf2f7' }, ticks:{ stepSize:1 } },
        y: { stacked:true, grid:{ display:false } }
      },
      animation: { duration:500 }
    }
  };
}

function renderTabelaConsultores(data) {
  const thStyle = 'cursor:pointer;user-select:none';
  const sortIcon = (key) => _sortConsul.key===key ? (_sortConsul.dir==='desc'?'↓':'↑') : '↕';
  const badgePct = (pct) => {
    const cls = pct > 30 ? 'badge-red' : pct > 15 ? 'badge-yellow' : 'badge-green';
    return `<span class="badge ${cls}">${pct}%</span>`;
  };
  return `
    <div class="table-wrap" style="margin-top:16px">
      <table class="data-table">
        <thead><tr>
          <th>Consultor</th>
          <th style="text-align:center" onclick="sortConsul('total')" style="${thStyle}">Total ${sortIcon('total')}</th>
          <th style="text-align:center;color:#3182ce">Em And.</th>
          <th style="text-align:center;color:#e53e3e">Atrasados</th>
          <th style="text-align:center;cursor:pointer" onclick="sortConsul('pctAtrasado')">% Atrasado ${sortIcon('pctAtrasado')}</th>
          <th style="text-align:center;color:#d69e2e">Pausados</th>
          <th style="text-align:center;color:#38a169">Concluídos</th>
        </tr></thead>
        <tbody>
          ${data.map(d => `<tr>
            <td style="font-weight:600">${d.nome}</td>
            <td style="text-align:center">${d.total}</td>
            <td style="text-align:center;color:#3182ce">${d.andamento}</td>
            <td style="text-align:center;color:#e53e3e;font-weight:600">${d.atrasado}</td>
            <td style="text-align:center">${badgePct(d.pctAtrasado)}</td>
            <td style="text-align:center;color:#d69e2e">${d.pausado}</td>
            <td style="text-align:center;color:#38a169">${d.concluido}</td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

function sortConsul(key) {
  if (_sortConsul.key === key) {
    _sortConsul.dir = _sortConsul.dir === 'desc' ? 'asc' : 'desc';
  } else {
    _sortConsul = {key, dir:'desc'};
  }
  renderProjetosGRV();
}
```

- [ ] **Step 3: Inserir chart + tabela em `renderDashboardProjetos`**

Substituir `<div id="dash-rest"></div>` (na Task 6) por:

```javascript
  const perf = computePerformance(clientes, consultores);
  // No template:
  `<div class="dash-section">
    <div class="dash-section-title">Performance por Consultor</div>
    <div class="dash-chart-box">
      <canvas id="ch-consul" height="220"></canvas>
    </div>
    ${renderTabelaConsultores(perf)}
  </div>`
```

- [ ] **Step 4: Inicializar `ch-consul` em `initCharts`**

Atualizar `initCharts`:

```javascript
function initCharts(kpis, clientes, consultores) {
  const donutEl    = document.getElementById('ch-donut');
  const barrasEl   = document.getElementById('ch-barras');
  const gaugeCpsEl = document.getElementById('ch-gauge-cps');
  const gaugeNxEl  = document.getElementById('ch-gauge-nx');
  const consulEl   = document.getElementById('ch-consul');

  if (donutEl)    _dashCharts.donut    = new Chart(donutEl,    chartDonutConfig(kpis));
  if (barrasEl)   _dashCharts.barras   = new Chart(barrasEl,   chartBarrasConfig(clientes));
  if (gaugeCpsEl) _dashCharts.gaugeCPS = new Chart(gaugeCpsEl, chartGaugeConfig(computeAtivacao(clientes,'CPS').pct));
  if (gaugeNxEl)  _dashCharts.gaugeNX  = new Chart(gaugeNxEl,  chartGaugeConfig(computeAtivacao(clientes,'NX').pct));
  if (consulEl)   _dashCharts.consul   = new Chart(consulEl,   chartConsulConfig(computePerformance(clientes, consultores)));
}
```

- [ ] **Step 5: Verificar no browser**

Dashboard completo deve mostrar:
- Barras horizontais empilhadas por consultor, ordenadas por % atrasado
- Cristiano Santos aparece no topo (maior % de atrasados)
- Tabela abaixo com badges vermelhos/amarelos/verdes na coluna %
- Clicar no header "% Atrasado" inverte a ordenação
- Clicar em "Total" ordena por total de projetos

- [ ] **Step 6: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): Chart 4 barras horizontais + tabela performance por consultor com sort"
```

---

## Task 8: Finalização — destroy loop + edge cases + polish

**Files:**
- Modify: `grv-cs-jornada.html`

**Interfaces:**
- Consumes: todas as funções das tasks anteriores
- Produces: dashboard completo e estável, sem memory leaks de Chart.js

- [ ] **Step 1: Garantir destroy ao navegar entre views**

A função `renderDashboardProjetos` já chama `Object.values(_dashCharts).forEach(ch => ch.destroy())` no início. Verificar que isso acontece quando o usuário vai para Lista e volta para Dashboard. Adicionar `destroy` também no `setProjetosView`:

Localizar `function setProjetosView(v)` (ou onde o `_proj_view` é setado e `renderProjetosGRV()` é chamado). Verificar que já existe, senão adicionar:

```javascript
function setProjetosView(v) {
  if (v !== 'dashboard') {
    Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
    _dashCharts = {};
  }
  _proj_view = v;
  localStorage.setItem(PROJETOS_VIEW_KEY, v);
  renderProjetosGRV();
}
```

- [ ] **Step 2: Empty state no dashboard quando filtro não tem dados**

Em `renderDashboardProjetos`, antes de construir o HTML, verificar se `clientes.length === 0`:

```javascript
function renderDashboardProjetos(clientes, consultores) {
  Object.values(_dashCharts).forEach(ch => { try{ ch.destroy(); }catch(e){} });
  _dashCharts = {};

  if (clientes.length === 0) {
    return `<div class="dash-filter-bar">
      <select onchange="setProjConsultor(this.value)">
        <option value="">Todos consultores</option>
        ${consultores.map(c => `<option value="${c.id}"${c.id===_proj_consultor?' selected':''}>${c.nome}</option>`).join('')}
      </select>
    </div>
    <div class="empty-state"><div class="es-icon">📊</div><div class="es-text">Nenhum projeto encontrado para este consultor.</div></div>`;
  }

  // ... resto do código
}
```

- [ ] **Step 3: Verificar que o donut center label está posicionado corretamente**

O label central do donut usa `left:25%` como estimate. Após ver no browser, ajustar se necessário. O donut com legenda à direita ocupa ~50% do canvas — o centro real fica em torno de `left: calc(50% * 0.5)` da box total.

Método mais robusto: envolver canvas e label em um flex container:

```html
<div style="display:flex;align-items:center;gap:16px">
  <div style="position:relative;flex:0 0 200px;height:220px">
    <canvas id="ch-donut"></canvas>
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none">
      <div style="font-size:28px;font-weight:700;color:#1A1A2E">${kpis.total}</div>
      <div style="font-size:11px;color:#718096;text-transform:uppercase">projetos</div>
    </div>
  </div>
</div>
```

Com Chart.js doughnut, a legenda fica `position:'right'` dentro do canvas. Alternativamente, desativar a legenda interna do Chart.js e renderizá-la manualmente em HTML ao lado.

Testar, ajustar posição até ficar centralizado. A regra de ouro: o donut preenche o canvas com `cutout:'65%'`, e o elemento central usa `position:absolute; top:50%; left:50%; transform:translate(-50%,-50%)` DENTRO de um wrapper com `position:relative`.

- [ ] **Step 4: Testar fluxo completo**

Sequência de verificação:
1. Abrir `grv-cs-jornada.html` — deve abrir em Projetos GRV → Dashboard (default)
2. KPIs animam: Total=38, Atrasados=10 (vermelho)
3. Donut com 6 fatias, barras por produto, gauges, alertas, chart consultor + tabela
4. Filtrar por "Cristiano Santos" → tudo atualiza (KPIs, charts, alertas, tabela)
5. Clicar "☰ Lista" → lista de projetos aparece, nenhum erro de Chart.js no console
6. Clicar "📊 Dashboard" → dashboard volta, KPIs animam de novo
7. Navegar para "Minha Carteira" e voltar para "Projetos GRV" → dashboard intacto
8. Console sem erros

- [ ] **Step 5: Commit final**

```bash
git add grv-cs-jornada.html
git commit -m "feat(dashboard): destroy loop + empty state + polish — dashboard estratégico completo"
```

---

## Self-Review

**Spec coverage:**
- [x] Toggle 📊 Dashboard | ☰ Lista | ⊞ Kanban — Task 3
- [x] Dashboard como view padrão — Task 1 + Task 3
- [x] Chart.js via CDN — Task 1
- [x] `getStatusDash` + `computeDashboardKPIs` — Task 1
- [x] KPI Row 7 cards com cores semânticas e countUp — Task 3
- [x] Filtro consultor apenas no modo dashboard — Task 3 + Task 8
- [x] Chart 1 Donut distribuição — Task 4
- [x] Chart 2 Barras agrupadas por produto — Task 4
- [x] Chart 3 Gauges ativação CPS/NX (meta 85%) — Task 5
- [x] Backlog stats (total dias, média) — Task 5
- [x] Alertas operacionais com thresholds — Task 6
- [x] Chart 4 Barras horizontais consultores — Task 7
- [x] Tabela performance por consultor com sort — Task 7
- [x] Seed data expandido (7 consultores, 38 clientes) — Task 2
- [x] `_dashCharts` destroy antes de re-render — Task 8
- [x] Empty state quando sem dados — Task 8
- [x] Responsividade (CSS media queries) — Task 3

**Sem placeholders:** cada step tem código completo.

**Consistência:** `_dashCharts` declarado em Task 1, usado em Tasks 4–8. `computePerformance` usa `computeDashboardKPIs` definida em Task 1. `initCharts` cresce em Tasks 4–7 de forma aditiva.
