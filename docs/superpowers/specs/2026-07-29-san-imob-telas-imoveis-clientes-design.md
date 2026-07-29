# SAN Imob — Telas de Imóveis e Clientes — Design Spec

**Data:** 2026-07-29
**Status:** Aprovado
**Escopo:** Duas novas telas de mockup estático (`imoveis.html`, `clientes.html`) para o protótipo SAN Imob, navegáveis a partir de `san-imob/index.html`

---

## Contexto

`san-imob/index.html` já existe como protótipo estático (HTML/CSS/JS puro, sem framework, sem servidor) da tela "Início" do CRM imobiliário SAN Imob. Esta rodada expande o protótipo com duas telas adicionais do menu lateral: **Imóveis** e **Clientes**. Backend, banco de dados e IA real ficam fora de escopo — segue sendo mockup navegável, com dados fictícios embutidos no HTML.

---

## Estrutura de arquivos

- `san-imob/index.html` (existente) — Início. Ajuste: os itens de menu "Imóveis" e "Clientes" passam de `<li>` sem destino para links reais (`<a href="imoveis.html">`, `<a href="clientes.html">`). Os demais itens (Visitas, Propostas, Portais, Relatórios) continuam como placeholders — mantêm o destaque visual ao clicar (JS já existente), sem navegação real.
- `san-imob/imoveis.html` (novo)
- `san-imob/clientes.html` (novo)

Cada arquivo é autocontido: repete seu próprio `<style>` e `<script>` (mesma sidebar, topbar e paleta de `index.html`, com o item correspondente marcado como ativo). Não há CSS/JS compartilhado entre arquivos — mantém o padrão "abre direto no navegador, sem servidor" do protótipo original.

---

## Tela: Imóveis (`imoveis.html`)

**Topbar:** título "Imóveis" + botão azul "Novo imóvel" (mesmo botão de `index.html`, sem ação real — só visual).

**Barra de filtro** (abaixo da saudação, acima da lista):
- Campo de busca por texto (sem lógica de busca real nesta rodada — input decorativo, mesmo padrão do input de IA em `index.html` onde a interatividade é mínima).
- Chips de filtro rápido: "Todos" (ativo por padrão), "Ativos", "Reservados". Clicar troca qual chip fica marcado como ativo (destaque azul), mas não precisa filtrar a lista de fato — é mockup visual, não funcional.

**Lista (layout híbrido — linha compacta com miniatura):**
Cada linha exibe, da esquerda para a direita:
1. Miniatura pequena (quadrado ~40x40px, fundo cinza claro `#F3F4F6`, emoji 🏠 centralizado — placeholder de foto)
2. Código do imóvel (ex: `#1023`)
3. Tipo + quartos (ex: "Ap. 2q")
4. Bairro (ex: "Palmeiras")
5. Preço formatado (ex: "R$ 480.000")
6. Badge de status: "Ativo" (verde), "Reservado" (amarelo), "Exclusivo" (azul, pode aparecer junto com Ativo)
7. Dias no mercado (ex: "12 dias")

Hover na linha: fundo muda para leve tom azul claro e a borda esquerda ganha um traço azul de 3px (mesmo espírito do hover-to-blue já usado nos cards de métrica de `index.html`).

Sem clique para abrir detalhe — fora de escopo desta rodada.

**Dados fictícios:** ~8 imóveis cobrindo bairros citados no contexto do produto (Palmeiras, Centro, Jd. Amanda, entre outros), com mix de status e preços variados (R$ 355.000 a R$ 710.000).

---

## Tela: Clientes (`clientes.html`)

**Topbar:** título "Clientes" (sem botão de ação adicional).

**Barra de filtro:** chips "Todos" (ativo por padrão), "Alta chance", "Sem contato recente" — mesmo comportamento visual-only dos chips de Imóveis (troca o chip ativo, não filtra de fato).

**Lista, ordenada por padrão por chance de fechamento (Alta → Média → Baixa):**
Cada linha exibe:
1. Avatar circular com iniciais (mesmo estilo do avatar "SW" da sidebar, cor de fundo azul)
2. Nome do cliente
3. Score de chance de fechamento — badge colorido: Alta (verde), Média (amarelo), Baixa (cinza)
4. Imóvel de interesse (ex: "Ap. 2q — Palmeiras")
5. Último contato, em texto relativo (ex: "há 3 dias", "sem contato há 3 semanas")
6. Status: "Lead novo" / "Em negociação" / "Proposta enviada"

**Marcos Andrade** aparece como primeiro da lista, com score Alta — mesmo cliente citado no card de oportunidade da IA em `index.html`, reforçando continuidade entre as telas.

Sem clique para abrir detalhe — fora de escopo desta rodada.

**Dados fictícios:** ~8 clientes com mix de scores e status.

---

## O que não muda

- Sidebar, topbar, paleta de cores, tipografia (Inter) e o restante do conteúdo de `index.html` (saudação, card de IA, grid de métricas, bloco de input de IA) — inalterados, exceto os dois links de menu que passam a navegar de verdade.
- Nenhuma chamada de rede, nenhum backend, nenhuma persistência — os filtros e chips são só destaque visual (`class="active"` trocando de elemento ao clicar), sem re-renderizar dados.
- Não há tela de detalhe de imóvel ou cliente nesta rodada.

---

## Implementação: pontos de atenção

- Reaproveitar a estrutura CSS de `index.html` (grid `.app`, `.sidebar`, `.topbar`, `.content`) para consistência visual entre as três páginas, ainda que cada arquivo seja independente (copiar o bloco `<style>`, ajustando apenas o necessário).
- O JS de destaque de menu ativo (`sidebar-nav li` / `<a>`) precisa ser adaptado: como agora existem links reais entre páginas, o item ativo de cada página é fixado no HTML (classe `active` hardcoded no item correspondente), não mais calculado dinamicamente por clique — cada arquivo já "nasce" com o item certo marcado.
- Chips de filtro (Imóveis e Clientes): JS simples de toggle de classe `active` entre os chips do mesmo grupo, sem lógica de filtragem de dados.
