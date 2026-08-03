-- ============================================================
-- Soma Imob — Schema PostgreSQL
--
-- Princípio de isolamento multi-tenant (Problema 1 da análise crítica):
-- toda tabela de dados de negócio tem imobiliaria_id NOT NULL, com
-- índice próprio. Isso permite Row-Level Security (RLS) direta em
-- cada tabela, sem depender de joins para saber de quem é o dado —
-- um erro de query não deve conseguir vazar dado entre imobiliárias.
--
-- Rodar direto no PostgreSQL (via Supabase ou instância própria).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- necessário para gen_random_uuid()

-- ===== Imobiliárias (tenants) =====
CREATE TABLE imobiliarias (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nome TEXT NOT NULL,
  plano TEXT NOT NULL DEFAULT 'padrao', -- padrao | premium
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE imobiliarias IS 'Cada linha é um cliente (tenant) da Soma Imob — uma imobiliária.';


-- ===== Usuários (corretores/gestores) =====
CREATE TABLE usuarios (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  email TEXT NOT NULL,
  cargo TEXT NOT NULL DEFAULT 'corretor', -- corretor | gestor
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (imobiliaria_id, email)
);
CREATE INDEX idx_usuarios_imobiliaria ON usuarios(imobiliaria_id);
COMMENT ON TABLE usuarios IS 'Corretores e gestores de cada imobiliária.';


-- ===== Imóveis =====
CREATE TABLE imoveis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  codigo TEXT NOT NULL,
  tipo TEXT NOT NULL,           -- ex: 'Ap. 2q', 'Casa 3q'
  bairro TEXT NOT NULL,
  preco NUMERIC(12,2) NOT NULL,
  status TEXT NOT NULL DEFAULT 'ativo', -- ativo | reservado | vendido | inativo
  quartos SMALLINT,
  area_m2 NUMERIC(8,2),
  exclusivo BOOLEAN NOT NULL DEFAULT false,
  dias_carteira INTEGER NOT NULL DEFAULT 0,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (imobiliaria_id, codigo)
);
CREATE INDEX idx_imoveis_imobiliaria ON imoveis(imobiliaria_id);
CREATE INDEX idx_imoveis_status ON imoveis(imobiliaria_id, status);
COMMENT ON TABLE imoveis IS 'Carteira de imóveis de cada imobiliária.';


-- ===== Clientes / leads =====
CREATE TABLE clientes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  nome TEXT NOT NULL,
  telefone TEXT,
  email TEXT,
  origem TEXT NOT NULL DEFAULT 'outro', -- whatsapp | portal | facebook | site | outro
  score_fechamento SMALLINT NOT NULL DEFAULT 0 CHECK (score_fechamento BETWEEN 0 AND 100),
  temperatura TEXT NOT NULL DEFAULT 'frio', -- quente | morno | frio
  corretor_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  -- ultimo_contato não estava na lista original de colunas do prompt,
  -- mas a query de scan de "leads sem contato" (Problema 4) depende
  -- dele — sem essa coluna a condição 1 do scanner proativo não roda.
  ultimo_contato TIMESTAMPTZ,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_clientes_imobiliaria ON clientes(imobiliaria_id);
CREATE INDEX idx_clientes_score ON clientes(imobiliaria_id, score_fechamento DESC);
COMMENT ON TABLE clientes IS 'Leads e clientes da carteira, com score de chance de fechamento.';


-- ===== Pipeline (estágio de cada lead no funil) =====
CREATE TABLE pipeline (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  etapa TEXT NOT NULL DEFAULT 'aberto',
  -- aberto | em_atendimento | visita | proposta | documentacao | concluido | arquivado
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_pipeline_imobiliaria ON pipeline(imobiliaria_id);
CREATE INDEX idx_pipeline_cliente ON pipeline(cliente_id);
COMMENT ON TABLE pipeline IS 'Estágio atual de cada lead no funil — corresponde ao board Kanban de Atendimento.';


-- ===== Imóveis de interesse (N:N cliente x imóvel) =====
CREATE TABLE imoveis_interesse (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- imobiliaria_id denormalizado aqui de propósito: embora seja
  -- derivável via cliente_id/imovel_id, a regra do projeto é
  -- imobiliaria_id em toda tabela — permite RLS direta nesta tabela
  -- sem depender de join, e remove a chance de uma query esquecer
  -- o filtro de tenant ao consultar interesses diretamente.
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  imovel_id UUID NOT NULL REFERENCES imoveis(id) ON DELETE CASCADE,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (cliente_id, imovel_id)
);
CREATE INDEX idx_imoveis_interesse_imobiliaria ON imoveis_interesse(imobiliaria_id);
CREATE INDEX idx_imoveis_interesse_cliente ON imoveis_interesse(cliente_id);
COMMENT ON TABLE imoveis_interesse IS 'Relação N:N entre clientes e imóveis que despertaram interesse.';


-- ===== Visitas =====
CREATE TABLE visitas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  imovel_id UUID NOT NULL REFERENCES imoveis(id) ON DELETE CASCADE,
  data_visita TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'agendada', -- agendada | realizada | cancelada
  observacoes TEXT
);
CREATE INDEX idx_visitas_imobiliaria ON visitas(imobiliaria_id);
CREATE INDEX idx_visitas_imovel ON visitas(imovel_id);
COMMENT ON TABLE visitas IS 'Visitas agendadas/realizadas — usada pelo scanner pra detectar imóveis sem feedback recente.';


-- ===== Propostas =====
CREATE TABLE propostas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  imovel_id UUID NOT NULL REFERENCES imoveis(id) ON DELETE CASCADE,
  valor NUMERIC(12,2) NOT NULL,
  condicoes TEXT, -- ex: 'financiamento 70%, entrada 30%'
  vencimento TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'aberta', -- aberta | aceita | recusada | vencida
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_propostas_imobiliaria ON propostas(imobiliaria_id);
CREATE INDEX idx_propostas_vencimento ON propostas(imobiliaria_id, vencimento) WHERE status = 'aberta';
COMMENT ON TABLE propostas IS 'Propostas em negociação — usada pelo scanner pra detectar vencimentos próximos sem contato.';


-- ===== Anotações =====
CREATE TABLE anotacoes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id UUID NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
  texto TEXT NOT NULL,
  autor_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_anotacoes_imobiliaria ON anotacoes(imobiliaria_id);
CREATE INDEX idx_anotacoes_cliente ON anotacoes(cliente_id);
COMMENT ON TABLE anotacoes IS 'Anotações livres do corretor sobre um cliente/lead.';


-- ===== Logs de chamadas de IA (observabilidade de custo — Problema 5) =====
CREATE TABLE api_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  usuario_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  intencao TEXT,        -- categoria vinda do intent_classifier
  modelo TEXT NOT NULL,
  tokens_input INTEGER NOT NULL DEFAULT 0,
  tokens_output INTEGER NOT NULL DEFAULT 0,
  cache_hit_tokens INTEGER NOT NULL DEFAULT 0,
  custo_estimado_brl NUMERIC(10,4) NOT NULL DEFAULT 0,
  latencia_ms INTEGER,
  aprovado BOOLEAN,      -- null = sem feedback, true = 👍, false = 👎
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_api_logs_imobiliaria ON api_logs(imobiliaria_id);
CREATE INDEX idx_api_logs_criado_em ON api_logs(imobiliaria_id, criado_em);
COMMENT ON TABLE api_logs IS 'Registro de cada chamada ao LLM — base pra validar a estimativa de custo/margem contra a realidade.';


-- ===== Alertas proativos =====
CREATE TABLE alertas_proativos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id UUID NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL, -- LEAD_SEM_CONTATO | PROPOSTA_VENCENDO | PROPRIETARIO_SEM_FEEDBACK
  cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE,
  -- imovel_id e proposta_id não estavam na lista original de colunas,
  -- mas a condição 3 do scanner (proprietário sem feedback) não tem
  -- cliente_id — é sobre um imóvel, não um lead. E a condição 2
  -- (proposta vencendo) precisa de uma referência direta pra fazer
  -- deduplicação sem recorrer a match de texto na mensagem sugerida.
  imovel_id UUID REFERENCES imoveis(id) ON DELETE CASCADE,
  proposta_id UUID REFERENCES propostas(id) ON DELETE CASCADE,
  mensagem_sugerida TEXT,
  status TEXT NOT NULL DEFAULT 'pendente', -- pendente | aprovado | rejeitado | enviado
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
  aprovado_em TIMESTAMPTZ
);
CREATE INDEX idx_alertas_imobiliaria ON alertas_proativos(imobiliaria_id);
CREATE INDEX idx_alertas_dedup_cliente ON alertas_proativos(cliente_id, tipo, criado_em);
CREATE INDEX idx_alertas_dedup_imovel ON alertas_proativos(imovel_id, tipo, criado_em);
CREATE INDEX idx_alertas_dedup_proposta ON alertas_proativos(proposta_id, tipo, criado_em);
COMMENT ON TABLE alertas_proativos IS 'Sugestões geradas pelo scanner proativo — nunca enviadas automaticamente, sempre aguardando aprovação do corretor na interface.';


-- ============================================================
-- Extensão — Arnês IA: novos intents e roteamento inteligente
--
-- EDICAO_CADASTRO (harness/router.py) precisa de campos que o schema
-- original não tinha: endereco/observacoes em clientes não existiam
-- (só havia a tabela anotacoes, que é histórico de notas, não um
-- campo único editável); imoveis não tinha valor_aluguel, suites,
-- banheiros, vagas nem descricao — o formulário "Novo imóvel" do
-- frontend já pedia esses campos, mas o schema nunca os persistia.
-- ALTER com IF NOT EXISTS pra rodar sem erro em bancos que já
-- aplicaram esta migração.
-- ============================================================
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS endereco TEXT;
ALTER TABLE clientes ADD COLUMN IF NOT EXISTS observacoes TEXT;

ALTER TABLE imoveis ADD COLUMN IF NOT EXISTS valor_aluguel NUMERIC(12,2);
ALTER TABLE imoveis ADD COLUMN IF NOT EXISTS suites SMALLINT;
ALTER TABLE imoveis ADD COLUMN IF NOT EXISTS banheiros SMALLINT;
ALTER TABLE imoveis ADD COLUMN IF NOT EXISTS vagas SMALLINT;
ALTER TABLE imoveis ADD COLUMN IF NOT EXISTS descricao TEXT;

ALTER TABLE pipeline ADD COLUMN IF NOT EXISTS observacoes TEXT;

-- economia_estimada_brl: quanto essa chamada economizou por ter sido
-- roteada pra Haiku/SQL em vez de Sonnet (Problema 5, parte 2). Fica
-- em api_logs — mesma tabela, mesma linha, pra somar junto do custo
-- real sem precisar de join.
ALTER TABLE api_logs ADD COLUMN IF NOT EXISTS economia_estimada_brl NUMERIC(10,4) NOT NULL DEFAULT 0;
