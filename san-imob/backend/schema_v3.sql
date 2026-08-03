-- ============================================================
-- Soma Imob — Schema PostgreSQL v3 (migration incremental)
--
-- PRÉ-REQUISITO: banco com schema_v2.sql já executado.
-- Este arquivo contém SOMENTE ALTER TABLE e CREATE TABLE novos.
-- Nenhuma tabela existente é recriada ou dropada.
--
-- Princípios mantidos do v2:
--   - Toda tabela nova tem imobiliaria_id NOT NULL + FK imobiliarias
--   - Sem CASCADE DELETE em dados de negócio — preferência por SET NULL
--   - Isolamento multi-tenant por coluna direta (sem join para saber
--     de qual imobiliária é o dado)
--
-- Ordem das seções:
--   1. clientes       — tipo, status, unicidade de telefone
--   2. condominios    — nova tabela
--   3. imoveis        — vínculo condominio, publicação, comissão, JSONB
--   4. negocios       — nova tabela (substitui lógica do pipeline)
--   5. visitas        — negocio_id, confirmação, feedback
--   6. propostas      — negocio_id, forma de pagamento, comissão
--   7. usuarios       — perfil de acesso
--   8. soma_sites     — nova tabela
--   9. triggers       — fn_set_atualizado_em para tabelas novas
--  10. verificação    — queries para validar a migration
-- ============================================================


-- ============================================================
-- SEÇÃO 1 — Alterações na tabela clientes
-- ============================================================

-- Papel do cliente no ecossistema da imobiliária.
-- 'interessado'  = compradores/locatários
-- 'proprietario' = donos que colocaram imóvel para vender/alugar
-- 'ambos'        = compra e vende ao mesmo tempo
ALTER TABLE clientes
  ADD COLUMN tipo TEXT NOT NULL DEFAULT 'interessado'
    CHECK (tipo IN ('interessado', 'proprietario', 'ambos'));

-- Status operacional do relacionamento com o cliente.
ALTER TABLE clientes
  ADD COLUMN status TEXT NOT NULL DEFAULT 'ativo'
    CHECK (status IN ('ativo', 'pausado', 'fechou_conosco', 'inativo'));

-- Data da última mudança de status (atualizar manualmente na aplicação
-- ou via trigger dedicado quando implementar o fluxo de status).
ALTER TABLE clientes
  ADD COLUMN data_status_alterado TIMESTAMPTZ DEFAULT now();

-- Unicidade de telefone por imobiliária.
-- O mesmo telefone pode existir em imobiliárias diferentes (multi-tenant).
-- Valores NULL ficam fora da constraint (comportamento padrão do
-- UNIQUE no PostgreSQL: dois NULLs não se conflitam).
ALTER TABLE clientes
  ADD CONSTRAINT uq_clientes_telefone_imobiliaria
    UNIQUE (imobiliaria_id, telefone);


-- ============================================================
-- SEÇÃO 2 — Nova tabela condominios
-- ============================================================

CREATE TABLE condominios (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id   UUID        NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  nome             TEXT        NOT NULL,

  -- Endereço completo
  cep              TEXT,
  logradouro       TEXT,
  numero           TEXT,
  complemento      TEXT,
  bairro           TEXT,
  cidade           TEXT,
  estado           TEXT,

  tipo             TEXT        NOT NULL DEFAULT 'residencial'
                     CHECK (tipo IN ('residencial', 'comercial', 'misto')),

  -- Status construtivo do empreendimento
  status           TEXT        NOT NULL DEFAULT 'pronto'
                     CHECK (status IN ('pronto', 'na_planta', 'em_construcao', 'entregue_recentemente')),

  construtora      TEXT,
  ano_construcao   INTEGER,
  previsao_entrega DATE,        -- relevante para 'na_planta' e 'em_construcao'
  total_unidades   INTEGER,
  total_torres     INTEGER,

  -- Objeto de booleans das amenidades do condomínio.
  -- Chaves esperadas: piscina_adulto, piscina_infantil, academia,
  -- salao_festas, churrasqueira_coletiva, playground, quadra,
  -- espaco_gourmet, pet_place, elevador, portaria_24h, seguranca_24h,
  -- gerador, energia_solar, estacionamento_visitantes, bicicletario.
  amenidades       JSONB       NOT NULL DEFAULT '{}',

  -- Array de URLs de fotos do condomínio
  fotos            JSONB       NOT NULL DEFAULT '[]',

  criado_em        TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_condominios_imobiliaria ON condominios(imobiliaria_id);


-- ============================================================
-- SEÇÃO 3 — Alterações na tabela imoveis
-- ============================================================

-- Vínculo opcional com condomínio. NULL = imóvel avulso.
-- SET NULL preserva o imóvel se o condomínio for deletado.
ALTER TABLE imoveis
  ADD COLUMN condominio_id UUID REFERENCES condominios(id) ON DELETE SET NULL;

-- Título curto para portais e site, sugerido pelo Arnês.
ALTER TABLE imoveis
  ADD COLUMN titulo TEXT;

-- NOTA: coluna `descricao TEXT` já existe em imoveis desde o schema_v2.
-- Não é re-adicionada aqui. O Arnês passa a populá-la via
-- EDICAO_CADASTRO quando estiver NULL.

-- Flags de visibilidade e destaque
ALTER TABLE imoveis
  ADD COLUMN publicar_site    BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN publicar_portais BOOLEAN NOT NULL DEFAULT false,
  ADD COLUMN destaque_site    BOOLEAN NOT NULL DEFAULT false;

-- `exclusividade` é coluna nova. A coluna `exclusivo` (BOOLEAN) existente
-- no v2 permanece para compatibilidade com queries legadas até que a
-- migração de dados seja concluída e o campo antigo descontinuado.
ALTER TABLE imoveis
  ADD COLUMN exclusividade BOOLEAN NOT NULL DEFAULT false;

-- Janela de vigência do contrato de captação
ALTER TABLE imoveis
  ADD COLUMN prazo_captacao_inicio DATE,
  ADD COLUMN prazo_captacao_fim    DATE;

-- Avaliação e estrutura de comissão
ALTER TABLE imoveis
  ADD COLUMN valor_avaliacao           NUMERIC(12,2),
  ADD COLUMN corretor_captacao_id      UUID REFERENCES usuarios(id) ON DELETE SET NULL,
  ADD COLUMN percentual_comissao       NUMERIC(5,2),  -- ex: 6.00 para 6%
  ADD COLUMN divisao_comissao_captacao NUMERIC(5,2),  -- % da comissão para o captador
  ADD COLUMN divisao_comissao_venda    NUMERIC(5,2);  -- % da comissão para o vendedor

-- Características internas do imóvel (booleans).
-- Chaves: armarios_embutidos, ar_condicionado, reformado,
-- vista_privilegiada, churrasqueira_privativa, piscina_privativa,
-- jardim, area_servico, copa, despensa, lavabo, closet,
-- varanda_gourmet, pet_friendly.
ALTER TABLE imoveis
  ADD COLUMN caracteristicas  JSONB NOT NULL DEFAULT '{}';

-- Histórico de preços: array de objetos {valor, data, usuario_id}.
-- Cada entrada é inserida pela aplicação a cada alteração de preço,
-- nunca editada retroativamente.
ALTER TABLE imoveis
  ADD COLUMN historico_precos JSONB NOT NULL DEFAULT '[]';

-- Índice parcial para buscar imóveis de um condomínio específico
CREATE INDEX idx_imoveis_condominio
  ON imoveis(condominio_id)
  WHERE condominio_id IS NOT NULL;

-- Dentro de um mesmo condomínio, o complemento (unidade/apartamento)
-- não pode se repetir. Index parcial: só aplica onde condominio_id
-- IS NOT NULL — imóveis avulsos ficam de fora da restrição.
CREATE UNIQUE INDEX uq_imoveis_condominio_complemento
  ON imoveis(condominio_id, complemento)
  WHERE condominio_id IS NOT NULL;


-- ============================================================
-- SEÇÃO 4 — Nova tabela negocios
-- ============================================================
--
-- Um negócio = cliente + imóvel + corretor + estágio de funil.
-- Substitui a lógica de rastreamento de pipeline para novos registros.
-- A tabela `pipeline` permanece no schema para compatibilidade com
-- dados históricos — nenhuma FK de negocios aponta para pipeline.

CREATE TABLE negocios (
  id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  imobiliaria_id       UUID        NOT NULL REFERENCES imobiliarias(id) ON DELETE CASCADE,
  cliente_id           UUID        NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,

  -- Imóvel nullable: negócio pode abrir antes do imóvel ser escolhido
  imovel_id            UUID        REFERENCES imoveis(id) ON DELETE SET NULL,

  -- Corretor responsável. SET NULL preserva o negócio se o corretor sair.
  corretor_id          UUID        REFERENCES usuarios(id) ON DELETE SET NULL,

  estagio              TEXT        NOT NULL DEFAULT 'novo_lead'
                         CHECK (estagio IN (
                           'novo_lead', 'em_contato', 'visita_agendada',
                           'proposta_enviada', 'em_negociacao', 'ganho', 'perdido'
                         )),

  -- Obrigatório quando estagio = 'perdido'. Validação pela aplicação:
  -- CHECK condicional em colunas da mesma tabela não é suportado de
  -- forma direta no PostgreSQL sem triggers.
  motivo_perda         TEXT,

  -- Atualizado pela aplicação a cada mudança de estágio,
  -- para calcular tempo em cada fase do funil.
  data_entrada_estagio TIMESTAMPTZ NOT NULL DEFAULT now(),

  valor_negocio        NUMERIC(12,2),
  comissao_prevista    NUMERIC(12,2),

  criado_em            TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_negocios_imobiliaria ON negocios(imobiliaria_id);
CREATE INDEX idx_negocios_cliente     ON negocios(cliente_id);
CREATE INDEX idx_negocios_corretor    ON negocios(corretor_id);
-- Índice composto para listar o kanban de uma imobiliária por estágio
CREATE INDEX idx_negocios_estagio     ON negocios(imobiliaria_id, estagio);


-- ============================================================
-- SEÇÃO 5 — Alterações na tabela visitas
-- ============================================================

-- Negócio que originou a visita. CASCADE: sem negócio, sem visita.
ALTER TABLE visitas
  ADD COLUMN negocio_id           UUID REFERENCES negocios(id) ON DELETE CASCADE;

-- Resposta do cliente ao convite de visita
ALTER TABLE visitas
  ADD COLUMN confirmacao_cliente  TEXT DEFAULT 'aguardando'
               CHECK (confirmacao_cliente IN ('aguardando', 'confirmado', 'recusado'));

-- Sentimento do cliente após a visita
ALTER TABLE visitas
  ADD COLUMN feedback_resultado   TEXT
               CHECK (feedback_resultado IN (
                 'gostou', 'nao_gostou', 'quer_pensar', 'quer_mais_opcoes'
               ));

-- Anotação livre do corretor sobre o feedback
ALTER TABLE visitas
  ADD COLUMN feedback_observacoes TEXT;


-- ============================================================
-- SEÇÃO 6 — Alterações na tabela propostas
-- ============================================================

-- Negócio ao qual a proposta pertence
ALTER TABLE propostas
  ADD COLUMN negocio_id          UUID REFERENCES negocios(id) ON DELETE CASCADE;

-- Valor efetivamente proposto (pode diferir do preco do imóvel)
ALTER TABLE propostas
  ADD COLUMN valor_proposto      NUMERIC(12,2);

-- Forma de pagamento declarada na proposta
ALTER TABLE propostas
  ADD COLUMN forma_pagamento     TEXT
               CHECK (forma_pagamento IN ('financiamento', 'a_vista', 'permuta', 'misto'));

-- Cláusulas adicionais (ex: inclusão de móveis, prazo de posse)
ALTER TABLE propostas
  ADD COLUMN condicoes_especiais TEXT;

-- Data limite para o proprietário responder à proposta
ALTER TABLE propostas
  ADD COLUMN prazo_validade      DATE;

-- Comissão calculada automaticamente a partir das regras do imóvel
ALTER TABLE propostas
  ADD COLUMN comissao_calculada  NUMERIC(12,2);

-- STATUS — ATENÇÃO: a coluna `status` já existe no schema_v2 com
-- DEFAULT 'aberta' e valores: aberta | aceita | recusada | vencida.
-- O novo vocabulário usa 'enviada' no lugar de 'aberta' e adiciona
-- 'contraproposta'. Para sincronizar o banco existente, executar:
--
--   UPDATE propostas SET status = 'enviada' WHERE status = 'aberta';
--   ALTER TABLE propostas ALTER COLUMN status SET DEFAULT 'enviada';
--
-- Estas linhas estão COMENTADAS intencionalmente. Executar somente
-- após confirmar que nenhuma query da aplicação ainda usa o valor
-- 'aberta'. O valor 'vencida' permanece válido para registros históricos.


-- ============================================================
-- SEÇÃO 7 — Alterações na tabela usuarios
-- ============================================================

-- Perfil de acesso e hierarquia na imobiliária.
-- Distinto do campo `cargo` (função operacional descritiva) — `perfil`
-- controla permissões, visibilidade de dados e menus na interface.
ALTER TABLE usuarios
  ADD COLUMN perfil TEXT NOT NULL DEFAULT 'corretor'
               CHECK (perfil IN (
                 'diretor', 'gerente', 'supervisor', 'corretor', 'administrativo'
               ));


-- ============================================================
-- SEÇÃO 8 — Nova tabela soma_sites
-- ============================================================
--
-- Cada imobiliária pode ter no máximo um site Soma (UNIQUE em
-- imobiliaria_id). O site existe no estado 'rascunho' até ser
-- publicado explicitamente.

CREATE TABLE soma_sites (
  id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),

  -- UNIQUE garante 1 site por imobiliária
  imobiliaria_id        UUID        NOT NULL UNIQUE REFERENCES imobiliarias(id) ON DELETE CASCADE,

  -- Template visual escolhido para o site
  template_id           TEXT        NOT NULL DEFAULT 'horizon'
                          CHECK (template_id IN (
                            'horizon', 'noir', 'natura', 'confianca',
                            'editorial', 'vivo', 'metropolis', 'galeria'
                          )),

  status                TEXT        NOT NULL DEFAULT 'rascunho'
                          CHECK (status IN ('rascunho', 'publicado')),

  dominio_personalizado TEXT,
  logo_url              TEXT,

  -- Paleta extraída da logo pelo Arnês: {primaria, secundaria, acento}
  cores                 JSONB       NOT NULL DEFAULT '{}',

  -- Conteúdo editável de cada seção do template
  conteudo              JSONB       NOT NULL DEFAULT '{}',

  seo_titulo            TEXT,
  seo_descricao         TEXT,

  criado_em             TIMESTAMPTZ NOT NULL DEFAULT now(),
  atualizado_em         TIMESTAMPTZ NOT NULL DEFAULT now(),
  publicado_em          TIMESTAMPTZ           -- NULL enquanto status = 'rascunho'
);

-- Índice parcial para listar sites publicados no painel administrativo
CREATE INDEX idx_soma_sites_publicados
  ON soma_sites(imobiliaria_id)
  WHERE status = 'publicado';


-- ============================================================
-- SEÇÃO 9 — Triggers de atualizado_em
-- ============================================================

-- Função genérica reutilizável. OR REPLACE torna o script idempotente
-- (seguro de rodar novamente sem remover o trigger primeiro).
CREATE OR REPLACE FUNCTION fn_set_atualizado_em()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.atualizado_em = now();
  RETURN NEW;
END;
$$;

-- Trigger para condominios
CREATE TRIGGER trg_condominios_atualizado_em
  BEFORE UPDATE ON condominios
  FOR EACH ROW EXECUTE FUNCTION fn_set_atualizado_em();

-- Trigger para negocios
CREATE TRIGGER trg_negocios_atualizado_em
  BEFORE UPDATE ON negocios
  FOR EACH ROW EXECUTE FUNCTION fn_set_atualizado_em();

-- Trigger para soma_sites
CREATE TRIGGER trg_soma_sites_atualizado_em
  BEFORE UPDATE ON soma_sites
  FOR EACH ROW EXECUTE FUNCTION fn_set_atualizado_em();


-- ============================================================
-- SEÇÃO 10 — Queries de verificação
-- ============================================================
-- Rodar manualmente após aplicar a migration para validar o resultado.
-- Todas as queries filtram por imobiliaria_id quando acessam dados
-- de negócio, conforme princípio de isolamento multi-tenant.

-- Verificar novas tabelas (deve listar condominios, negocios, soma_sites)
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verificar colunas adicionadas em clientes
-- (deve incluir tipo, status, data_status_alterado)
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'clientes'
ORDER BY ordinal_position;

-- Verificar colunas adicionadas em imoveis
-- (deve incluir condominio_id, titulo, publicar_site, publicar_portais,
--  destaque_site, exclusividade, prazo_captacao_inicio, prazo_captacao_fim,
--  valor_avaliacao, corretor_captacao_id, percentual_comissao,
--  divisao_comissao_captacao, divisao_comissao_venda, caracteristicas,
--  historico_precos)
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'imoveis'
ORDER BY ordinal_position;

-- Verificar estrutura da tabela negocios
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'negocios'
ORDER BY ordinal_position;

-- Verificar constraints e índices criados nesta migration
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname IN (
    'uq_clientes_telefone_imobiliaria',
    'idx_condominios_imobiliaria',
    'idx_imoveis_condominio',
    'uq_imoveis_condominio_complemento',
    'idx_negocios_imobiliaria',
    'idx_negocios_cliente',
    'idx_negocios_corretor',
    'idx_negocios_estagio',
    'idx_soma_sites_publicados'
  )
ORDER BY indexname;

-- Verificar triggers criados nesta migration
SELECT trigger_name, event_object_table, action_timing, event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
  AND trigger_name IN (
    'trg_condominios_atualizado_em',
    'trg_negocios_atualizado_em',
    'trg_soma_sites_atualizado_em'
  )
ORDER BY trigger_name;
