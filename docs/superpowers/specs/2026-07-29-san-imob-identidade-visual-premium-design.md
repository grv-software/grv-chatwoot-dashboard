# SAN Imob — Identidade Visual Premium — Design Spec

**Data:** 2026-07-29
**Status:** Aprovado
**Escopo:** Substituir a identidade visual genérica do protótipo SAN Imob (cor, ícones, logo, tratamento do card de IA) por uma linguagem à altura de produtos SaaS premium (Linear/Vercel/Notion/Lofty), e incorporar diferenciais de posicionamento competitivo (badge de pricing simples, painel de atividade da IA, toast em tempo real, score de lead numérico) — sem alterar estrutura, conteúdo ou navegação já existentes

---

## Contexto

Uma análise do protótipo atual (`san-imob/index.html`, `imoveis.html`, `clientes.html`) identificou que a **estrutura** (navbar, densidade de listas, badges semânticos, hierarquia de layout) já está no nível de produto SaaS, mas o **revestimento visual** ainda lê como "mockup genérico gerado por IA":

1. Ícones em emoji (🏢 🔔 🏠 ✦) em vez de SVG — o anti-padrão mais evidente.
2. Azul `#2563EB` é o Tailwind blue-600 padrão — não é uma cor de marca, é o default de qualquer template.
3. O card de oportunidade da IA (o elemento mais importante do produto) é visualmente idêntico a um card de métrica comum — nada sinaliza "isto é IA agindo agora".
4. Tipografia sem ajuste de tracking — falta a nitidez de produtos como Linear/Vercel.
5. Sem microinteração de transição — troca de conteúdo é instantânea.
6. Logo é emoji + texto, sem identidade própria.

**Contexto competitivo adicional:** o Kenlo (principal concorrente brasileiro) cobra a IA por créditos ("Koins"), gerando insegurança em imobiliárias pequenas, e tem interface densa/dark theme de alta curva de aprendizado. A Lofty (referência americana) já opera IA agêntica visível — um painel "Cowork" mostra em tempo real o que a IA está fazendo, com toast notifications e score de lead numérico. O posicionamento do SAN Imob é: mais simples que Kenlo (IA inclusa, sem créditos), mais brasileiro que Lofty (WhatsApp nativo), com IA no núcleo do produto. Isso adiciona quatro elementos ao escopo deste spec (seções 7 a 10), além dos seis pontos de identidade visual.

Este spec resolve os seis pontos de identidade visual e os quatro diferenciais competitivos numa só passada, consistente nas três páginas.

---

## 1. Sistema de cor

Substituir toda ocorrência de `#2563EB` / `#1D4ED8` / `#EFF6FF` (usados como cor de marca/ação) por uma paleta indigo própria:

| Token | Valor | Uso |
|---|---|---|
| Marca | `#4F46E5` | Botões primários, links de nav ativos, bordas de destaque, acentos de foco |
| Marca (hover/dark) | `#4338CA` | Hover de botões e links primários |
| Marca (tint claro) | `#EEF2FF` | Fundo de itens de nav ativos, badges "IA", badge de status Exclusivo |

**Não muda:** cores semânticas de status (`#16A34A` verde/Ativo/Alta, `#CA8A04` amarelo/Reservado/Média, `#6B7280` cinza/Baixa, `#DC2626` vermelho/badge de notificação). O problema identificado foi o azul genérico usado como cor de marca, não os semânticos de status.

Aplicar a substituição em todas as ocorrências das três páginas (navbar, botões, chips ativos, hover de cards, ai-card, ai-input-label).

---

## 2. Ícones SVG inline

Como os arquivos são HTML autocontidos sem build step, os ícones são SVG inline no próprio HTML (sem dependência de biblioteca externa como Lucide/Heroicons via CDN). Estilo: outline fino, stroke `1.5–1.75px`, `stroke-linecap="round"`, `stroke-linejoin="round"`, sem preenchimento (herdam `currentColor` para se adaptarem à cor do texto ao redor).

Substituições obrigatórias:
- 🔔 (sino de notificação, presente nas 3 páginas) → ícone de sino outline
- ✦ (sparkle da IA, `index.html`: header do ai-card e label do ai-input-block) → ícone de sparkle/estrela outline
- 🏠 (miniatura de imóvel, `imoveis.html`, ~8 ocorrências nas linhas da lista) → ícone de casa outline, dentro do quadrado `.thumb` já existente

Adições de polimento (mesma linguagem de ícone):
- Ícone de lupa dentro/ao lado do campo de busca em `imoveis.html`
- Ícone de "+" antes do texto no botão "Novo imóvel"

Cada ícone é definido uma vez por arquivo (inline `<svg>`) e reutilizado via `use`/cópia direta — não é necessário um sprite sheet centralizado para esta escala (poucos ícones, 3 arquivos independentes).

---

## 3. Logomark

Substitui o emoji 🏢 ao lado de "SAN Imob" na navbar (presente nas 3 páginas): um `div` de ~28px, `border-radius: 8px`, fundo sólido na cor de marca (`#4F46E5`), com a letra "S" branca, bold, centralizada. Mesma linguagem de radius dos cards do produto. Não depende de asset SVG — é puramente CSS + texto, então funciona de forma idêntica nos três arquivos sem necessidade de arquivo de imagem externo.

---

## 4. Tratamento do card de oportunidade da IA (`index.html`)

O `.ai-card` (único elemento deste tipo, só existe na tela Início) recebe tratamento distinto de qualquer outro card do produto, para comunicar "isto é um insight de IA, não um dado estático":

- **Fundo:** gradiente sutil `linear-gradient(135deg, #FFFFFF 0%, #F5F4FF 100%)` — tint de ~2-4% de indigo, perceptível apenas por comparação direta com os cards brancos ao lado, nunca chamativo.
- **Badge "IA":** pequeno pill (`#EEF2FF` fundo, texto indigo, ícone sparkle SVG + texto "IA") posicionado ao lado do título do card.
- **Borda esquerda de destaque:** migra de azul para indigo (`#4F46E5`), mantém 4px.
- **Microanimação de entrada:** fade + leve slide-up (`translateY(8px)` → `0`, opacidade `0` → `1`), duração ~250ms, `ease-out`, dispara uma vez ao carregar a página. Envolvida em `@media (prefers-reduced-motion: no-preference)` — usuários com redução de movimento ativada veem o card já no estado final, sem animação.
- **Crossfade na troca de conteúdo:** ao clicar "Enviar mensagem", em vez de `innerHTML` instantâneo, o conteúdo atual faz fade-out (~100ms), o HTML é trocado, e o novo conteúdo faz fade-in (~150ms). Mesma lógica de `prefers-reduced-motion` — se reduzido, troca é instantânea.

---

## 5. Tipografia

Adicionar `letter-spacing: -0.02em` aos elementos de maior destaque visual em todas as páginas: `h2` (títulos de página/saudação), `h3` do ai-card, `.value` dos cards de métrica, e o texto do logo na navbar. Corpo de texto (14px, listas, parágrafos) não muda — o ajuste é só nos elementos que funcionam como "display type".

---

## 6. Escopo de aplicação (identidade visual)

| Mudança | index.html | imoveis.html | clientes.html |
|---|---|---|---|
| Cor de marca (indigo) | ✅ | ✅ | ✅ |
| Ícones SVG (sino, logo) | ✅ | ✅ | ✅ |
| Ícone de casa (thumb) | — | ✅ | — |
| Ícone de lupa (busca) | — | ✅ | — |
| Ícone "+" (Novo imóvel) | ✅ | ✅ | — (página não tem esse botão) |
| Logomark | ✅ | ✅ | ✅ |
| Letter-spacing em títulos | ✅ | ✅ | ✅ |
| Tratamento especial do ai-card (gradiente, badge, animação, crossfade) | ✅ (único lugar onde o elemento existe) | — | — |

---

## 7. Badge "✦ IA inclusa" na navbar

Presente nas três páginas, logo após o wordmark "SAN Imob" na navbar (antes dos links de navegação). Pill pequena: fundo `#EEF2FF`, texto indigo `#4F46E5`, ~11-12px, ícone sparkle SVG (mesmo do card de IA) + texto "IA inclusa". Comunica visualmente, desde o primeiro olhar, o diferencial de pricing (sem créditos/Koins) sem precisar de texto explicativo.

---

## 8. Painel "Atividade da IA" (`index.html`, novo bloco)

Novo bloco na tela Início, posicionado logo abaixo do `.ai-card` de oportunidade (que continua no topo como destaque principal — a ação mais urgente). O painel comunica que a IA trabalha continuamente sobre toda a carteira, não só quando solicitada — mesmo papel do painel "Cowork" da Lofty.

**Estrutura:** card branco padrão (mesmo estilo dos outros cards do produto, sem o tratamento especial do ai-card), título "Atividade da IA", lista de 4 itens recentes. Cada item tem:
- Ícone de status: ✓ concluído (verde `#16A34A`), ↻ processando (indigo `#4F46E5`, com leve animação de rotação contínua enquanto for o único item "em andamento" exibido), ⏳ agendado (cinza `#6B7280`)
- Descrição da ação, citando o canal (WhatsApp) quando aplicável
- Tempo relativo, alinhado à direita

**Conteúdo (mock, ordem cronológica decrescente):**
1. ✓ Mensagem enviada via WhatsApp — Marcos Andrade (há 2 min)
2. ↻ Analisando carteira de 481 imóveis... (agora)
3. ✓ Proposta gerada — Ap. 2q Palmeiras (há 18 min)
4. ⏳ Follow-up agendado — Fernanda Lima (amanhã 10h)

Sem interatividade além do hover leve nas linhas (mesmo padrão de `.list-row` já usado em Imóveis/Clientes) — não há ação real por trás dos itens nesta rodada.

---

## 9. Toast de oportunidade em tempo real (`index.html`)

Aparece apenas na tela Início, simulando monitoramento ativo da IA. Dispara automaticamente ~5 segundos após o carregamento da página (via `setTimeout`), sem exigir nenhuma ação do usuário.

**Conteúdo:** "✦ Nova oportunidade: Fernanda Lima abriu a proposta 3x hoje" + botão de texto "Ver" + botão de fechar (×).

**Comportamento:**
- Desliza a partir da borda direita, fixado no canto inferior direito da viewport (`position: fixed`).
- Auto-dismiss após ~5 segundos, com fade-out.
- Dispensável manualmente a qualquer momento pelo botão ×, cancelando o timer de auto-dismiss.
- Dispara uma única vez por carregamento de página — não repete nem enfileira novos toasts.
- Entrada/saída animada por `transform`/`opacity` (150-250ms, ease-out na entrada, ease-in na saída). Sob `prefers-reduced-motion: reduce`, aparece/desaparece sem slide, só com fade instantâneo mais curto.
- Não bloqueia interação com o restante da página (não é modal).

---

## 10. Score numérico na lista de Clientes (`clientes.html`)

Os badges de chance de fechamento já existentes (Alta/Média/Baixa) ganham um número ao lado, mantendo a cor/badge como indicador primário (não depende só do número para ser compreendido): formato `"Alta · 94"`.

**Valores atribuídos (mantendo a ordem já existente na lista):**

| Cliente | Score | Valor |
|---|---|---|
| Marcos Andrade | Alta | 94 |
| Fernanda Lima | Alta | 91 |
| Ricardo Souza | Alta | 87 |
| Juliana Prado | Média | 68 |
| Carlos Eduardo | Média | 61 |
| Patrícia Nunes | Média | 58 |
| Bruno Tavares | Baixa | 34 |
| Camila Rocha | Baixa | 22 |

---

## 11. Escopo de aplicação (features competitivas)

| Mudança | index.html | imoveis.html | clientes.html |
|---|---|---|---|
| Badge "IA inclusa" na navbar | ✅ | ✅ | ✅ |
| Painel "Atividade da IA" | ✅ (único lugar) | — | — |
| Toast de oportunidade em tempo real | ✅ (único lugar) | — | — |
| Score numérico nos badges de chance | — | — | ✅ (único lugar onde o badge existe) |

---

## O que não muda

- Estrutura de navbar, layout de coluna central (max-width 960px), estrutura de listas e filtros já aprovados nos specs anteriores.
- Cores semânticas de status (verde/amarelo/cinza/vermelho).
- Conteúdo, dados fictícios e comportamento de filtros/chips (continuam sendo mockup visual, sem filtragem real de dados).
- Nenhuma dependência externa nova é introduzida — sem CDN de ícones, sem web fonts além do Inter já usado.
- `imoveis.html` e `clientes.html` não ganham painel de atividade nem toast nesta rodada — só `index.html` (ver seções 8 e 9).

---

## Implementação: pontos de atenção

- Os ícones SVG devem usar `fill="none"` e `stroke="currentColor"` para herdar a cor do elemento pai automaticamente (ex: o sino já herda a cor de `.icon-btn`, sem precisar de classe extra).
- A animação de entrada do `.ai-card` deve rodar apenas uma vez por carregamento de página — não repetir ao interagir com outros elementos da tela.
- O crossfade do `enviarMensagem()` precisa aguardar o `transitionend` (ou usar `setTimeout` equivalente à duração do fade-out) antes de trocar o `innerHTML`, para não cortar a transição.
- Testar visualmente que o gradiente do `.ai-card` continua legível com o texto em `#374151`/`#111827` — o tint é claro o suficiente para não afetar contraste.
- Repetir cada substituição (cor, ícone, logo) nos três arquivos individualmente, já que não há CSS/JS compartilhado entre eles (decisão já tomada em spec anterior).
- O ícone ↻ do painel de atividade usa `@keyframes spin` contínuo só enquanto for o único item "processando" da lista mockada — não é um indicador de estado real, então não precisa de lógica de start/stop, só rodar infinitamente via CSS.
- O toast usa `aria-live="polite"` (não rouba foco) e o timer de auto-dismiss deve ser cancelado (`clearTimeout`) se o usuário clicar em ×, para não tentar remover um elemento já removido.
- `setTimeout` do toast dispara uma vez só — não usar `setInterval` nem recriar o timer em nenhuma interação da página.
