# Spec — Health Score + NPS + CSAT Histórico + Last Touch

**Data:** 2026-07-06
**Escopo:** `grv-cs-jornada.html` — quatro sinais de saúde do cliente em ordem de utilidade

---

## Prioridade de implementação

1. **Last Touch** — dias desde último contato (mais fácil, impacto imediato)
2. **Health Score** — score composto 0–100 visível em todos os cards
3. **CSAT histórico** — histórico de pesquisas de satisfação
4. **NPS** — Net Promoter Score por cliente

---

## 1. Last Touch (Último Contato)

### Modelo de dados

Calculado dinamicamente — sem campo novo. Usa a data mais recente entre:
- Último `registro.data` em qualquer atividade do cliente
- Último `registro.data` no array `cliente.registros`

```javascript
function getDiasUltimoContato(cliente) {
  const hoje = new Date(); hoje.setHours(0,0,0,0);
  let ultima = null;
  const checkData = d => { if (d) { const dt = new Date(d); if (!ultima || dt > ultima) ultima = dt; } };
  (cliente.registros||[]).forEach(r => checkData(r.data));
  (cliente.ativPlaybooks||[]).forEach(pb =>
    (pb.atividades||[]).forEach(at =>
      (at.registros||[]).forEach(r => checkData(r.data))
    )
  );
  if (!ultima) return null;
  ultima.setHours(0,0,0,0);
  return Math.round((hoje - ultima) / 86400000);
}
```

### Exibição

- **Card Feed (Minha Carteira):** badge "Xd sem contato" abaixo do nome quando dias > 14. Cor: amarelo (15–29d), vermelho (≥30d).
- **Detalhe do cliente (header):** linha "Último contato: há X dias" ou "Hoje" se dias === 0.
- **Visão Geral (Projetos GRV):** alerta se > 20% do portfólio tem last touch > 30d.

### Alerta automático

Em `computeAlertas()`, adicionar alert tipo `'sem_contato'` para clientes com `getDiasUltimoContato > 30`.

---

## 2. Health Score (0–100)

### Fórmula

```
Health Score = SLA(30) + CSAT(30) + Progresso(25) + Contato(15)
```

| Componente | Peso | Cálculo |
|---|---|---|
| SLA compliance | 30 pts | `calcSlaCompliance([cliente]) / 100 * 30` |
| CSAT | 30 pts | `(csat / 5) * 30` (usa média do histórico se disponível, senão campo `csat`) |
| Progresso atividades | 25 pts | `calcProgresso(cliente.ativPlaybooks) / 100 * 25` |
| Último contato | 15 pts | `dias===null?0 : dias===0?15 : dias<=7?12 : dias<=14?8 : dias<=30?4 : 0` |

Score final: inteiro 0–100. Se não há dados suficientes (sem atividades com prazo e sem CSAT), retorna `null`.

```javascript
function calcHealthScore(cliente) {
  const sla  = calcSlaCompliance([cliente]);
  const csat = calcCsatAtual(cliente); // usa média histórico ou campo csat
  const prog = calcProgresso(cliente.ativPlaybooks || []);
  const dias = getDiasUltimoContato(cliente);
  if (sla === null && csat === null) return null;
  const sSla  = sla  !== null ? (sla  / 100 * 30) : 15; // fallback 50%
  const sCsat = csat !== null ? (csat / 5   * 30) : 15;
  const sProg = prog / 100 * 25;
  const sCont = dias === null ? 7.5
              : dias === 0   ? 15
              : dias <= 7    ? 12
              : dias <= 14   ? 8
              : dias <= 30   ? 4 : 0;
  return Math.round(sSla + sCsat + sProg + sCont);
}
```

### Cores

| Score | Cor | Label |
|---|---|---|
| ≥ 75 | `#22c55e` (verde) | Saudável |
| 50–74 | `#eab308` (amarelo) | Atenção |
| < 50 | `#ef4444` (vermelho) | Risco |
| null | `var(--text4)` | — |

### Exibição

- **Card Feed:** score em círculo colorido (32px) no canto direito do card, substituindo/complementando o badge de status.
- **Detalhe do cliente (header):** "Health Score: 78 · Saudável" ao lado dos chips de status.
- **Visão Geral:** novo KPI "Health Médio" — média de todos os scores não-nulos.
- **Tabela consultores:** coluna "Health Médio" da carteira.

---

## 3. CSAT Histórico

### Modelo de dados

Converter `cliente.csat` (número) em `cliente.csatRespostas[]`:

```javascript
// csatRespostas item:
{ id: string, score: number (1-5), data: ISO date string, obs: string (opcional) }
```

**Migração em `migrateLS()`:** se `c.csat` existe e `!c.csatRespostas`, criar:
```javascript
c.csatRespostas = [{ id:'csat_migrado', score: c.csat, data: c.dataInicioCS||c.dataInicio||'2025-01-01', obs:'' }];
```
O campo `c.csat` é mantido como cache calculado: `calcCsatAtual(c)`.

### Função de cálculo

```javascript
function calcCsatAtual(cliente) {
  const resps = (cliente.csatRespostas||[]).slice(-3); // últimas 3
  if (!resps.length) return cliente.csat || null;
  return Math.round(resps.reduce((s,r)=>s+r.score,0)/resps.length*10)/10;
}
```

### UI

Em `renderAbaAtividades` ou nova seção na aba **Visão 360°**:
- Card "Satisfação (CSAT)" com score atual destacado (estrelas ou número grande)
- Lista cronológica de pesquisas anteriores (data + score + obs)
- Botão **+ Registrar CSAT** → inline form: date picker + slider 1–5 + campo obs opcional → salva e re-renderiza

---

## 4. NPS

### Modelo de dados

Novo campo `cliente.npsRespostas[]`:

```javascript
// npsRespostas item:
{ id: string, score: number (0-10), data: ISO date string, comentario: string }
```

### Cálculo do NPS

```javascript
function calcNps(cliente) {
  const resps = cliente.npsRespostas || [];
  if (!resps.length) return null;
  const promotores  = resps.filter(r => r.score >= 9).length;
  const detratores  = resps.filter(r => r.score <= 6).length;
  return Math.round((promotores - detratores) / resps.length * 100);
}
```

NPS resultante: -100 a +100.
- ≥ 50: excelente (verde)
- 0–49: bom (amarelo)
- < 0: crítico (vermelho)

### UI

Em aba **Visão 360°** do detalhe do cliente:
- Card "NPS" com valor atual (número grande) e classificação
- Lista de respostas anteriores (data + score + comentário)
- Score colorido por faixa: Promotor (9–10 verde), Neutro (7–8 cinza), Detrator (0–6 vermelho)
- Botão **+ Registrar NPS** → inline form: slider 0–10 + campo comentário + data → salva e re-renderiza

---

## Impacto em telas existentes

| Tela | Mudança |
|---|---|
| Minha Carteira (Feed) | + Health Score badge no card + badge last touch |
| Detalhe do cliente (header) | + Health Score + "há X dias sem contato" |
| Visão 360° do cliente | + cards CSAT histórico e NPS |
| Projetos GRV (Visão Geral) | + KPI "Health Médio" |
| Alertas | + alerta "sem contato > 30d" |

---

## Fora do escopo

- ARR/MRR e métricas financeiras
- Stakeholders/contatos do cliente
- Churn preditivo
- Integração com Chatwoot para auto-registrar last touch
