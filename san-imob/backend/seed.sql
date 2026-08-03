-- ============================================================
-- Soma Imob — Seed de dados (Imobiliária Valinhos)
--
-- Primeiro dado real do sistema. Rodar depois de schema_v2.sql (ou
-- schema.sql) num banco vazio — os INSERTs não usam ON CONFLICT nem
-- IF NOT EXISTS, de propósito: rodar duas vezes deve falhar de forma
-- óbvia (violação de UNIQUE/PK), não duplicar silenciosamente linhas.
--
-- IDs: UUIDs fixos e legíveis, um bloco de 100 por tabela, terminando
-- no mesmo número em toda a cadeia de referência sempre que possível
-- (ex: cliente ...0301 tem pipeline ...0401 e usa o telefone
-- terminado em 0301) — dá pra rastrear um registro em outra tabela só
-- de olhar o final do UUID, sem precisar consultar o banco:
--   ...0001            imobiliarias (1 linha)
--   ...0101 – 0103     usuarios (3)
--   ...0201 – 0220     imoveis (20)
--   ...0301 – 0325     clientes (25)
--   ...0401 – 0425     pipeline (25, mesmo índice do cliente correspondente)
--   ...0501 – 0508     visitas (8)
--   ...0601 – 0604     propostas (4)
--   ...0701 – 0703     alertas_proativos (3)
--
-- Datas: campos históricos (criado_em, atualizado_em) usam timestamps
-- fixos de 2025, já que não importa a data exata de criação pra
-- nenhuma regra de negócio. Campos que alimentam o scanner proativo
-- (ultimo_contato, data_visita, vencimento) usam NOW() +/- INTERVAL —
-- de propósito, pra que "lead sem contato há 7+ dias", "visita
-- agendada pros próximos dias" e "proposta vencendo em 5 dias"
-- continuem verdadeiros não importa quando este arquivo for rodado.
--
-- Dados fictícios: nenhum nome, telefone ou e-mail aqui corresponde a
-- pessoa ou empresa real. Telefones seguem (19) 98700-XXXX, onde XXXX
-- é o final do próprio UUID do registro (mesmo truque de legibilidade
-- acima). E-mails de clientes usam o domínio inexistente
-- emailexemplo.com.br.
-- ============================================================


-- ===== IMOBILIARIAS =====
INSERT INTO imobiliarias (id, nome, plano, criado_em) VALUES
('00000000-0000-0000-0000-000000000001', 'Imobiliária Valinhos', 'premium', '2024-01-15 09:00:00-03');


-- ===== USUARIOS =====
-- 1 gestora + 2 corretores. E-mails no formato pedido (gestorN/corretorN),
-- não nome.sobrenome — evita qualquer aparência de e-mail real.
INSERT INTO usuarios (id, imobiliaria_id, nome, email, cargo, criado_em) VALUES
('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000001', 'Maria Silva', 'gestor1@imobiliariavalinhos.com.br', 'gestor', '2024-01-15 09:30:00-03'),
('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000001', 'João Santos', 'corretor1@imobiliariavalinhos.com.br', 'corretor', '2024-02-01 10:00:00-03'),
('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000001', 'Ana Costa', 'corretor2@imobiliariavalinhos.com.br', 'corretor', '2024-02-10 10:00:00-03');


-- ===== IMOVEIS =====
-- 10 apartamentos (AP001-AP010, R$280k-R$1,2M), 6 casas (CA001-CA006,
-- R$420k-R$980k), 3 coberturas (CO001-CO003) e 1 terreno (TE001).
-- Bairros de Valinhos/SP reais ou plausíveis para a região.
INSERT INTO imoveis (
  id, imobiliaria_id, codigo, tipo, bairro, preco, valor_aluguel, status,
  quartos, suites, banheiros, vagas, area_m2, exclusivo, descricao,
  dias_carteira, criado_em, atualizado_em
) VALUES
('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000001', 'AP001', 'Apartamento', 'Centro', 420000.00, NULL, 'ativo', 2, 0, 1, 1, 62.0, false, 'Apartamento reformado, próximo ao comércio do Centro.', 18, '2025-06-01 09:00:00-03', '2025-06-01 09:00:00-03'),
('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000001', 'AP002', 'Apartamento', 'Jardim São Marcos', 385000.00, NULL, 'ativo', 2, 1, 2, 1, 68.0, true, 'Andar alto, vista livre, condomínio com portaria 24h.', 9, '2025-06-10 09:00:00-03', '2025-06-10 09:00:00-03'),
('00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000001', 'AP003', 'Apartamento', 'Vila Faria', 620000.00, NULL, 'ativo', 3, 1, 2, 2, 92.0, false, NULL, 34, '2025-05-15 09:00:00-03', '2025-05-15 09:00:00-03'),
('00000000-0000-0000-0000-000000000204', '00000000-0000-0000-0000-000000000001', 'AP004', 'Apartamento', 'Bosque de Valinhos', 780000.00, NULL, 'ativo', 3, 1, 2, 2, 98.0, true, 'Condomínio fechado com área de lazer completa.', 12, '2025-06-07 09:00:00-03', '2025-06-07 09:00:00-03'),
('00000000-0000-0000-0000-000000000205', '00000000-0000-0000-0000-000000000001', 'AP005', 'Apartamento', 'Nova Suíça', 280000.00, 1800.00, 'ativo', 1, 0, 1, 1, 45.0, false, 'Ideal para investidor, próximo à rodovia.', 71, '2025-04-08 09:00:00-03', '2025-04-08 09:00:00-03'),
('00000000-0000-0000-0000-000000000206', '00000000-0000-0000-0000-000000000001', 'AP006', 'Apartamento', 'Centro', 690000.00, NULL, 'reservado', 3, 1, 2, 2, 95.0, false, NULL, 6, '2025-06-13 09:00:00-03', '2025-06-16 14:00:00-03'),
('00000000-0000-0000-0000-000000000207', '00000000-0000-0000-0000-000000000001', 'AP007', 'Apartamento', 'Chácara Flórida', 1150000.00, NULL, 'ativo', 4, 2, 3, 3, 160.0, true, 'Alto padrão, acabamento premium, 160m² de área privativa.', 15, '2025-06-04 09:00:00-03', '2025-06-04 09:00:00-03'),
('00000000-0000-0000-0000-000000000208', '00000000-0000-0000-0000-000000000001', 'AP008', 'Apartamento', 'Jardim Regina', 410000.00, NULL, 'ativo', 2, 0, 1, 1, 58.0, false, NULL, 40, '2025-04-30 09:00:00-03', '2025-04-30 09:00:00-03'),
('00000000-0000-0000-0000-000000000209', '00000000-0000-0000-0000-000000000001', 'AP009', 'Apartamento', 'Vila São João', 450000.00, NULL, 'vendido', 2, 1, 2, 1, 65.0, false, NULL, 120, '2025-02-10 09:00:00-03', '2025-06-01 11:00:00-03'),
('00000000-0000-0000-0000-000000000210', '00000000-0000-0000-0000-000000000001', 'AP010', 'Apartamento', 'Parque das Videiras', 980000.00, NULL, 'ativo', 3, 1, 2, 2, 110.0, true, 'Vista para os vinhedos, diferencial único na região.', 22, '2025-05-28 09:00:00-03', '2025-05-28 09:00:00-03'),

('00000000-0000-0000-0000-000000000211', '00000000-0000-0000-0000-000000000001', 'CA001', 'Casa', 'Recanto das Palmeiras', 620000.00, NULL, 'ativo', 3, 1, 2, 2, 140.0, false, 'Casa térrea com quintal amplo.', 28, '2025-05-22 09:00:00-03', '2025-05-22 09:00:00-03'),
('00000000-0000-0000-0000-000000000212', '00000000-0000-0000-0000-000000000001', 'CA002', 'Casa', 'Vila São João', 540000.00, NULL, 'ativo', 3, 1, 2, 2, 150.0, true, NULL, 8, '2025-06-11 09:00:00-03', '2025-06-11 09:00:00-03'),
('00000000-0000-0000-0000-000000000213', '00000000-0000-0000-0000-000000000001', 'CA003', 'Casa', 'Chácara Flórida', 890000.00, NULL, 'ativo', 4, 2, 3, 3, 220.0, false, 'Sobrado com piscina e churrasqueira.', 50, '2025-04-20 09:00:00-03', '2025-04-20 09:00:00-03'),
('00000000-0000-0000-0000-000000000214', '00000000-0000-0000-0000-000000000001', 'CA004', 'Casa', 'Nova Suíça', 420000.00, NULL, 'ativo', 2, 0, 1, 1, 100.0, false, NULL, 65, '2025-04-05 09:00:00-03', '2025-04-05 09:00:00-03'),
('00000000-0000-0000-0000-000000000215', '00000000-0000-0000-0000-000000000001', 'CA005', 'Casa', 'Bosque de Valinhos', 980000.00, NULL, 'reservado', 4, 2, 3, 4, 260.0, true, 'Casa de alto padrão em condomínio fechado, ideal para família grande.', 95, '2025-03-01 09:00:00-03', '2025-06-14 10:00:00-03'),
('00000000-0000-0000-0000-000000000216', '00000000-0000-0000-0000-000000000001', 'CA006', 'Casa', 'Jardim Regina', 675000.00, NULL, 'ativo', 3, 1, 2, 2, 135.0, false, NULL, 19, '2025-06-03 09:00:00-03', '2025-06-03 09:00:00-03'),

('00000000-0000-0000-0000-000000000217', '00000000-0000-0000-0000-000000000001', 'CO001', 'Cobertura', 'Centro', 1050000.00, NULL, 'ativo', 3, 1, 3, 2, 145.0, true, 'Cobertura duplex com terraço gourmet.', 11, '2025-06-08 09:00:00-03', '2025-06-08 09:00:00-03'),
('00000000-0000-0000-0000-000000000218', '00000000-0000-0000-0000-000000000001', 'CO002', 'Cobertura', 'Vila Faria', 1180000.00, NULL, 'ativo', 4, 2, 3, 3, 180.0, false, NULL, 20, '2025-05-30 09:00:00-03', '2025-05-30 09:00:00-03'),
('00000000-0000-0000-0000-000000000219', '00000000-0000-0000-0000-000000000001', 'CO003', 'Cobertura', 'Bosque de Valinhos', 890000.00, NULL, 'ativo', 3, 1, 2, 2, 130.0, false, NULL, 33, '2025-05-08 09:00:00-03', '2025-05-08 09:00:00-03'),

('00000000-0000-0000-0000-000000000220', '00000000-0000-0000-0000-000000000001', 'TE001', 'Terreno', 'Nova Suíça', 350000.00, NULL, 'ativo', NULL, NULL, NULL, NULL, 450.0, false, 'Terreno plano, pronto para construir, escritura em dia.', 95, '2025-03-01 09:00:00-03', '2025-03-01 09:00:00-03');


-- ===== CLIENTES =====
-- 25 clientes: 6 quentes (score 75-95), 10 mornos (40-74), 9 frios (0-39).
-- Endereço preenchido só para os 6 quentes (mais avançados no funil);
-- e-mail presente em ~2/3 dos registros, ausente no restante — reflete
-- uma base real, onde nem todo lead tem e-mail cadastrado.
INSERT INTO clientes (
  id, imobiliaria_id, nome, telefone, email, endereco, origem,
  score_fechamento, temperatura, corretor_id, ultimo_contato, observacoes, criado_em
) VALUES
-- Quentes (75-95)
('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000001', 'Marcos Andrade', '(19) 98700-0301', 'marcos.andrade@emailexemplo.com.br', 'Rua das Palmeiras, 245 — Jardim São Marcos, Valinhos/SP', 'whatsapp', 94, 'quente', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '9 days', 'Prefere contato por WhatsApp à noite.', '2025-05-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000001', 'Fernanda Lima', '(19) 98700-0302', 'fernanda.lima@emailexemplo.com.br', 'Av. Costa e Silva, 1120 — Centro, Valinhos/SP', 'site', 91, 'quente', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '1 days', NULL, '2025-05-25 10:00:00-03'),
('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000001', 'Ricardo Souza', '(19) 98700-0303', 'ricardo.souza@emailexemplo.com.br', 'Rua João Rodrigues, 88 — Vila Faria, Valinhos/SP', 'portal', 87, 'quente', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '3 days', NULL, '2025-05-10 10:00:00-03'),
('00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000001', 'Camila Ferreira', '(19) 98700-0304', NULL, 'Rua das Uvas, 310 — Nova Suíça, Valinhos/SP', 'whatsapp', 83, 'quente', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '2 days', NULL, '2025-06-02 10:00:00-03'),
('00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000001', 'Rafael Oliveira', '(19) 98700-0305', 'rafael.oliveira@emailexemplo.com.br', 'Rua Sete de Setembro, 502 — Bosque de Valinhos, Valinhos/SP', 'facebook', 79, 'quente', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '4 days', NULL, '2025-04-28 10:00:00-03'),
('00000000-0000-0000-0000-000000000306', '00000000-0000-0000-0000-000000000001', 'Beatriz Almeida', '(19) 98700-0306', 'beatriz.almeida@emailexemplo.com.br', 'Rua Barão de Itapura, 77 — Jardim Regina, Valinhos/SP', 'portal', 76, 'quente', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '1 days', NULL, '2025-06-05 10:00:00-03'),

-- Mornos (40-74)
('00000000-0000-0000-0000-000000000307', '00000000-0000-0000-0000-000000000001', 'Juliana Prado', '(19) 98700-0307', 'juliana.prado@emailexemplo.com.br', NULL, 'site', 74, 'morno', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '4 days', NULL, '2025-05-01 10:00:00-03'),
('00000000-0000-0000-0000-000000000308', '00000000-0000-0000-0000-000000000001', 'Bruno Carvalho', '(19) 98700-0308', NULL, NULL, 'whatsapp', 69, 'morno', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '5 days', NULL, '2025-04-15 10:00:00-03'),
('00000000-0000-0000-0000-000000000309', '00000000-0000-0000-0000-000000000001', 'Patrícia Gomes', '(19) 98700-0309', 'patricia.gomes@emailexemplo.com.br', NULL, 'portal', 65, 'morno', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '6 days', NULL, '2025-03-22 10:00:00-03'),
('00000000-0000-0000-0000-000000000310', '00000000-0000-0000-0000-000000000001', 'Eduardo Martins', '(19) 98700-0310', NULL, NULL, 'facebook', 61, 'morno', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '6 days', NULL, '2025-03-18 10:00:00-03'),
('00000000-0000-0000-0000-000000000311', '00000000-0000-0000-0000-000000000001', 'Larissa Barbosa', '(19) 98700-0311', 'larissa.barbosa@emailexemplo.com.br', NULL, 'whatsapp', 58, 'morno', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '7 days', NULL, '2025-02-27 10:00:00-03'),
('00000000-0000-0000-0000-000000000312', '00000000-0000-0000-0000-000000000001', 'Diego Ribeiro', '(19) 98700-0312', NULL, NULL, 'site', 54, 'morno', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '7 days', NULL, '2025-02-14 10:00:00-03'),
('00000000-0000-0000-0000-000000000313', '00000000-0000-0000-0000-000000000001', 'Vanessa Teixeira', '(19) 98700-0313', 'vanessa.teixeira@emailexemplo.com.br', NULL, 'portal', 50, 'morno', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '8 days', NULL, '2025-01-30 10:00:00-03'),
('00000000-0000-0000-0000-000000000314', '00000000-0000-0000-0000-000000000001', 'Rodrigo Pereira', '(19) 98700-0314', NULL, NULL, 'facebook', 47, 'morno', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '8 days', NULL, '2025-01-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000315', '00000000-0000-0000-0000-000000000001', 'Camila Duarte', '(19) 98700-0315', 'camila.duarte@emailexemplo.com.br', NULL, 'whatsapp', 44, 'morno', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '9 days', NULL, '2025-01-05 10:00:00-03'),
('00000000-0000-0000-0000-000000000316', '00000000-0000-0000-0000-000000000001', 'Thiago Cardoso', '(19) 98700-0316', NULL, NULL, 'site', 41, 'morno', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '9 days', NULL, '2024-12-18 10:00:00-03'),

-- Frios (0-39)
('00000000-0000-0000-0000-000000000317', '00000000-0000-0000-0000-000000000001', 'Patrícia Nunes', '(19) 98700-0317', 'patricia.nunes@emailexemplo.com.br', NULL, 'portal', 38, 'frio', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '12 days', NULL, '2024-12-01 10:00:00-03'),
('00000000-0000-0000-0000-000000000318', '00000000-0000-0000-0000-000000000001', 'Carlos Eduardo', '(19) 98700-0318', NULL, NULL, 'facebook', 33, 'frio', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '15 days', NULL, '2024-11-15 10:00:00-03'),
('00000000-0000-0000-0000-000000000319', '00000000-0000-0000-0000-000000000001', 'Ana Beatriz', '(19) 98700-0319', 'ana.beatriz@emailexemplo.com.br', NULL, 'whatsapp', 29, 'frio', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '18 days', NULL, '2024-11-02 10:00:00-03'),
('00000000-0000-0000-0000-000000000320', '00000000-0000-0000-0000-000000000001', 'André Monteiro', '(19) 98700-0320', NULL, NULL, 'site', 25, 'frio', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '21 days', NULL, '2024-10-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000321', '00000000-0000-0000-0000-000000000001', 'Fernanda Rocha', '(19) 98700-0321', 'fernanda.rocha@emailexemplo.com.br', NULL, 'portal', 21, 'frio', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '25 days', NULL, '2024-10-05 10:00:00-03'),
('00000000-0000-0000-0000-000000000322', '00000000-0000-0000-0000-000000000001', 'Gustavo Lima', '(19) 98700-0322', NULL, NULL, 'facebook', 17, 'frio', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '30 days', NULL, '2024-09-22 10:00:00-03'),
('00000000-0000-0000-0000-000000000323', '00000000-0000-0000-0000-000000000001', 'Isabela Santos', '(19) 98700-0323', 'isabela.santos@emailexemplo.com.br', NULL, 'whatsapp', 13, 'frio', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '35 days', NULL, '2024-09-10 10:00:00-03'),
('00000000-0000-0000-0000-000000000324', '00000000-0000-0000-0000-000000000001', 'Leonardo Costa', '(19) 98700-0324', NULL, NULL, 'site', 8, 'frio', '00000000-0000-0000-0000-000000000103', NOW() - INTERVAL '40 days', 'Pediu para retomar contato só depois das férias, em janeiro.', '2024-09-02 10:00:00-03'),
('00000000-0000-0000-0000-000000000325', '00000000-0000-0000-0000-000000000001', 'Mariana Alves', '(19) 98700-0325', 'mariana.alves@emailexemplo.com.br', NULL, 'portal', 2, 'frio', '00000000-0000-0000-0000-000000000102', NOW() - INTERVAL '45 days', NULL, '2024-08-25 10:00:00-03');


-- ===== PIPELINE =====
-- 1 linha por cliente (mesmo índice numérico). Quentes em visita/proposta,
-- mornos em em_atendimento, frios em aberto — exatamente como pedido.
-- Nota: Ricardo Souza (0303) segue em "visita" mesmo tendo uma proposta
-- já aceita (ver seção PROPOSTAS) — de propósito: no CRM real, o card do
-- Kanban nem sempre é arrastado no mesmo instante em que o status muda,
-- é um lag realista, não um erro de dado.
INSERT INTO pipeline (id, imobiliaria_id, cliente_id, etapa, observacoes, criado_em, atualizado_em) VALUES
('00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000301', 'proposta', NULL, '2025-05-20 10:00:00-03', '2025-06-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000302', 'proposta', NULL, '2025-05-25 10:00:00-03', '2025-06-18 10:00:00-03'),
('00000000-0000-0000-0000-000000000403', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000303', 'visita', NULL, '2025-05-10 10:00:00-03', '2025-06-14 10:00:00-03'),
('00000000-0000-0000-0000-000000000404', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000304', 'visita', NULL, '2025-06-02 10:00:00-03', '2025-06-19 10:00:00-03'),
('00000000-0000-0000-0000-000000000405', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000305', 'proposta', NULL, '2025-04-28 10:00:00-03', '2025-06-05 10:00:00-03'),
('00000000-0000-0000-0000-000000000406', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000306', 'visita', NULL, '2025-06-05 10:00:00-03', '2025-06-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000407', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000307', 'em_atendimento', NULL, '2025-05-01 10:00:00-03', '2025-06-16 10:00:00-03'),
('00000000-0000-0000-0000-000000000408', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000308', 'em_atendimento', NULL, '2025-04-15 10:00:00-03', '2025-06-15 10:00:00-03'),
('00000000-0000-0000-0000-000000000409', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000309', 'em_atendimento', NULL, '2025-03-22 10:00:00-03', '2025-06-14 10:00:00-03'),
('00000000-0000-0000-0000-000000000410', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000310', 'em_atendimento', NULL, '2025-03-18 10:00:00-03', '2025-06-13 10:00:00-03'),
('00000000-0000-0000-0000-000000000411', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000311', 'em_atendimento', NULL, '2025-02-27 10:00:00-03', '2025-06-12 10:00:00-03'),
('00000000-0000-0000-0000-000000000412', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000312', 'em_atendimento', NULL, '2025-02-14 10:00:00-03', '2025-06-11 10:00:00-03'),
('00000000-0000-0000-0000-000000000413', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000313', 'em_atendimento', NULL, '2025-01-30 10:00:00-03', '2025-06-10 10:00:00-03'),
('00000000-0000-0000-0000-000000000414', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000314', 'em_atendimento', NULL, '2025-01-20 10:00:00-03', '2025-06-09 10:00:00-03'),
('00000000-0000-0000-0000-000000000415', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000315', 'em_atendimento', NULL, '2025-01-05 10:00:00-03', '2025-06-08 10:00:00-03'),
('00000000-0000-0000-0000-000000000416', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000316', 'em_atendimento', NULL, '2024-12-18 10:00:00-03', '2025-06-07 10:00:00-03'),
('00000000-0000-0000-0000-000000000417', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000317', 'aberto', NULL, '2024-12-01 10:00:00-03', '2024-12-01 10:00:00-03'),
('00000000-0000-0000-0000-000000000418', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000318', 'aberto', NULL, '2024-11-15 10:00:00-03', '2024-11-15 10:00:00-03'),
('00000000-0000-0000-0000-000000000419', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000319', 'aberto', NULL, '2024-11-02 10:00:00-03', '2024-11-02 10:00:00-03'),
('00000000-0000-0000-0000-000000000420', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000320', 'aberto', NULL, '2024-10-20 10:00:00-03', '2024-10-20 10:00:00-03'),
('00000000-0000-0000-0000-000000000421', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000321', 'aberto', NULL, '2024-10-05 10:00:00-03', '2024-10-05 10:00:00-03'),
('00000000-0000-0000-0000-000000000422', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000322', 'aberto', NULL, '2024-09-22 10:00:00-03', '2024-09-22 10:00:00-03'),
('00000000-0000-0000-0000-000000000423', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000323', 'aberto', NULL, '2024-09-10 10:00:00-03', '2024-09-10 10:00:00-03'),
('00000000-0000-0000-0000-000000000424', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000324', 'aberto', 'Cliente pediu para não ser contatado até janeiro.', '2024-09-02 10:00:00-03', '2024-09-02 10:00:00-03'),
('00000000-0000-0000-0000-000000000425', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000325', 'aberto', NULL, '2024-08-25 10:00:00-03', '2024-08-25 10:00:00-03');


-- ===== VISITAS =====
-- 5 realizadas (passado), 2 agendadas (próximos dias) e 1 cancelada.
INSERT INTO visitas (id, imobiliaria_id, cliente_id, imovel_id, data_visita, status, observacoes) VALUES
('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000203', NOW() - INTERVAL '12 days', 'realizada', 'Cliente gostou do apartamento, pediu para pensar mais um pouco.'),
('00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000304', '00000000-0000-0000-0000-000000000212', NOW() - INTERVAL '8 days', 'realizada', 'Achou o quintal um pouco pequeno para os planos da família.'),
('00000000-0000-0000-0000-000000000503', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000306', '00000000-0000-0000-0000-000000000217', NOW() - INTERVAL '5 days', 'realizada', 'Muito interessada, deve encaminhar proposta em breve.'),
('00000000-0000-0000-0000-000000000504', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000218', NOW() - INTERVAL '20 days', 'realizada', 'Aguardando aprovação de financiamento antes de avançar.'),
('00000000-0000-0000-0000-000000000505', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000207', NOW() - INTERVAL '25 days', 'realizada', 'Visitou acompanhado da esposa, ambos gostaram do padrão do imóvel.'),
('00000000-0000-0000-0000-000000000506', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000219', NOW() + INTERVAL '2 days', 'agendada', NULL),
('00000000-0000-0000-0000-000000000507', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000307', '00000000-0000-0000-0000-000000000211', NOW() + INTERVAL '4 days', 'agendada', NULL),
('00000000-0000-0000-0000-000000000508', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000308', '00000000-0000-0000-0000-000000000208', NOW() - INTERVAL '3 days', 'cancelada', 'Cliente remarcou por motivo pessoal, aguardando nova data.');


-- ===== PROPOSTAS =====
-- 2 abertas vencendo nos próximos 5 dias (disparam alerta de vencimento),
-- 1 aceita e 1 vencida. Valores negociados abaixo do preço de tabela do
-- imóvel, como é comum numa proposta real.
INSERT INTO propostas (id, imobiliaria_id, cliente_id, imovel_id, valor, condicoes, vencimento, status, criado_em) VALUES
('00000000-0000-0000-0000-000000000601', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000204', 760000.00, 'Financiamento 70%, entrada 30%', NOW() + INTERVAL '3 days', 'aberta', NOW() - INTERVAL '4 days'),
('00000000-0000-0000-0000-000000000602', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000218', 1150000.00, 'À vista, com desconto de 5% sobre o valor de tabela', NOW() + INTERVAL '5 days', 'aberta', NOW() - INTERVAL '6 days'),
('00000000-0000-0000-0000-000000000603', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000203', 605000.00, 'Financiamento Caixa, entrada 20%', NOW() - INTERVAL '2 days', 'aceita', NOW() - INTERVAL '11 days'),
('00000000-0000-0000-0000-000000000604', '00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000305', '00000000-0000-0000-0000-000000000207', 1100000.00, 'Financiamento 80%', NOW() - INTERVAL '15 days', 'vencida', NOW() - INTERVAL '23 days');


-- ===== ALERTAS PROATIVOS =====
-- 1 de cada tipo, todos pendentes (nunca enviados automaticamente —
-- ver jobs/proactive_scanner.py: sempre esperam aprovação manual).
INSERT INTO alertas_proativos (id, imobiliaria_id, tipo, cliente_id, imovel_id, proposta_id, mensagem_sugerida, status, criado_em, aprovado_em) VALUES
('00000000-0000-0000-0000-000000000701', '00000000-0000-0000-0000-000000000001', 'LEAD_SEM_CONTATO', '00000000-0000-0000-0000-000000000301', NULL, NULL, 'Marcos Andrade está sem contato há mais de uma semana, mesmo com score 94 e proposta em aberto no AP004. Vale reforçar contato antes que o interesse esfrie.', 'pendente', NOW() - INTERVAL '1 days', NULL),
('00000000-0000-0000-0000-000000000702', '00000000-0000-0000-0000-000000000001', 'PROPOSTA_VENCENDO', '00000000-0000-0000-0000-000000000302', NULL, '00000000-0000-0000-0000-000000000602', 'A proposta de Fernanda Lima na cobertura CO002 vence em 5 dias e não há contato registrado recentemente. Vale confirmar o andamento antes do prazo.', 'pendente', NOW() - INTERVAL '1 days', NULL),
('00000000-0000-0000-0000-000000000703', '00000000-0000-0000-0000-000000000001', 'PROPRIETARIO_SEM_FEEDBACK', NULL, '00000000-0000-0000-0000-000000000220', NULL, 'O terreno TE001 está há 95 dias na carteira sem nenhuma visita registrada. Vale enviar um retorno ao proprietário sobre a estratégia de divulgação.', 'pendente', NOW() - INTERVAL '2 days', NULL);


-- ===== VERIFICAÇÃO =====
-- Rode os SELECTs abaixo depois do seed pra confirmar que tudo entrou
-- certo. Resultado esperado ao lado de cada bloco.

-- Contagem geral por tabela — esperado: alertas_proativos=3, clientes=25,
-- imobiliarias=1, imoveis=20, pipeline=25, propostas=4, usuarios=3, visitas=8.
SELECT 'imobiliarias' AS tabela, COUNT(*) AS total FROM imobiliarias
UNION ALL SELECT 'usuarios', COUNT(*) FROM usuarios
UNION ALL SELECT 'imoveis', COUNT(*) FROM imoveis
UNION ALL SELECT 'clientes', COUNT(*) FROM clientes
UNION ALL SELECT 'pipeline', COUNT(*) FROM pipeline
UNION ALL SELECT 'visitas', COUNT(*) FROM visitas
UNION ALL SELECT 'propostas', COUNT(*) FROM propostas
UNION ALL SELECT 'alertas_proativos', COUNT(*) FROM alertas_proativos
ORDER BY tabela;

-- Clientes por temperatura — esperado: frio=9, morno=10, quente=6.
SELECT temperatura, COUNT(*) AS total
FROM clientes
GROUP BY temperatura
ORDER BY temperatura;

-- Imóveis por prefixo de código — esperado: AP=10, CA=6, CO=3, TE=1.
SELECT LEFT(codigo, 2) AS prefixo, COUNT(*) AS total
FROM imoveis
GROUP BY LEFT(codigo, 2)
ORDER BY prefixo;

-- Pipeline por etapa — esperado: aberto=9, em_atendimento=10, proposta=3, visita=3.
SELECT etapa, COUNT(*) AS total
FROM pipeline
GROUP BY etapa
ORDER BY etapa;

-- Visitas por status — esperado: agendada=2, cancelada=1, realizada=5.
SELECT status, COUNT(*) AS total
FROM visitas
GROUP BY status
ORDER BY status;

-- Propostas por status — esperado: aberta=2, aceita=1, vencida=1.
SELECT status, COUNT(*) AS total
FROM propostas
GROUP BY status
ORDER BY status;

-- Alertas pendentes por tipo — esperado: 1 linha de cada um dos 3 tipos.
SELECT tipo, COUNT(*) AS total
FROM alertas_proativos
WHERE status = 'pendente'
GROUP BY tipo
ORDER BY tipo;
