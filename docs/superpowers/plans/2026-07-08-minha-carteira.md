# Minha Carteira — Role-Aware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestruturar Minha Carteira em 3 sub-abas (Agenda / Carteira / Desempenho) com conteúdo role-aware para CS vs Implantação, persona switcher de teste (Priscila / João), e feed card enriquecido.

**Architecture:** Tudo em `grv-cs-jornada.html` (SPA single-file). Estado novo `_carteira_tab` controla a sub-aba ativa. `getTipo(cid)` detecta o papel do consultor pelo campo `tipo` no objeto. As 3 sub-renders (`renderCarteiraAgenda`, view enriquecida, `renderCarteiraDesempenho`) são funções JS adicionadas após as existentes.

**Tech Stack:** HTML/CSS/JS inline, sem build. localStorage para persistência. Funções existentes reutilizadas: `isUrgente`, `calcHealthScore`, `calcProgresso`, `getDiasUltimoContato`, `getStatus`, `avatarGradiente`, `hsColor`, `toggleProjPop`, `closeProjPops`, `registrarContato`, `openProxAcaoModal`.

## Global Constraints

- Arquivo único: `grv-cs-jornada.html`
- Sem frameworks, sem build — JS/CSS inline
- Incrementar `DATA_V` de `'v4'` para `'v5'` para forçar re-seed (linha ~1797)
- Variáveis com `var`, funções com `function` (padrão do arquivo)
- Touch targets ≥ 44px, sem horizontal scroll, SVG para ícones
- Cor semântica: `#dc2626` = urgência/risco, `var(--primary)` = ações primárias

---

### Task 1: Mock data — personas Priscila e João

**Files:**
- Modify: `grv-cs-jornada.html` (~linha 1002 SEED_CONSULTORES, ~linha 1021 SEED_CLIENTES, ~linha 1797 DATA_V)

**Interfaces:**
- Produces: `getTipo('priscila')` → `'implantacao'`; `getTipo('joao')` → `'cs'`; `getMinhaCarteira('priscila')` → 7 clientes; `getMinhaCarteira('joao')` → 6 clientes

- [ ] **Step 1: Adicionar campo `tipo` em SEED_CONSULTORES e inserir Priscila e João**

Localizar `const SEED_CONSULTORES = [` (~linha 1002). Substituir o bloco inteiro:

```javascript
const SEED_CONSULTORES = [
  {id:'ana-paula',  nome:'Ana Paula Souza',   tipo:'implantacao'},
  {id:'carlos',     nome:'Carlos Menezes',    tipo:'implantacao'},
  {id:'maria',      nome:'Maria Lima',         tipo:'implantacao'},
  {id:'cristiano',  nome:'Cristiano Santos',  tipo:'implantacao'},
  {id:'felipe',     nome:'Felipe Alves',      tipo:'implantacao'},
  {id:'silvia',     nome:'Silvia Costa',      tipo:'implantacao'},
  {id:'severiano',  nome:'Severiano Rocha',   tipo:'implantacao'},
  {id:'priscila',   nome:'Priscila Mendes',   tipo:'implantacao'},
  {id:'joao',       nome:'João Ferreira',     tipo:'cs'},
];
```

- [ ] **Step 2: Adicionar clientes de João ao final de SEED_CLIENTES**

Localizar o fechamento de `SEED_CLIENTES` (o `];` que fecha o array, após o último cliente existente). Inserir antes do `];`:

```javascript
  // ── João (CS) ─────────────────────────────────────────────
  {
    id:'NEXTAR', projeto:'SAGP-00201', produto:'CPS', consultorId:'joao', segmento:'Saúde',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2025-06-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2025-06-01', dataInicioCS:'2025-09-01',
    csat:1.5, healthHistory:[{data:'2026-07-01', valor:50}],
    ativPlaybooks:[{
      id:'pb_nxt1', nome:'CS CPS', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_nxt1',nome:'Revisão trimestral',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_nxt2',nome:'Plano de expansão',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'SIGMA PRINT', projeto:'SAGP-00202', produto:'NX/IOT', consultorId:'joao', segmento:'Indústria',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2025-01-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2025-01-01', dataInicioCS:'2025-04-01',
    csat:2.0, healthHistory:[{data:'2026-07-01', valor:42}],
    ativPlaybooks:[{
      id:'pb_sig1', nome:'CS NX', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_sig1',nome:'Onboarding CS',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_sig2',nome:'Revisão mensal',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'OPTIX', projeto:'SAGP-00203', produto:'CPS', consultorId:'joao', segmento:'Serviços',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2025-03-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2025-03-01', dataInicioCS:'2025-06-01',
    csat:4.0, healthHistory:[{data:'2026-07-01', valor:62}],
    ativPlaybooks:[{
      id:'pb_opt1', nome:'CS CPS', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_opt1',nome:'QBR Q2',status:'concluida',dataLimite:'2026-06-30',dataConclusao:'2026-06-01',
          registros:[{id:'r_opt1',tipo:'contato',data:'2026-06-01',obs:'Reunião Q2'}]},
        {id:'at_opt2',nome:'Plano Q3',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'MAPEX', projeto:'SAGP-00204', produto:'CPS', consultorId:'joao', segmento:'Varejo',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2024-10-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2024-10-01', dataInicioCS:'2025-01-01',
    csat:4.2, proximaAcao:'Apresentar módulo analytics', healthHistory:[{data:'2026-07-01', valor:58}],
    ativPlaybooks:[{
      id:'pb_map1', nome:'CS CPS', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_map1',nome:'QBR Q1',status:'concluida',dataLimite:'2026-03-31',dataConclusao:'2026-03-28',
          registros:[{id:'r_map1',tipo:'contato',data:'2026-06-28',obs:'Ligação mensal'}]},
        {id:'at_map2',nome:'QBR Q3',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'SAUDETECH', projeto:'SAGP-00205', produto:'NX/IOT', consultorId:'joao', segmento:'Saúde',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2025-05-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2025-05-01', dataInicioCS:'2025-08-01',
    csat:4.0, proximaAcao:'Renovar contrato Q3', healthHistory:[{data:'2026-07-01', valor:72}],
    ativPlaybooks:[{
      id:'pb_sau1', nome:'CS NX', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_sau1',nome:'Onboarding CS',status:'concluida',dataLimite:'2025-09-01',dataConclusao:'2025-08-28',
          registros:[{id:'r_sau1',tipo:'contato',data:'2026-07-03',obs:'Alinhamento contrato'}]},
        {id:'at_sau2',nome:'Revisão semestral',status:'concluida',dataLimite:'2026-06-01',dataConclusao:'2026-05-30',registros:[]},
        {id:'at_sau3',nome:'Renovação Q3',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'BETAFORM', projeto:'SAGP-00206', produto:'CPS', consultorId:'joao', segmento:'Tecnologia',
    status:'cs_ativo', etapa:'CS Ativo', dataInicio:'2024-06-01', prazo:'2026-12-31',
    dataInicioImplantacao:'2024-06-01', dataInicioCS:'2024-09-01',
    csat:4.8, healthHistory:[{data:'2026-07-01', valor:88}],
    ativPlaybooks:[{
      id:'pb_bet1', nome:'CS CPS', fase:'cs', donoId:'joao', estado:'ativo',
      atividades:[
        {id:'at_bet1',nome:'Onboarding CS',status:'concluida',dataLimite:'2024-10-01',dataConclusao:'2024-09-28',registros:[]},
        {id:'at_bet2',nome:'Expansão módulo 2',status:'concluida',dataLimite:'2025-03-01',dataConclusao:'2025-02-20',registros:[]},
        {id:'at_bet3',nome:'Renovação anual',status:'concluida',dataLimite:'2025-09-01',dataConclusao:'2025-08-15',
          registros:[{id:'r_bet1',tipo:'contato',data:'2026-07-05',obs:'Check-in mensal'}]},
        {id:'at_bet4',nome:'Expansão módulo 3',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  // ── Priscila (Implantação) ─────────────────────────────────
  {
    id:'RIALTO', projeto:'SAGP-00301', produto:'CPS', consultorId:'priscila', segmento:'Varejo',
    status:'em_implantacao', etapa:'Evolução', dataInicio:'2026-01-15', prazo:'2026-05-30',
    dataInicioImplantacao:'2026-01-15', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:40}],
    ativPlaybooks:[{
      id:'pb_rial1', nome:'Implantação CPS', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_rial1',nome:'Kickoff',status:'concluida',dataLimite:'2026-02-01',dataConclusao:'2026-02-01',
          registros:[{id:'r_rial1',tipo:'contato',data:'2026-07-01',obs:'Revisão de progresso'}]},
        {id:'at_rial2',nome:'Parametrização',status:'concluida',dataLimite:'2026-03-01',dataConclusao:'2026-03-01',registros:[]},
        {id:'at_rial3',nome:'Treinamento',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_rial4',nome:'Go-live',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'FERREX', projeto:'SAGP-00302', produto:'NX/IOT', consultorId:'priscila', segmento:'Indústria',
    status:'em_implantacao', etapa:'Implantação', dataInicio:'2026-02-01', prazo:'2026-06-15',
    dataInicioImplantacao:'2026-02-01', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:35}],
    ativPlaybooks:[{
      id:'pb_fer1', nome:'Implantação NX', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_fer1',nome:'1ª Reunião',status:'concluida',dataLimite:'2026-02-15',dataConclusao:'2026-02-15',
          registros:[{id:'r_fer1',tipo:'contato',data:'2026-07-02',obs:'Acompanhamento'}]},
        {id:'at_fer2',nome:'Levantamento',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_fer3',nome:'Configuração',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'AQUAMAX', projeto:'SAGP-00303', produto:'CPS', consultorId:'priscila', segmento:'Saúde',
    status:'em_implantacao', etapa:'Engajamento', dataInicio:'2026-03-01', prazo:'2026-09-30',
    dataInicioImplantacao:'2026-03-01', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:55}],
    ativPlaybooks:[{
      id:'pb_aqu1', nome:'Implantação CPS', fase:'implantacao', donoId:'priscila', estado:'pausado',
      atividades:[
        {id:'at_aqu1',nome:'Kickoff',status:'concluida',dataLimite:'2026-03-15',dataConclusao:'2026-03-15',
          registros:[{id:'r_aqu1',tipo:'contato',data:'2026-06-25',obs:'Tentativa de retomada'}]},
        {id:'at_aqu2',nome:'Parametrização',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_aqu3',nome:'Treinamento',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'LUMIA', projeto:'SAGP-00304', produto:'CPS', consultorId:'priscila', segmento:'Tecnologia',
    status:'em_implantacao', etapa:'Evolução', dataInicio:'2026-02-15', prazo:'2026-08-15',
    dataInicioImplantacao:'2026-02-15', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:60}],
    ativPlaybooks:[{
      id:'pb_lum1', nome:'Implantação CPS', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_lum1',nome:'Kickoff',status:'concluida',dataLimite:'2026-03-01',dataConclusao:'2026-02-28',registros:[]},
        {id:'at_lum2',nome:'Parametrização',status:'concluida',dataLimite:'2026-04-01',dataConclusao:'2026-03-30',
          registros:[{id:'r_lum1',tipo:'contato',data:'2026-06-18',obs:'Status call'}]},
        {id:'at_lum3',nome:'Treinamento',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_lum4',nome:'Go-live',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'NORDIK', projeto:'SAGP-00305', produto:'NX/IOT', consultorId:'priscila', segmento:'Energia',
    status:'em_implantacao', etapa:'Conclusão', dataInicio:'2025-10-01', prazo:'2026-07-31',
    dataInicioImplantacao:'2025-10-01', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:85}],
    ativPlaybooks:[{
      id:'pb_nor1', nome:'Implantação NX', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_nor1',nome:'Kickoff',status:'concluida',dataLimite:'2025-10-15',dataConclusao:'2025-10-14',registros:[]},
        {id:'at_nor2',nome:'Levantamento',status:'concluida',dataLimite:'2025-11-01',dataConclusao:'2025-10-30',registros:[]},
        {id:'at_nor3',nome:'Configuração',status:'concluida',dataLimite:'2025-12-01',dataConclusao:'2025-11-28',registros:[]},
        {id:'at_nor4',nome:'Treinamento',status:'concluida',dataLimite:'2026-02-01',dataConclusao:'2026-01-28',registros:[]},
        {id:'at_nor5',nome:'Testes UAT',status:'concluida',dataLimite:'2026-04-01',dataConclusao:'2026-03-28',registros:[]},
        {id:'at_nor6',nome:'Go-live',status:'concluida',dataLimite:'2026-06-01',dataConclusao:'2026-05-30',registros:[]},
        {id:'at_nor7',nome:'Ajustes pós go-live',status:'concluida',dataLimite:'2026-06-30',dataConclusao:'2026-06-28',registros:[]},
        {id:'at_nor8',nome:'Treinamento avançado',status:'concluida',dataLimite:'2026-07-15',dataConclusao:'2026-07-05',registros:[]},
        {id:'at_nor9',nome:'Documentação',status:'concluida',dataLimite:'2026-07-20',dataConclusao:'2026-07-06',
          registros:[{id:'r_nor1',tipo:'contato',data:'2026-07-04',obs:'Validação final pré-handoff'}]},
        {id:'at_nor10',nome:'Handoff CS',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'TESTEK', projeto:'SAGP-00306', produto:'CPS', consultorId:'priscila', segmento:'Serviços',
    status:'em_implantacao', etapa:'Implantação', dataInicio:'2026-04-01', prazo:'2026-10-31',
    dataInicioImplantacao:'2026-04-01', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:72}],
    ativPlaybooks:[{
      id:'pb_tes1', nome:'Implantação CPS', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_tes1',nome:'Kickoff',status:'concluida',dataLimite:'2026-04-15',dataConclusao:'2026-04-14',
          registros:[{id:'r_tes1',tipo:'contato',data:'2026-07-06',obs:'Reunião semanal'}]},
        {id:'at_tes2',nome:'Levantamento',status:'concluida',dataLimite:'2026-05-15',dataConclusao:'2026-05-13',registros:[]},
        {id:'at_tes3',nome:'Configuração',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_tes4',nome:'Treinamento',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
  {
    id:'VIATECH', projeto:'SAGP-00307', produto:'NX/IOT', consultorId:'priscila', segmento:'Logística',
    status:'em_implantacao', etapa:'Evolução', dataInicio:'2026-03-15', prazo:'2026-09-15',
    dataInicioImplantacao:'2026-03-15', dataInicioCS:null,
    healthHistory:[{data:'2026-07-01', valor:68}],
    ativPlaybooks:[{
      id:'pb_via1', nome:'Implantação NX', fase:'implantacao', donoId:'priscila', estado:'ativo',
      atividades:[
        {id:'at_via1',nome:'Kickoff',status:'concluida',dataLimite:'2026-04-01',dataConclusao:'2026-03-30',registros:[]},
        {id:'at_via2',nome:'Levantamento',status:'concluida',dataLimite:'2026-04-30',dataConclusao:'2026-04-28',registros:[]},
        {id:'at_via3',nome:'Configuração',status:'concluida',dataLimite:'2026-06-01',dataConclusao:'2026-05-28',
          registros:[{id:'r_via1',tipo:'contato',data:'2026-07-07',obs:'Status parametrização'}]},
        {id:'at_via4',nome:'Treinamento equipe',status:'pendente',registros:[],checklist:[],anotacoes:[]},
        {id:'at_via5',nome:'Go-live',status:'pendente',registros:[],checklist:[],anotacoes:[]}
      ]
    }]
  },
```

- [ ] **Step 3: Incrementar DATA_V**

Localizar `var DATA_V = 'v4';` (~linha 1797). Alterar para:
```javascript
var DATA_V = 'v5';
```

- [ ] **Step 4: Verificar no browser**

Abrir `http://localhost:7799/grv-cs-jornada.html`. Abrir DevTools → Application → localStorage → limpar tudo (ou recarregar com Ctrl+Shift+R). Verificar no console:
```javascript
getConsultores().find(c => c.id === 'priscila')  // deve retornar {tipo:'implantacao'}
getMinhaCarteira('joao').length                  // deve retornar 6
getMinhaCarteira('priscila').length              // deve retornar 7
```

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): mock data Priscila (impl) e João (cs) com healthHistory"
```

---

### Task 2: CSS — persona switcher, tab bar, agenda cards, KPI chips

**Files:**
- Modify: `grv-cs-jornada.html` (bloco `<style>`, ao final do CSS existente, antes do `</style>`)

**Interfaces:**
- Produces: classes `.carteira-tab-bar`, `.ctab`, `.persona-switcher`, `.psw-pill`, `.agenda-wrap`, `.acard`, `.kpi-grid`, `.kpi-chip`

- [ ] **Step 1: Localizar o fim do bloco CSS**

Procurar no arquivo o comentário `/* ── CENTRAL DE ATENÇÃO` — o bloco de CSS da feature anterior termina alguns blocos depois. Inserir o novo bloco antes de `</style>`.

- [ ] **Step 2: Adicionar o CSS**

```css
/* ── MINHA CARTEIRA — NOVA UI ────────────────────────── */
.carteira-tab-bar{display:flex;gap:0;border-bottom:1px solid var(--border);padding:0 24px;background:var(--surface)}
.ctab{padding:10px 16px;font-size:12.5px;font-weight:500;color:var(--text3);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:color .15s,border-color .15s;white-space:nowrap;user-select:none}
.ctab:hover{color:var(--text)}
.ctab.active{color:var(--primary);border-bottom-color:var(--primary);font-weight:600}

.persona-switcher{display:flex;align-items:center;gap:3px;background:var(--bg);border-radius:20px;padding:3px}
.psw-pill{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:400;color:var(--text3);cursor:pointer;transition:background .15s,color .15s;white-space:nowrap}
.psw-pill.active{background:var(--primary);color:#fff;font-weight:600}

.agenda-wrap{padding:16px 24px;display:flex;flex-direction:column;gap:16px}
.agenda-secao-head{display:flex;align-items:center;gap:8px;padding:6px 0;cursor:pointer;user-select:none}
.agenda-secao-lbl{font-size:11px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.05em;flex:1}
.agenda-secao-cnt{font-size:10px;font-weight:700;padding:1px 6px;border-radius:10px}
.agenda-secao-cnt.urg{background:#dc2626;color:#fff}
.agenda-secao-cnt.neu{background:var(--border);color:var(--text2)}
.agenda-secao-chev{width:14px;height:14px;color:var(--text4);transition:transform .2s;flex-shrink:0}
.agenda-secao-chev.open{transform:rotate(180deg)}
.agenda-secao-body{display:flex;flex-direction:column;gap:8px}
.agenda-secao-body.collapsed{display:none}
.agenda-empty{padding:28px 16px;text-align:center;color:var(--text3);font-size:12px;display:flex;flex-direction:column;align-items:center;gap:8px}

.acard{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:var(--radius-sm);background:var(--surface);box-shadow:0 1px 3px rgba(0,0,0,.06);cursor:pointer;transition:box-shadow .15s;position:relative;overflow:hidden;min-height:52px}
.acard:hover{box-shadow:0 2px 8px rgba(0,0,0,.1)}
.acard-stripe{position:absolute;left:0;top:0;bottom:0;width:3px}
.acard-avatar{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;flex-shrink:0}
.acard-info{flex:1;min-width:0}
.acard-nome{font-size:13px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.acard-motivo{font-size:11px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}
.acard-right{display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0;margin-right:4px}
.acard-hs{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;border:2.5px solid}
.acard-trend{font-size:10px;font-weight:700}
.acard-prog{font-size:12px;font-weight:700}

.kpi-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:20px 24px 12px}
.kpi-chip{background:var(--surface);border-radius:var(--radius);padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.kpi-val{font-size:28px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1}
.kpi-lbl{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:.06em;color:var(--text3);margin-top:4px}
.kpi-destaques{padding:0 24px 20px}
.kpi-dest-titulo{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--text3);margin-bottom:8px}
.kpi-dest-item{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:var(--surface);border-radius:var(--radius-sm);box-shadow:0 1px 2px rgba(0,0,0,.05);margin-bottom:6px}
.kpi-dest-nome{font-size:13px;font-weight:600;color:var(--text)}
.kpi-dest-info{font-size:11px;color:var(--text3)}
@media (prefers-reduced-motion:reduce){.agenda-secao-chev{transition:none}}
```

- [ ] **Step 3: Verificar no browser**

Abrir o app. Inspecionar elementos — confirmar que as classes CSS são reconhecidas (sem erros no console, sem 404).

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): CSS tab bar, agenda cards, KPI chips, persona switcher"
```

---

### Task 3: Nav dropdown para Minha Carteira

**Files:**
- Modify: `grv-cs-jornada.html` (~linha 782, HTML do nav)

**Interfaces:**
- Produces: `setCarteiraTab('agenda')` chamado pelo dropdown; IDs `drop-ct-agenda`, `drop-ct-carteira`, `drop-ct-desempenho`

- [ ] **Step 1: Converter nav-item em nav-group**

Localizar o bloco exato (ler o arquivo para confirmar antes de editar):
```html
    <div class="nav-item" id="nav-carteira" data-route="carteira" onclick="navigate('carteira')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
      Minha Carteira
    </div>
```

Substituir por:
```html
    <div class="nav-group" id="nav-carteira-group">
      <div class="nav-item" id="nav-carteira" data-route="carteira" onclick="navigate('carteira')">
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
        Minha Carteira
        <svg style="width:10px;height:10px;margin-left:3px;opacity:.4;flex-shrink:0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>
      </div>
      <div class="nav-dropdown" id="carteira-dropdown">
        <div class="nav-drop-header">MINHA CARTEIRA</div>
        <div class="nav-drop-divider"></div>
        <div class="nav-drop-item" id="drop-ct-agenda" onclick="setCarteiraTab('agenda')">Agenda</div>
        <div class="nav-drop-item" id="drop-ct-carteira" onclick="setCarteiraTab('carteira')">Carteira</div>
        <div class="nav-drop-item" id="drop-ct-desempenho" onclick="setCarteiraTab('desempenho')">Desempenho</div>
      </div>
    </div>
```

- [ ] **Step 2: Verificar no browser**

Passar o mouse sobre "Minha Carteira" no topnav. Deve aparecer dropdown com 3 itens. Clicar em cada um — no momento ainda não funciona (função `setCarteiraTab` ainda não existe), mas o dropdown deve abrir/fechar.

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): nav dropdown com Agenda / Carteira / Desempenho"
```

---

### Task 4: State + helpers (getTipo, getHealthTrend, isUrgente, setCarteiraTab)

**Files:**
- Modify: `grv-cs-jornada.html` (~linha 1925 `isUrgente`, ~linha 3228 área de declarações de estado da carteira)

**Interfaces:**
- Produces: `getTipo(cid)` → `'cs'|'implantacao'`; `getHealthTrend(c)` → `{arrow,color}|null`; `_carteira_tab`; `setCarteiraTab(tab)`; `switchPersona(id)`

- [ ] **Step 1: Estender `isUrgente` para incluir pausado**

Localizar a função `isUrgente` (~linha 1925):
```javascript
function isUrgente(c) {
  if (c.status !== 'cs_ativo') {
    return getStatus(c) === 'Atrasado' || getDiasUltimoContato(c) > 14;
  }
  var h = calcHealthScore(c);
  return (h !== null && h < 40) || getDiasUltimoContato(c) > 30;
}
```

Substituir por:
```javascript
function isUrgente(c) {
  if (c.status !== 'cs_ativo') {
    var cid = getConsultorAtivo();
    var pb = (c.ativPlaybooks || []).find(function(p){ return p.donoId === cid; });
    var pausado = pb && pb.estado === 'pausado';
    return getStatus(c) === 'Atrasado' || getDiasUltimoContato(c) > 14 || pausado;
  }
  var h = calcHealthScore(c);
  return (h !== null && h < 40) || getDiasUltimoContato(c) > 30;
}
```

- [ ] **Step 2: Adicionar state e helpers após `_carteira_view` (~linha 3229)**

Localizar:
```javascript
let _carteira_view = (function(){const v=localStorage.getItem(CARTEIRA_VIEW_KEY);return(v==='feed'||v==='kanban')?v:'feed';})();
```

Inserir DEPOIS dessa linha:

```javascript
const CARTEIRA_TAB_KEY = 'grv_cs_tab_carteira';
var _carteira_tab = localStorage.getItem(CARTEIRA_TAB_KEY) || 'agenda';
var _agenda_collapsed = new Set([1, 2]);

function getTipo(cid) {
  var c = getConsultores().find(function(x){ return x.id === cid; });
  return (c && c.tipo) || 'implantacao';
}

function getHealthTrend(c) {
  var hist = c.healthHistory;
  if (!hist || !hist.length) return null;
  var prev = hist[hist.length - 1].valor;
  var curr = calcHealthScore(c);
  if (curr === null) return null;
  var diff = curr - prev;
  if (diff >= 5)  return {arrow:'↑', color:'var(--green)'};
  if (diff <= -5) return {arrow:'↓', color:'#dc2626'};
  return {arrow:'→', color:'var(--text4)'};
}

function setCarteiraTab(tab) {
  _carteira_tab = tab;
  _agenda_collapsed = new Set([1, 2]);
  localStorage.setItem(CARTEIRA_TAB_KEY, tab);
  if (location.hash === '#carteira') {
    renderCarteira();
  } else {
    navigate('carteira');
  }
}

function switchPersona(id) {
  setConsultorAtivo(id);
  _agenda_collapsed = new Set([1, 2]);
  updateSidebarConsultor();
  renderCarteira();
}

function getCarteiraViewKey() {
  return 'grv_cs_view_carteira_' + getTipo(getConsultorAtivo());
}

function setCarteiraView(v) {
  localStorage.setItem(getCarteiraViewKey(), v);
  renderCarteira();
}
```

- [ ] **Step 3: Verificar no console**

```javascript
getTipo('joao')      // → 'cs'
getTipo('priscila')  // → 'implantacao'
getTipo('ana-paula') // → 'implantacao'
getHealthTrend(getMinhaCarteira('joao')[0])  // → {arrow:'↓', color:'#dc2626'} (NEXTAR caiu de 50 para ~32)
```

- [ ] **Step 4: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): state _carteira_tab, getTipo, getHealthTrend, isUrgente+pausado"
```

---

### Task 5: Aba Agenda

**Files:**
- Modify: `grv-cs-jornada.html` (JS, após `renderCarteiraKanban` ~linha 3323)

**Interfaces:**
- Consumes: `isUrgente(c)`, `getHealthTrend(c)`, `calcHealthScore`, `calcProgresso`, `getDiasUltimoContato`, `getStatus`, `hsColor`, `avatarGradiente`, `toggleProjPop`, `registrarContato`, `openProxAcaoModal`
- Produces: `renderCarteiraAgenda(clientes, cid, tipo)` → HTML string; `toggleAgendaSecao(idx)`; `renderAgendaCard(c, cid, tipo)` → HTML string

- [ ] **Step 1: Inserir as funções após `renderCarteiraKanban`**

Localizar o fim de `renderCarteiraKanban` (a linha `return '<div class="ck-wrap">' + cols + '</div>';` seguida do `}`). Inserir DEPOIS:

```javascript
function toggleAgendaSecao(idx) {
  if (_agenda_collapsed.has(idx)) _agenda_collapsed.delete(idx);
  else _agenda_collapsed.add(idx);
  var body = document.getElementById('asec-body-' + idx);
  var chev = document.getElementById('asec-chev-' + idx);
  if (body) body.classList.toggle('collapsed');
  if (chev) chev.classList.toggle('open');
}

function renderAgendaCard(c, cid, tipo) {
  var meusPbs = (c.ativPlaybooks || []).filter(function(pb){ return pb.donoId === cid; });
  var nome = c.id || c.projeto || '?';
  var urg = isUrgente(c);
  var stripeColor = urg ? '#dc2626' : 'var(--green)';

  var motivo = '';
  if (tipo === 'cs') {
    var h = calcHealthScore(c);
    var dias = getDiasUltimoContato(c);
    if (h !== null && h < 40) {
      var tr0 = getHealthTrend(c);
      motivo = 'Health ' + h + (tr0 ? ' ' + tr0.arrow : '');
    } else if (dias !== null && dias > 30) {
      motivo = dias + 'd sem contato';
    } else if (c.proximaAcao) {
      motivo = c.proximaAcao;
    }
  } else {
    var pb0 = meusPbs[0];
    var pausado0 = pb0 && pb0.estado === 'pausado';
    var dias2 = getDiasUltimoContato(c);
    if (getStatus(c) === 'Atrasado' && c.prazo) {
      var diasAtr = Math.round((new Date() - new Date(c.prazo)) / 86400000);
      motivo = 'Atrasado · ' + diasAtr + 'd';
      stripeColor = '#dc2626';
    } else if (pausado0) {
      motivo = 'Pausado' + (dias2 !== null ? ' · ' + dias2 + 'd sem contato' : '');
      stripeColor = 'var(--yellow)';
    } else if (dias2 !== null && dias2 > 14) {
      motivo = dias2 + 'd sem contato';
      stripeColor = 'var(--yellow)';
    } else {
      motivo = calcProgresso(meusPbs) + '% concluído';
    }
  }

  var rightHtml = '';
  if (tipo === 'cs') {
    var hv = calcHealthScore(c);
    var hc = hsColor(hv);
    var tr = getHealthTrend(c);
    rightHtml = '<div class="acard-hs" style="border-color:' + hc + ';color:' + hc + '">' + (hv !== null ? hv : '—') + '</div>' +
      (tr ? '<span class="acard-trend" style="color:' + tr.color + '">' + tr.arrow + '</span>' : '');
  } else {
    var prog = calcProgresso(meusPbs);
    var pc = prog >= 90 ? 'var(--green)' : prog >= 50 ? 'var(--yellow)' : 'var(--text3)';
    rightHtml = '<span class="acard-prog" style="color:' + pc + '">' + prog + '%</span>';
  }

  var dotHtml = urg
    ? '<div class="proj-ac" onclick="event.stopPropagation()">' +
        '<button class="proj-dot" onclick="toggleProjPop(event,\'ap-ag-' + c.id + '\',\'ab-ag-' + c.id + '\')" id="ab-ag-' + c.id + '">···</button>' +
        '<div class="proj-pop" id="ap-ag-' + c.id + '">' +
          '<div class="proj-pop-head">' + nome + '</div>' +
          '<div class="proj-pop-item prim" onclick="registrarContato(\'' + c.id + '\')">Registrar contato</div>' +
          '<div class="proj-pop-item" onclick="openProxAcaoModal(\'' + c.id + '\')">Atualizar próxima ação</div>' +
          '<div class="proj-pop-item" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">Abrir cliente</div>' +
        '</div>' +
      '</div>'
    : '';

  return '<div class="acard" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">' +
    '<div class="acard-stripe" style="background:' + stripeColor + '"></div>' +
    '<div class="acard-avatar" style="background:' + avatarGradiente(nome) + '">' + nome[0].toUpperCase() + '</div>' +
    '<div class="acard-info">' +
      '<div class="acard-nome">' + nome + '</div>' +
      (motivo ? '<div class="acard-motivo">' + motivo + '</div>' : '') +
    '</div>' +
    '<div class="acard-right">' + rightHtml + '</div>' +
    dotHtml +
  '</div>';
}

function renderAgendaSecao(idx, label, items, cid, tipo, isUrgent) {
  var collapsed = _agenda_collapsed.has(idx);
  var cntClass = isUrgent ? 'urg' : 'neu';
  return '<div>' +
    '<div class="agenda-secao-head" onclick="event.stopPropagation();toggleAgendaSecao(' + idx + ')">' +
      '<span class="agenda-secao-lbl">' + label + '</span>' +
      '<span class="agenda-secao-cnt ' + cntClass + '">' + items.length + '</span>' +
      '<svg class="agenda-secao-chev' + (collapsed ? '' : ' open') + '" id="asec-chev-' + idx + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>' +
    '</div>' +
    '<div class="agenda-secao-body' + (collapsed ? ' collapsed' : '') + '" id="asec-body-' + idx + '">' +
      (items.length ? items.map(function(c){ return renderAgendaCard(c, cid, tipo); }).join('') :
        '<div style="font-size:12px;color:var(--text3);padding:8px 0">Nenhum item.</div>') +
    '</div>' +
  '</div>';
}

function renderCarteiraAgenda(clientes, cid, tipo) {
  var meusPbsFn = function(c){ return (c.ativPlaybooks||[]).filter(function(pb){ return pb.donoId===cid; }); };
  var sec1, sec2, sec3;

  if (tipo === 'cs') {
    sec1 = clientes.filter(function(c){ return isUrgente(c); })
      .sort(function(a,b){ return (calcHealthScore(a)||99) - (calcHealthScore(b)||99); });
    sec2 = clientes.filter(function(c){ return !isUrgente(c) && c.proximaAcao; });
    sec3 = clientes.filter(function(c){ return !isUrgente(c) && !c.proximaAcao; })
      .sort(function(a,b){ return (calcHealthScore(a)||99) - (calcHealthScore(b)||99); });
  } else {
    sec1 = clientes.filter(function(c){ return isUrgente(c); })
      .sort(function(a,b){ return calcProgresso(meusPbsFn(a)) - calcProgresso(meusPbsFn(b)); });
    sec2 = clientes.filter(function(c){ return !isUrgente(c) && calcProgresso(meusPbsFn(c)) >= 90; });
    sec3 = clientes.filter(function(c){ return !isUrgente(c) && calcProgresso(meusPbsFn(c)) < 90; })
      .sort(function(a,b){ return calcProgresso(meusPbsFn(a)) - calcProgresso(meusPbsFn(b)); });
  }

  var emptyState = '<div class="agenda-empty">' +
    '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--green)" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' +
    'Sua carteira está sob controle hoje.' +
  '</div>';

  var secLabel1 = 'Atenção agora';
  var secLabel2 = tipo === 'cs' ? 'Próxima ação pendente' : 'Pronto para handoff';
  var secLabel3 = tipo === 'cs' ? 'Em dia' : 'Em andamento';

  var sec1Html = sec1.length
    ? sec1.map(function(c){ return renderAgendaCard(c, cid, tipo); }).join('')
    : emptyState;

  return '<div class="agenda-wrap">' +
    '<div>' +
      '<div class="agenda-secao-head" onclick="event.stopPropagation();toggleAgendaSecao(0)">' +
        '<span class="agenda-secao-lbl">' + secLabel1 + '</span>' +
        (sec1.length ? '<span class="agenda-secao-cnt urg">' + sec1.length + '</span>' : '') +
        '<svg class="agenda-secao-chev open" id="asec-chev-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M6 9l6 6 6-6"/></svg>' +
      '</div>' +
      '<div class="agenda-secao-body" id="asec-body-0">' + sec1Html + '</div>' +
    '</div>' +
    renderAgendaSecao(1, secLabel2, sec2, cid, tipo, false) +
    renderAgendaSecao(2, secLabel3, sec3, cid, tipo, false) +
  '</div>';
}
```

- [ ] **Step 2: Verificar no browser**

Ir para Minha Carteira → dropdown → Agenda. Com João: deve ver NEXTAR, SIGMA PRINT, OPTIX em "Atenção agora". Com Priscila: deve ver RIALTO, FERREX, AQUAMAX, LUMIA em "Atenção agora" e NORDIK em "Pronto para handoff".

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): aba Agenda com fila de prioridade role-aware"
```

---

### Task 6: Aba Carteira enriquecida (feed + kanban CS)

**Files:**
- Modify: `grv-cs-jornada.html` (~linha 3246 `renderFeedCard`, após `renderCarteiraKanban`)

**Interfaces:**
- Consumes: `getHealthTrend(c)`, `getTipo(cid)`, `getCarteiraViewKey()`
- Produces: `renderCarteiraKanbanCS(clientes, cid)` → HTML; `renderFeedCard` enriquecido; `filtrarCarteira` atualizado

- [ ] **Step 1: Enriquecer `renderFeedCard`**

Localizar em `renderFeedCard` a linha:
```javascript
  const hs  = calcHealthScore(c);
```

Inserir ANTES dela:
```javascript
  const pausado = meusPbs.some(pb => pb.estado === 'pausado');
```

Localizar a linha:
```javascript
  const hsCircle = '<div style="width:36px;height:36px;border-radius:50%;border:2.5px solid ' + hsC + ';display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;color:' + hsC + ';flex-shrink:0;margin-bottom:4px">' + hs + '</div>';
```

Inserir APÓS ela:
```javascript
  const tr = getHealthTrend(c);
  const trendHtml = tr ? '<span style="font-size:10px;font-weight:700;color:' + tr.color + '">' + tr.arrow + '</span>' : '';
  const acaoHtml = c.proximaAcao
    ? '<div style="font-size:11px;font-style:italic;color:var(--text3);max-width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px">' + c.proximaAcao + '</div>'
    : '';
  const pausadoBadge = pausado
    ? '<span style="font-size:10px;padding:1px 6px;border-radius:8px;background:rgba(160,174,192,.15);color:var(--text3)">Pausado</span>'
    : '';
```

No bloco de retorno de `renderFeedCard`, localizar:
```javascript
        '<div class="fc-meta">' + fase + ' · ' + prog + '%</div>' +
      '</div>' +
```
Substituir por:
```javascript
        '<div class="fc-meta">' + fase + ' · ' + prog + '%</div>' +
        acaoHtml +
      '</div>' +
```

Localizar dentro de `fc-right`:
```javascript
        hsCircle +
        '<span class="status-badge b-' + st + '">' + statusLabel(st) + '</span>' +
```
Substituir por:
```javascript
        hsCircle +
        trendHtml +
        '<span class="status-badge b-' + st + '">' + statusLabel(st) + '</span>' +
        pausadoBadge +
```

- [ ] **Step 2: Adicionar `renderCarteiraKanbanCS`**

Após o fechamento de `renderCarteiraKanban`, inserir:

```javascript
function renderCarteiraKanbanCS(clientes, cid) {
  var tiers = [
    {label:'Crítico', min:0, max:39, color:'#dc2626'},
    {label:'Atenção', min:40, max:70, color:'var(--yellow)'},
    {label:'Saudável', min:71, max:100, color:'var(--green)'}
  ];
  var cols = tiers.map(function(tier) {
    var items = clientes.filter(function(c) {
      var h = calcHealthScore(c);
      return h !== null && h >= tier.min && h <= tier.max;
    });
    var cards = items.map(function(c) {
      var h = calcHealthScore(c);
      var nome = c.id || c.projeto || '?';
      return '<div class="ck-card" onclick="navigate(\'cliente/' + encodeURIComponent(c.id) + '\')">' +
        '<div class="ck-stripe" style="background:' + tier.color + '"></div>' +
        '<div class="ck-nome">' + nome + '</div>' +
        '<div class="ck-fase">' + (c.proximaAcao || '—') + '</div>' +
        '<div class="ck-foot">' +
          '<span class="ck-pct" style="color:' + tier.color + '">' + (h !== null ? h : '—') + '</span>' +
          '<span class="status-badge" style="background:' + tier.color + '22;color:' + tier.color + '">' + tier.label + '</span>' +
        '</div>' +
      '</div>';
    }).join('');
    return '<div class="ck-col">' +
      '<div class="ck-col-head" style="border-top:2px solid ' + tier.color + '">' +
        '<span class="ck-col-lbl" style="color:' + tier.color + '">' + tier.label + '</span>' +
        '<span class="ck-col-cnt">' + items.length + '</span>' +
      '</div>' +
      (cards || '<div style="font-size:11px;color:var(--text4);padding:8px 0">Vazio</div>') +
    '</div>';
  }).join('');
  return '<div class="ck-wrap">' + cols + '</div>';
}
```

- [ ] **Step 3: Atualizar `filtrarCarteira` para usar a view key correta e kanban CS**

Localizar a função `filtrarCarteira` (~linha 3325). Substituir o bloco `const view = ...` e `const body = ...` no final da função:

Localizar:
```javascript
  const view = localStorage.getItem(CARTEIRA_VIEW_KEY) || 'feed';
  const body = document.getElementById('carteira-body');
  if (body) body.innerHTML = view === 'feed' ? renderCarteiraFeed(cls, cid) : renderCarteiraKanban(cls, cid);
```
Substituir por:
```javascript
  var tipo = getTipo(cid);
  var view = localStorage.getItem(getCarteiraViewKey()) || 'feed';
  var body = document.getElementById('carteira-body');
  if (body) body.innerHTML = view === 'feed'
    ? renderCarteiraFeed(cls, cid)
    : (tipo === 'cs' ? renderCarteiraKanbanCS(cls, cid) : renderCarteiraKanban(cls, cid));
```

- [ ] **Step 4: Verificar no browser**

Ir para Minha Carteira → Carteira (aba). Com João → Feed deve mostrar trend arrow e próxima ação nos cards. Kanban deve ter 3 colunas (Crítico / Atenção / Saudável). Com Priscila → Kanban normal por etapas, cards de AQUAMAX devem mostrar badge "Pausado".

- [ ] **Step 5: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): feed card enriquecido + kanban CS por tier de saúde"
```

---

### Task 7: Aba Desempenho

**Files:**
- Modify: `grv-cs-jornada.html` (JS, após `renderCarteiraAgenda`)

**Interfaces:**
- Consumes: `calcHealthScore`, `getDiasUltimoContato`, `calcCsatAtual`, `isUrgente`, `calcProgresso`, `getStatus`, `getHealthTrend`
- Produces: `renderCarteiraDesempenho(clientes, cid, tipo)` → HTML string

- [ ] **Step 1: Inserir `renderKpiChip` e `renderCarteiraDesempenho` após `renderCarteiraAgenda`**

```javascript
function renderKpiChip(valor, label, cor) {
  return '<div class="kpi-chip"><div class="kpi-val" style="color:' + cor + '">' + valor + '</div><div class="kpi-lbl">' + label + '</div></div>';
}

function renderCarteiraDesempenho(clientes, cid, tipo) {
  var html = '';

  if (tipo === 'cs') {
    var hScores = clientes.map(function(c){ return calcHealthScore(c); }).filter(function(h){ return h !== null; });
    var hMedio  = hScores.length ? Math.round(hScores.reduce(function(s,h){ return s+h; },0)/hScores.length) : null;
    var hCor    = hMedio === null ? 'var(--text3)' : hMedio < 50 ? '#dc2626' : hMedio >= 70 ? 'var(--green)' : 'var(--text)';

    var contMes = clientes.filter(function(c){ var d=getDiasUltimoContato(c); return d!==null && d<=30; }).length;
    var pctCont = clientes.length ? Math.round(contMes/clientes.length*100) : 0;
    var contCor = pctCont < 60 ? 'var(--yellow)' : pctCont >= 80 ? 'var(--green)' : 'var(--text)';

    var csats   = clientes.map(function(c){ return calcCsatAtual(c); }).filter(function(v){ return v!==null; });
    var csatMed = csats.length ? Math.round(csats.reduce(function(s,v){ return s+v; },0)/csats.length*10)/10 : null;
    var csatCor = csatMed === null ? 'var(--text3)' : csatMed <= 3 ? '#dc2626' : csatMed >= 4 ? 'var(--green)' : 'var(--text)';

    var emRisco = clientes.filter(isUrgente).length;
    var riscoCor = emRisco > 0 ? '#dc2626' : 'var(--green)';

    html += '<div class="kpi-grid">' +
      renderKpiChip(hMedio !== null ? hMedio : '—', 'Health médio', hCor) +
      renderKpiChip(pctCont + '%', 'Contactados no mês', contCor) +
      renderKpiChip(csatMed !== null ? csatMed : '—', 'CSAT médio', csatCor) +
      renderKpiChip(emRisco, 'Em risco', riscoCor) +
    '</div>';

    var comTrend = clientes
      .filter(function(c){ return c.healthHistory && c.healthHistory.length; })
      .map(function(c){ return {c:c, diff: (calcHealthScore(c)||0) - c.healthHistory[c.healthHistory.length-1].valor}; })
      .sort(function(a,b){ return a.diff - b.diff; })
      .slice(0,3);

    var destItems = comTrend.length
      ? comTrend.map(function(item){
          return '<div class="kpi-dest-item"><span class="kpi-dest-nome">' + (item.c.id||'?') + '</span>' +
            '<span class="kpi-dest-info" style="color:#dc2626">health ' + (calcHealthScore(item.c)||'?') + ' ↓ ' + Math.abs(item.diff) + '</span></div>';
        }).join('')
      : '<div style="font-size:12px;color:var(--text3);padding:8px 0">Nada crítico esta semana.</div>';

    html += '<div class="kpi-destaques"><div class="kpi-dest-titulo">Maior queda de health</div>' + destItems + '</div>';

  } else {
    var meusPbsFn = function(c){ return (c.ativPlaybooks||[]).filter(function(pb){ return pb.donoId===cid; }); };

    var emDia    = clientes.filter(function(c){ return getStatus(c) !== 'Atrasado'; }).length;
    var pctEmDia = clientes.length ? Math.round(emDia/clientes.length*100) : 0;
    var emDiaCor = pctEmDia < 70 ? '#dc2626' : pctEmDia >= 90 ? 'var(--green)' : 'var(--text)';

    var progs    = clientes.map(function(c){ return calcProgresso(meusPbsFn(c)); });
    var progMed  = progs.length ? Math.round(progs.reduce(function(s,p){ return s+p; },0)/progs.length) : 0;

    var pausados = clientes.filter(function(c){
      var pb = (c.ativPlaybooks||[]).find(function(p){ return p.donoId===cid; });
      return pb && pb.estado === 'pausado';
    }).length;
    var pausCor  = pausados > 0 ? 'var(--yellow)' : 'var(--green)';

    var handoff  = clientes.filter(function(c){ return calcProgresso(meusPbsFn(c)) >= 90; }).length;
    var handCor  = handoff > 0 ? 'var(--green)' : 'var(--text3)';

    html += '<div class="kpi-grid">' +
      renderKpiChip(pctEmDia + '%', 'Projetos em dia', emDiaCor) +
      renderKpiChip(progMed + '%', 'Progresso médio', 'var(--text)') +
      renderKpiChip(pausados, 'Pausados', pausCor) +
      renderKpiChip(handoff, 'Prontos p/ handoff', handCor) +
    '</div>';

    var criticos = clientes.filter(isUrgente)
      .sort(function(a,b){ return calcProgresso(meusPbsFn(a)) - calcProgresso(meusPbsFn(b)); })
      .slice(0,3);

    var destImpl = criticos.length
      ? criticos.map(function(c){
          var pb  = (c.ativPlaybooks||[]).find(function(p){ return p.donoId===cid; });
          var psd = pb && pb.estado === 'pausado';
          var info;
          if (getStatus(c) === 'Atrasado' && c.prazo) {
            var d = Math.round((new Date() - new Date(c.prazo))/86400000);
            info = 'Atrasado · ' + d + 'd';
          } else if (psd) {
            info = 'Pausado';
          } else {
            info = getDiasUltimoContato(c) + 'd sem contato';
          }
          return '<div class="kpi-dest-item"><span class="kpi-dest-nome">' + (c.id||'?') + '</span>' +
            '<span class="kpi-dest-info" style="color:#dc2626">' + info + '</span></div>';
        }).join('')
      : '<div style="font-size:12px;color:var(--text3);padding:8px 0">Nada crítico esta semana.</div>';

    html += '<div class="kpi-destaques"><div class="kpi-dest-titulo">Projetos críticos</div>' + destImpl + '</div>';
  }

  return html;
}
```

- [ ] **Step 2: Verificar no browser**

Ir para Minha Carteira → Desempenho. Com João: deve mostrar 4 KPI chips (Health médio ~44, Contactados no mês %, CSAT médio, Em risco 3) + lista com NEXTAR e SIGMA PRINT mostrando queda. Com Priscila: chips (Projetos em dia %, Progresso médio, Pausados 1, Prontos p/ handoff 1) + RIALTO e FERREX como críticos.

- [ ] **Step 3: Commit**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): aba Desempenho com KPI chips role-aware"
```

---

### Task 8: Wire up renderCarteira — header + tab bar + dispatch

**Files:**
- Modify: `grv-cs-jornada.html` (função `renderCarteira` ~linha 3346)

**Interfaces:**
- Consumes: todas as funções criadas nas tasks anteriores
- Produces: `renderCarteira()` completo com persona switcher, tab bar e dispatch correto

- [ ] **Step 1: Substituir `renderCarteira` completo**

Localizar a função `renderCarteira` inteira (~linha 3346 até o `}`). Substituir por:

```javascript
function renderCarteira() {
  var cid       = getConsultorAtivo();
  var tipo      = getTipo(cid);
  var nomeAtivo = (getConsultores().find(function(c){ return c.id === cid; }) || {}).nome || cid;
  var clientes  = getMinhaCarteira(cid);
  var tab       = _carteira_tab;
  var view      = localStorage.getItem(getCarteiraViewKey()) || 'feed';
  var atr       = clientes.filter(function(c){ return c.status !== 'cs_ativo' && getStatusCliente(c,cid) === 'atrasado'; }).length;
  var sec       = document.getElementById('sec-carteira');
  if (!sec) return;

  // Persona switcher (só mostra se Priscila e João existem)
  var allConsult = getConsultores();
  var hasPri = allConsult.some(function(c){ return c.id === 'priscila'; });
  var hasJoa = allConsult.some(function(c){ return c.id === 'joao'; });
  var switcherHtml = (hasPri && hasJoa)
    ? '<div class="persona-switcher">' +
        '<div class="psw-pill' + (cid==='priscila'?' active':'') + '" onclick="switchPersona(\'priscila\')">Priscila</div>' +
        '<div class="psw-pill' + (cid==='joao'?' active':'') + '" onclick="switchPersona(\'joao\')">João</div>' +
      '</div>'
    : '';

  // Atualizar drop-items do nav
  ['agenda','carteira','desempenho'].forEach(function(t) {
    var el = document.getElementById('drop-ct-' + t);
    if (el) el.classList.toggle('active', tab === t);
  });

  // Header
  var header = '<div style="padding:16px 24px 12px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)">' +
    '<div>' +
      '<div style="font-size:18px;font-weight:800;color:var(--text)">Minha Carteira</div>' +
      '<div style="font-size:11px;color:var(--text3);margin-top:2px">' + nomeAtivo + ' · ' + clientes.length + ' clientes' +
        (atr ? ' · <span style="color:var(--red);font-weight:700">' + atr + ' atrasado' + (atr!==1?'s':'') + '</span>' : '') +
      '</div>' +
    '</div>' +
    switcherHtml +
  '</div>';

  // Tab bar
  var tabBar = '<div class="carteira-tab-bar">' +
    [{key:'agenda',label:'Agenda'},{key:'carteira',label:'Carteira'},{key:'desempenho',label:'Desempenho'}]
    .map(function(t){
      return '<div class="ctab' + (tab===t.key?' active':'') + '" onclick="setCarteiraTab(\'' + t.key + '\')">' + t.label + '</div>';
    }).join('') +
  '</div>';

  // Body
  var body = '';
  if (tab === 'agenda') {
    body = renderCarteiraAgenda(clientes, cid, tipo);
  } else if (tab === 'desempenho') {
    body = renderCarteiraDesempenho(clientes, cid, tipo);
  } else {
    body =
      '<div style="padding:12px 24px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--border);flex-wrap:wrap">' +
        '<div style="display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);padding:7px 12px;min-width:220px">' +
          '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--text4)" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>' +
          '<input type="text" placeholder="Buscar cliente..." id="carteira-busca" oninput="filtrarCarteira()" style="border:none;outline:none;font-size:12px;color:var(--text);width:100%;background:transparent"/>' +
        '</div>' +
        '<select id="carteira-status" onchange="filtrarCarteira()" style="border:1px solid var(--border);border-radius:var(--radius-sm);padding:7px 10px;font-size:12px;color:var(--text2);background:var(--surface)">' +
          '<option value="">Todos os status</option>' +
          '<option value="atrasado">Atrasados</option>' +
          '<option value="atencao">Atenção</option>' +
          '<option value="em_ordem">Em ordem</option>' +
          '<option value="inicio">Início</option>' +
          '<option value="cs_ativo">CS Ativo</option>' +
        '</select>' +
        '<div class="view-toggle" style="margin-left:auto">' +
          '<button class="vt-btn' + (view==='feed'?' active':'') + '" onclick="setCarteiraView(\'feed\')">' +
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/></svg>Feed' +
          '</button>' +
          '<button class="vt-btn' + (view==='kanban'?' active':'') + '" onclick="setCarteiraView(\'kanban\')">' +
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="13" rx="1"/><rect x="17" y="3" width="5" height="9" rx="1"/></svg>Kanban' +
          '</button>' +
        '</div>' +
      '</div>' +
      '<div id="carteira-body">' +
        (view === 'feed'
          ? renderCarteiraFeed(clientes, cid)
          : (tipo === 'cs' ? renderCarteiraKanbanCS(clientes, cid) : renderCarteiraKanban(clientes, cid))) +
      '</div>';
  }

  sec.innerHTML = header + tabBar + body;
}
```

- [ ] **Step 2: Remover `setCarteiraView` antiga (se existir duplicata)**

Procurar se ainda existe a função `setCarteiraView` antiga logo após `renderCarteira`. Se existir, remover a versão antiga (a nova foi adicionada na Task 4).

- [ ] **Step 3: Verificar fluxo completo no browser**

Checklist de verificação:
- [ ] Minha Carteira abre na aba Agenda por padrão
- [ ] Persona switcher mostra "Priscila" e "João"; clicar alterna a view
- [ ] João → Agenda: NEXTAR, SIGMA PRINT, OPTIX em "Atenção agora"; MAPEX, SAUDETECH em "Próxima ação pendente"
- [ ] Priscila → Agenda: RIALTO, FERREX, AQUAMAX, LUMIA em "Atenção agora"; NORDIK em "Pronto para handoff"
- [ ] Seções 2 e 3 começam colapsadas, clique expande/colapsa
- [ ] Botão `···` nos urgentes abre popover com 3 ações
- [ ] João → Carteira → Feed: cards com trend arrow (↓ em NEXTAR/SIGMA)
- [ ] João → Carteira → Kanban: colunas Crítico/Atenção/Saudável
- [ ] Priscila → Carteira → Feed: AQUAMAX tem badge "Pausado"
- [ ] Priscila → Carteira → Kanban: colunas por etapa (normal)
- [ ] João → Desempenho: 4 KPI chips + lista de clientes com queda
- [ ] Priscila → Desempenho: 4 KPI chips + RIALTO/FERREX como críticos
- [ ] Tab bar: clicar em cada tab navega corretamente
- [ ] Nav dropdown hover abre com 3 itens; item ativo destacado

- [ ] **Step 4: Commit final**

```bash
git add grv-cs-jornada.html
git commit -m "feat(carteira): renderCarteira completo — header, tab bar, persona switcher, dispatch role-aware"
```
