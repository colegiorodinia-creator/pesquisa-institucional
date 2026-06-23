-- =========================================================================
-- Script de Configuração do Banco de Dados no Supabase — Colégio Rodin
-- Execute este script no SQL Editor do seu projeto Supabase.
-- =========================================================================

-- 1. Remover tabelas anteriores se existirem (para reinicialização limpa)
DROP TABLE IF EXISTS respostas CASCADE;
DROP TABLE IF EXISTS mapeamento CASCADE;
DROP TABLE IF EXISTS professores_perfis CASCADE;

-- 2. Tabela de perfis de professores para mapear o login ao nome no Excel
CREATE TABLE professores_perfis (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    nome_professor TEXT NOT NULL, -- Ex: "Alberto" ou "Diretoria"
    nomes_exibicao TEXT[] NOT NULL, -- Ex: ARRAY['Alberto (Matemática)', 'Alberto (Matemática principal)']
    role TEXT DEFAULT 'professor' NOT NULL CHECK (role IN ('admin', 'professor')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Tabela de respostas consolidadas da Pesquisa 2026
CREATE TABLE respostas (
    id TEXT PRIMARY KEY,
    turma_pasta TEXT NOT NULL,
    turma_declarada TEXT NOT NULL,
    segmento TEXT NOT NULL,
    professor TEXT NOT NULL,
    disciplina TEXT NOT NULL,
    timestamp TEXT,
    comentario TEXT,
    didatica REAL,
    apoio REAL,
    tempo REAL,
    avaliacao REAL,
    clima REAL,
    respeito REAL,
    dominio REAL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Tabela de mapeamento administrativo de professores e disciplinas
CREATE TABLE mapeamento (
    turma_pasta TEXT NOT NULL,
    block_index INTEGER NOT NULL,
    start_column_index INTEGER NOT NULL,
    teacher_name TEXT NOT NULL,
    discipline TEXT NOT NULL,
    turmas JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    PRIMARY KEY (turma_pasta, block_index)
);

-- 5. Habilitar RLS (Row Level Security) para proteger as tabelas
ALTER TABLE professores_perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE respostas ENABLE ROW LEVEL SECURITY;
ALTER TABLE mapeamento ENABLE ROW LEVEL SECURITY;

-- 6. Políticas de Segurança para a tabela de Perfis
CREATE POLICY "Leitura de perfis por todos autenticados" ON professores_perfis
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Admin insere perfis" ON professores_perfis
    FOR INSERT TO authenticated WITH CHECK (
        (SELECT role FROM professores_perfis WHERE id = auth.uid()) = 'admin'
    );

CREATE POLICY "Admin atualiza perfis" ON professores_perfis
    FOR UPDATE TO authenticated USING (
        (SELECT role FROM professores_perfis WHERE id = auth.uid()) = 'admin'
    );

CREATE POLICY "Admin deleta perfis" ON professores_perfis
    FOR DELETE TO authenticated USING (
        (SELECT role FROM professores_perfis WHERE id = auth.uid()) = 'admin'
    );

-- 7. Políticas de Segurança para a tabela de Respostas
CREATE POLICY "Leitura de respostas baseada no perfil" ON respostas
    FOR SELECT TO authenticated USING (
        (EXISTS (SELECT 1 FROM professores_perfis WHERE id = auth.uid() AND role = 'admin'))
        OR
        (professor IN (SELECT unnest(nomes_exibicao) FROM professores_perfis WHERE id = auth.uid() AND role = 'professor'))
    );

-- 8. Políticas de Segurança para a tabela de Mapeamento
CREATE POLICY "Leitura de mapeamento apenas por admin" ON mapeamento
    FOR SELECT TO authenticated USING (
        (EXISTS (SELECT 1 FROM professores_perfis WHERE id = auth.uid() AND role = 'admin'))
    );

CREATE POLICY "Escrita de mapeamento apenas por admin" ON mapeamento
    FOR ALL TO authenticated USING (
        (EXISTS (SELECT 1 FROM professores_perfis WHERE id = auth.uid() AND role = 'admin'))
    );
