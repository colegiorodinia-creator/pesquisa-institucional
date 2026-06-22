import os
import sys
import pandas as pd
import json
import re
import sqlite3

# Garantir UTF-8 no console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"
workspace_mapping_path = os.path.join(workspace, "mapeamento_professores.json")
db_path = os.path.join(workspace, "pesquisa.db")

# Mapeamento estático e limpo dos blocos de colunas de cada CSV para o respectivo professor e disciplina
# Baseado na ordem física dos PDFs e análise de blocos
MAPPING_ESTATICO = {
    "1ª séries": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Guilherme (Literatura)", "discipline": "Literatura"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Tati Fadel (Redação)", "discipline": "Redação"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Jessica (Arte)", "discipline": "Arte"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Carlos (Física)", "discipline": "Física"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Rita (Gramática)", "discipline": "Gramática"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Oka (Biologia)", "discipline": "Biologia"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Emerson (História)", "discipline": "História"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Juliana (Inglês)", "discipline": "Inglês"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Vitor (Física)", "discipline": "Física"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Rafael Reis (Filosofia)", "discipline": "Filosofia"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Diego (Matemática)", "discipline": "Matemática"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Altair (Matemática)", "discipline": "Matemática"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Aline (Química)", "discipline": "Química"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Marcos (Química)", "discipline": "Química"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Rafael Reis (Sociologia)", "discipline": "Sociologia"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Lucas (Geografia)", "discipline": "Geografia"},
        {"block_index": 16, "start_column_index": 114, "teacher_name": "Marcio (Matemática)", "discipline": "Matemática"},
        {"block_index": 17, "start_column_index": 121, "teacher_name": "Andreia (Projeto de Vida)", "discipline": "Projeto de Vida"},
        {"block_index": 18, "start_column_index": 128, "teacher_name": "Ben (Biologia)", "discipline": "Biologia"},
        {"block_index": 19, "start_column_index": 137, "teacher_name": "Rafael Pavani (História - Itinerário)", "discipline": "História"},
        {"block_index": 20, "start_column_index": 144, "teacher_name": "Emerson (História - Itinerário)", "discipline": "História"},
        {"block_index": 21, "start_column_index": 151, "teacher_name": "Lucas (Geografia - Itinerário)", "discipline": "Geografia"},
        {"block_index": 22, "start_column_index": 158, "teacher_name": "Marcio (Matemática - Itinerário)", "discipline": "Matemática"},
        {"block_index": 23, "start_column_index": 165, "teacher_name": "Vitor (Física - Itinerário)", "discipline": "Física"},
        {"block_index": 24, "start_column_index": 172, "teacher_name": "Marcos (Química - Itinerário)", "discipline": "Química"},
        {"block_index": 25, "start_column_index": 179, "teacher_name": "Ben (Biologia - Itinerário)", "discipline": "Biologia"}
    ],
    "2ª séries": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Guilherme (Literatura)", "discipline": "Literatura"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Tati Fadel (Redação)", "discipline": "Redação"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Rafael Reis (Estudo da Contemporaneidade)", "discipline": "Estudo da Contemporaneidade"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Carlos (Física)", "discipline": "Física"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Rita (Gramática)", "discipline": "Gramática"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Oka (Biologia)", "discipline": "Biologia"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Juliana (Inglês)", "discipline": "Inglês"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Vitor (Física)", "discipline": "Física"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Rafael Reis (Filosofia)", "discipline": "Filosofia"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Alberto (Matemática)", "discipline": "Matemática"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Altair (Matemática)", "discipline": "Matemática"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Aline (Química)", "discipline": "Química"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Marcos (Química)", "discipline": "Química"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Rafael Reis (Sociologia)", "discipline": "Sociologia"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Lucas (Geografia)", "discipline": "Geografia"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Marcio (Matemática)", "discipline": "Matemática"},
        {"block_index": 16, "start_column_index": 114, "teacher_name": "Andreia (Projeto de Vida)", "discipline": "Projeto de Vida"},
        {"block_index": 17, "start_column_index": 121, "teacher_name": "Ben (Biologia)", "discipline": "Biologia"},
        {"block_index": 18, "start_column_index": 128, "teacher_name": "Rafael Pavani (História)", "discipline": "História"},
        {"block_index": 19, "start_column_index": 136, "teacher_name": "Rafael Pavani (História - Itinerário)", "discipline": "História"},
        {"block_index": 20, "start_column_index": 143, "teacher_name": "Lucas (Geografia - Itinerário)", "discipline": "Geografia"},
        {"block_index": 21, "start_column_index": 150, "teacher_name": "Alberto (Matemática - Itinerário)", "discipline": "Matemática"},
        {"block_index": 22, "start_column_index": 157, "teacher_name": "Vitor (Física - Itinerário)", "discipline": "Física"},
        {"block_index": 23, "start_column_index": 164, "teacher_name": "Marcos (Química - Itinerário)", "discipline": "Química"},
        {"block_index": 24, "start_column_index": 171, "teacher_name": "Ben (Biologia - Itinerário)", "discipline": "Biologia"}
    ],
    "3ª série": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Aline (Química)", "discipline": "Química"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Altair (Matemática)", "discipline": "Matemática"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Oka (Biologia)", "discipline": "Biologia"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Ben (Biologia)", "discipline": "Biologia"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Carlos (Física)", "discipline": "Física"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Evandro (Geografia)", "discipline": "Geografia"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Guilherme (Literatura)", "discipline": "Literatura"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Juliana (Inglês)", "discipline": "Inglês"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Lucas (Geografia)", "discipline": "Geografia"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Marcos (Química)", "discipline": "Química"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Ricardo (História)", "discipline": "História"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Tati Fadel (Redação)", "discipline": "Redação"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Thiago (Biologia)", "discipline": "Biologia"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Vitor (Física)", "discipline": "Física"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Rafael Reis (Filosofia/Sociologia)", "discipline": "Filosofia"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Marcio (Matemática)", "discipline": "Matemática"},
        {"block_index": 16, "start_column_index": 114, "teacher_name": "Rafael Pavani (História)", "discipline": "História"}
    ],
    "6º anos": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Alice (Arte - Dança)", "discipline": "Arte"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Danielle (Ciências)", "discipline": "Ciências"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Diego (Matemática)", "discipline": "Matemática"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Karen (Matemática)", "discipline": "Matemática"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Luana (Matemática)", "discipline": "Matemática"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Márcia (Arte - Visual)", "discipline": "Arte"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Mário (Geografia)", "discipline": "Geografia"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Monique (Lab. Inteligência Emocional)", "discipline": "Laboratório"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Betão (Matemática)", "discipline": "Matemática"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Pavarina (Ed. Física)", "discipline": "Ed. Física"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Renatinha (Inglês)", "discipline": "Inglês"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Ricardo (História)", "discipline": "História"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Rita Quiles (Gramática)", "discipline": "Gramática"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Valeska (Inglês)", "discipline": "Inglês"}
    ],
    "7º anos": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Alberto (Matemática)", "discipline": "Matemática"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Ariany (Matemática)", "discipline": "Matemática"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Daniela (Ciências)", "discipline": "Ciências"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Danielle (Matemática)", "discipline": "Matemática"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Karen (Matemática)", "discipline": "Matemática"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Márcia (Arte - Visual)", "discipline": "Arte"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Mário (Geografia)", "discipline": "Geografia"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Monique (Lab. Inteligência Emocional)", "discipline": "Laboratório"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Betão (Matemática)", "discipline": "Matemática"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Pavarina (Ed. Física)", "discipline": "Ed. Física"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Renatinha (Inglês)", "discipline": "Inglês"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Ricardo (História)", "discipline": "História"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Rita Quiles (Gramática)", "discipline": "Gramática"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Samarina (Ciências)", "discipline": "Ciências"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Thomas (Ciência Aplicada)", "discipline": "Ciência Aplicada"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Valeska (Inglês)", "discipline": "Inglês"}
    ],
    "8º anos": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Andreia (Ciências Sociais)", "discipline": "Ciências"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Carla Back (Matemática)", "discipline": "Matemática"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Carlos Dias (Matemática)", "discipline": "Matemática"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Ciro (Leitura e Gramática)", "discipline": "Gramática"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Daniela (Inglês)", "discipline": "Inglês"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Daniela (Ciência Aplicada)", "discipline": "Ciência Aplicada"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Danielle (Matemática)", "discipline": "Matemática"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Evelyn (História)", "discipline": "História"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Fabiano (Redação)", "discipline": "Redação"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "João (Arte - Teatro)", "discipline": "Arte"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Kaique (Geografia)", "discipline": "Geografia"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Márcia (Arte - Visual)", "discipline": "Arte"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Monique (Lab. Inteligência Emocional)", "discipline": "Laboratório"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Pavarina (Ed. Física)", "discipline": "Ed. Física"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Thiago (Ciências)", "discipline": "Ciências"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Thomas (Ciência Aplicada)", "discipline": "Ciência Aplicada"},
        {"block_index": 16, "start_column_index": 114, "teacher_name": "Valeska (Inglês)", "discipline": "Inglês"}
    ],
    "9º anos": [
        {"block_index": 0, "start_column_index": 2, "teacher_name": "Andreia (Ciências Sociais)", "discipline": "Ciências"},
        {"block_index": 1, "start_column_index": 9, "teacher_name": "Carla Back (Matemática)", "discipline": "Matemática"},
        {"block_index": 2, "start_column_index": 16, "teacher_name": "Carlos Dias (Matemática)", "discipline": "Matemática"},
        {"block_index": 3, "start_column_index": 23, "teacher_name": "Ciro (Leitura e Gramática)", "discipline": "Gramática"},
        {"block_index": 4, "start_column_index": 30, "teacher_name": "Daniela (Inglês)", "discipline": "Inglês"},
        {"block_index": 5, "start_column_index": 37, "teacher_name": "Daniela (Ciência Aplicada)", "discipline": "Ciência Aplicada"},
        {"block_index": 6, "start_column_index": 44, "teacher_name": "Danielle (Matemática)", "discipline": "Matemática"},
        {"block_index": 7, "start_column_index": 51, "teacher_name": "Emerson (História)", "discipline": "História"},
        {"block_index": 8, "start_column_index": 58, "teacher_name": "Jéssica (Arte - Teatro)", "discipline": "Arte"},
        {"block_index": 9, "start_column_index": 65, "teacher_name": "Kaique (Geografia)", "discipline": "Geografia"},
        {"block_index": 10, "start_column_index": 72, "teacher_name": "Luana (Ciências - Biologia/Química)", "discipline": "Ciências"},
        {"block_index": 11, "start_column_index": 79, "teacher_name": "Márcia (Arte - Visual)", "discipline": "Arte"},
        {"block_index": 12, "start_column_index": 86, "teacher_name": "Monique (Lab. Inteligência Emocional)", "discipline": "Laboratório"},
        {"block_index": 13, "start_column_index": 93, "teacher_name": "Pavani (Atualidades)", "discipline": "Atualidades"},
        {"block_index": 14, "start_column_index": 100, "teacher_name": "Pavarina (Ed. Física)", "discipline": "Ed. Física"},
        {"block_index": 15, "start_column_index": 107, "teacher_name": "Valeska (Inglês)", "discipline": "Inglês"},
        {"block_index": 16, "start_column_index": 114, "teacher_name": "Vitor (Física)", "discipline": "Física"},
        {"block_index": 17, "start_column_index": 121, "teacher_name": "Zé Eduardo (Matemática)", "discipline": "Matemática"}
    ]
}

# Dicionário robusto com keywords de mapeamento de atributos (inclusive para Ed. Física)
KEYWORDS_ATTRIBUTES = {
    "Didática": ["não entender", "nao entende", "explica de outro jeito", "explica de um jeito diferente", "outros exemplos", "regras dos jogos"],
    "Apoio": ["aberto e disponível", "tirar as dúvidas", "tirar as duvidas", "paciente e nos deixa", "confortáveis para tirar", "suporte", "aberto e disponivel", "garante que todos participem"],
    "Tempo": ["tempo total", "forma produtiva", "iniciando e finalizando", "ociosa", "planejamento", "tempo", "tempo de quadra", "ociosidade/espera"],
    "Avaliação": ["alinhadas com", "nível de exigência", "exigencia das provas", "provas e trabalhos", "avaliação", "avaliativa", "nivel de exigencia", "critérios de nota", "uniforme, esforço", "uniforme"],
    "Clima": ["manter o ambiente", "organizado e focado", "conversas paralelas", "atrapalhem", "organizada e focada", "clima", "ambiente de sala", "desentendimentos no jogo", "intervém de forma justa"],
    "Respeito": ["respeito e educação", "expor ninguém", "trata todos os alunos", "comportamentos dos alunos", "mediação", "respectivo", "respeito e educacao", "expor ninguem", "respeito mútuo", "proíbe piadas"],
    "Domínio": ["domínio do conteúdo", "dominio", "estimulam a participação", "participação ativa", "aula interessante", "estimulem", "engajamento", "participacao ativa", "disponível para ouvir as dúvidas"]
}

def identify_attribute(col_name):
    col_lower = col_name.lower()
    for attr, keywords in KEYWORDS_ATTRIBUTES.items():
        for kw in keywords:
            if kw in col_lower:
                return attr
    return None

def clean_likert(val):
    if pd.isna(val) or not isinstance(val, str):
        return None
    val_clean = val.strip().lower()
    if val_clean == "sempre":
        return 4
    elif val_clean == "quase sempre":
        return 3
    elif val_clean in ["poucas vezes", "poucas vezez", "poucas vezes.", "poucas vezez."]:
        return 2
    elif val_clean == "nunca":
        return 1
    return None

def clean_turma_6ano(name):
    if not isinstance(name, str):
        return "6ºA"
    name_clean = name.strip().upper()
    name_no_words = name_clean.replace("ANO", "").replace("SÉRIE", "").replace("SERIE", "").replace("SÉRIES", "").replace("SERIES", "")
    
    if 'A' in name_no_words:
        return "6ºA"
    elif 'B' in name_no_words:
        return "6ºB"
    elif 'C' in name_no_words:
        return "6ºC"
    elif 'D' in name_no_words:
        return "6ºD"
    return "6ºA"

def init_sqlite_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Tabela de Mapeamento (forçar recriação com a coluna turmas)
    cursor.execute("DROP TABLE IF EXISTS mapeamento")
    cursor.execute("""
    CREATE TABLE mapeamento (
        turma_pasta TEXT,
        block_index INTEGER,
        start_column_index INTEGER,
        teacher_name TEXT,
        discipline TEXT,
        turmas TEXT,
        PRIMARY KEY (turma_pasta, block_index)
    )
    """)
    
    # Se a tabela mapeamento estiver vazia, popular com MAPPING_ESTATICO
    cursor.execute("SELECT COUNT(*) FROM mapeamento")
    if cursor.fetchone()[0] == 0:
        print("[SQLITE] Populando tabela mapeamento com MAPPING_ESTATICO inicial...")
        for turma_name, blocks in MAPPING_ESTATICO.items():
            for b in blocks:
                cursor.execute("""
                INSERT INTO mapeamento (turma_pasta, block_index, start_column_index, teacher_name, discipline, turmas)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (turma_name, b["block_index"], b["start_column_index"], b["teacher_name"], b["discipline"], "[]"))
        conn.commit()

    # 2. Tabela de Professores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )
    """)
    
    # 3. Tabela de Respostas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id TEXT PRIMARY KEY,
        turma_pasta TEXT,
        turma_declarada TEXT,
        segmento TEXT,
        professor TEXT,
        disciplina TEXT,
        timestamp TEXT,
        comentario TEXT,
        didatica REAL,
        apoio REAL,
        tempo REAL,
        avaliacao REAL,
        clima REAL,
        respeito REAL,
        dominio REAL
    )
    """)
    
    conn.commit()
    conn.close()

def run_processing():
    all_responses = []
    teachers_global = set()
    classes_global = set()

    print("=== INICIANDO O PROCESSAMENTO DOS DADOS (MAPEAMENTO ESTATÍSTICO) ===")
    
    # Garantir a criação das tabelas no SQLite
    init_sqlite_db()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tenta carregar o mapeamento do arquivo mapeamento_professores.json
    current_mapping = {}
    if os.path.exists(workspace_mapping_path):
        try:
            with open(workspace_mapping_path, "r", encoding="utf-8") as f:
                current_mapping = json.load(f)
            # Sincronizar dados do JSON para o banco SQLite
            for turma_name, blocks in current_mapping.items():
                for b in blocks:
                    turmas_str = json.dumps(b.get("turmas", []))
                    cursor.execute("""
                    INSERT OR REPLACE INTO mapeamento (turma_pasta, block_index, start_column_index, teacher_name, discipline, turmas)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (turma_name, b["block_index"], b["start_column_index"], b["teacher_name"], b["discipline"], turmas_str))
            conn.commit()
            print("[INFO] Mapeamento do JSON sincronizado com o SQLite com sucesso.")
        except Exception as e:
            print(f"[AVISO] Erro ao sincronizar JSON com SQLite: {e}. Carregando mapeamento do SQLite.")
    
    # Garantir que o SQLite contenha todas as chaves padrão do MAPPING_ESTATICO
    for turma_name, blocks in MAPPING_ESTATICO.items():
        for b in blocks:
            cursor.execute("""
            INSERT OR IGNORE INTO mapeamento (turma_pasta, block_index, start_column_index, teacher_name, discipline, turmas)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (turma_name, b["block_index"], b["start_column_index"], b["teacher_name"], b["discipline"], "[]"))
    conn.commit()

    # Carregar mapeamentos unificados do SQLite para a memória
    current_mapping = {}
    cursor.execute("SELECT turma_pasta, block_index, start_column_index, teacher_name, discipline, turmas FROM mapeamento")
    for row in cursor.fetchall():
        t_name, b_idx, start_col, teacher, disc, turmas_str = row
        try:
            turmas = json.loads(turmas_str) if turmas_str else []
        except Exception:
            turmas = []
        if t_name not in current_mapping:
            current_mapping[t_name] = []
        current_mapping[t_name].append({
            "block_index": b_idx,
            "start_column_index": start_col,
            "teacher_name": teacher,
            "discipline": disc,
            "turmas": turmas
        })

    for turma_name in sorted(os.listdir(workspace)):
        dir_path = os.path.join(workspace, turma_name)
        if not os.path.isdir(dir_path):
            continue
            
        csv_file = None
        xlsx_file = None
        for f in os.listdir(dir_path):
            if f.lower().endswith('.csv'):
                csv_file = f
                break
            elif f.lower().endswith('.xlsx') and not f.startswith('~$'):
                xlsx_file = f
                
        if not csv_file and not xlsx_file:
            continue
            
        # 1. Carregar mapeamento estático da turma
        turma_mapping = current_mapping.get(turma_name, [])
        if not turma_mapping:
            print(f"  [AVISO] Mapeamento não encontrado para a turma {turma_name}. Pulando...")
            continue
            
        print(f"  Mapeando {len(turma_mapping)} blocos de professores configurados.")
        
        # Limpar respostas antigas da turma no SQLite para evitar duplicidade
        cursor.execute("DELETE FROM respostas WHERE turma_pasta = ?", (turma_name,))
        
        segmento = "Ensino Médio"
        if "ano" in turma_name.lower():
            segmento = "Ensino Fundamental II"
            
        if csv_file:
            csv_path = os.path.join(dir_path, csv_file)
            print(f"\nProcessando CSV de {turma_name}: {csv_file}")
            
            df = pd.read_csv(csv_path)
            cols = list(df.columns)
            
            for index, row in df.iterrows():
                row_turma = row.get("Turma", None)
                if pd.isna(row_turma) or not str(row_turma).strip():
                    row_turma = turma_name
                else:
                    row_turma = str(row_turma).strip()
                    
                classes_global.add(row_turma)
                
                timestamp = row.get("Carimbo de data/hora", None)
                if pd.isna(timestamp):
                    timestamp = ""
                    
                comment_col = [c for c in cols if "sugestão" in c.lower() or "sugestao" in c.lower() or "comentários" in c.lower()]
                aluno_comment = None
                if comment_col:
                    aluno_comment = row.get(comment_col[0], None)
                    if pd.isna(aluno_comment) or not str(aluno_comment).strip():
                        aluno_comment = None
                    else:
                        aluno_comment = str(aluno_comment).strip()
                        
                for item in turma_mapping:
                    allowed_turmas = item.get("turmas", [])
                    if allowed_turmas and row_turma not in allowed_turmas:
                        continue
                        
                    b_idx = item["block_index"]
                    start_col = item["start_column_index"]
                    teacher = item["teacher_name"]
                    discipline = item["discipline"]
                    
                    teachers_global.add(teacher)
                    
                    ratings = {}
                    has_data = False
                    
                    for offset in range(7):
                        if start_col + offset < len(cols):
                            col_name = cols[start_col + offset]
                            attr = identify_attribute(col_name)
                            if attr:
                                val = row[col_name]
                                val_num = clean_likert(val)
                                if val_num is not None:
                                    ratings[attr] = val_num
                                    has_data = True
                                    
                    if has_data:
                        didatica = ratings.get("Didática", None)
                        apoio = ratings.get("Apoio", None)
                        tempo = ratings.get("Tempo", None)
                        avaliacao = ratings.get("Avaliação", None)
                        clima = ratings.get("Clima", None)
                        respeito = ratings.get("Respeito", None)
                        dominio = ratings.get("Domínio", None)
                        
                        resp_id = f"{turma_name.replace(' ', '_')}_{index}_{b_idx}"
                        
                        cursor.execute("""
                        INSERT OR REPLACE INTO respostas (
                            id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
                            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            resp_id, turma_name, row_turma, segmento, teacher, discipline, timestamp, aluno_comment,
                            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                        ))
                        
                        response_record = {
                            "id": resp_id,
                            "turma_pasta": turma_name,
                            "turma_declarada": row_turma,
                            "segmento": segmento,
                            "professor": teacher,
                            "disciplina": discipline,
                            "timestamp": timestamp,
                            "ratings": ratings,
                            "comentario": aluno_comment
                        }
                        all_responses.append(response_record)
                        
        elif xlsx_file:
            xlsx_path = os.path.join(dir_path, xlsx_file)
            print(f"\nProcessando EXCEL de {turma_name}: {xlsx_file}")
            
            xl = pd.ExcelFile(xlsx_path)
            sheet_name = None
            for s in xl.sheet_names:
                if '6' in s:
                    sheet_name = s
                    break
            if not sheet_name:
                sheet_name = xl.sheet_names[0]
                
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            
            # Primeira linha (índice 0) são as chaves/números das perguntas. As respostas de fato começam em df.iloc[1:]
            for index in range(1, len(df)):
                row = df.iloc[index]
                row_turma_raw = row.iloc[0]
                if pd.isna(row_turma_raw) or not str(row_turma_raw).strip():
                    row_turma = turma_name
                else:
                    row_turma = clean_turma_6ano(row_turma_raw)
                    
                classes_global.add(row_turma)
                
                for item in turma_mapping:
                    allowed_turmas = item.get("turmas", [])
                    if allowed_turmas and row_turma not in allowed_turmas:
                        continue
                        
                    b_idx = item["block_index"]
                    start_col = item["start_column_index"]
                    teacher = item["teacher_name"]
                    discipline = item["discipline"]
                    
                    teachers_global.add(teacher)
                    
                    ratings = {}
                    has_data = False
                    
                    # Ordem física fixa de atributos do 6º ano no Excel:
                    # Didática, Apoio, Tempo, Avaliação, Clima, Respeito, Domínio
                    atributos_ordem = ["Didática", "Apoio", "Tempo", "Avaliação", "Clima", "Respeito", "Domínio"]
                    for offset in range(7):
                        col_idx = start_col + offset
                        if col_idx < len(row):
                            val = row.iloc[col_idx]
                            if not pd.isna(val):
                                try:
                                    val_num = float(val)
                                    if 1.0 <= val_num <= 4.0:
                                        ratings[atributos_ordem[offset]] = val_num
                                        has_data = True
                                except ValueError:
                                    pass
                                    
                    if has_data:
                        didatica = ratings.get("Didática", None)
                        apoio = ratings.get("Apoio", None)
                        tempo = ratings.get("Tempo", None)
                        avaliacao = ratings.get("Avaliação", None)
                        clima = ratings.get("Clima", None)
                        respeito = ratings.get("Respeito", None)
                        dominio = ratings.get("Domínio", None)
                        
                        resp_id = f"{turma_name.replace(' ', '_')}_{index}_{b_idx}"
                        
                        cursor.execute("""
                        INSERT OR REPLACE INTO respostas (
                            id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
                            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            resp_id, turma_name, row_turma, segmento, teacher, discipline, "", "",
                            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                        ))
                        
                        response_record = {
                            "id": resp_id,
                            "turma_pasta": turma_name,
                            "turma_declarada": row_turma,
                            "segmento": segmento,
                            "professor": teacher,
                            "disciplina": discipline,
                            "timestamp": "",
                            "ratings": ratings,
                            "comentario": None
                        }
                        all_responses.append(response_record)
                    
    # Sincronizar lista de professores na tabela de professores do SQLite
    cursor.execute("DELETE FROM professores")
    cursor.execute("INSERT INTO professores (nome) SELECT DISTINCT professor FROM respostas")
    conn.commit()
    
    # Obter lista consolidada de professores ordenados do SQLite
    cursor.execute("SELECT nome FROM professores ORDER BY nome")
    teachers_list = [r[0] for r in cursor.fetchall()]

    # Salvar mapeamento de professores consolidado de volta no arquivo JSON
    with open(workspace_mapping_path, "w", encoding="utf-8") as f:
        json.dump(current_mapping, f, indent=4, ensure_ascii=False)
    print(f"\nMapeamento de professores consolidado salvo em: {workspace_mapping_path}")

    # Salvar data.json consolidado (para manter compatibilidade imediata com o frontend)
    db_data = {
        "segmentos": ["Ensino Fundamental II", "Ensino Médio"],
        "turmas": sorted(list(classes_global)),
        "professores": teachers_list,
        "atributos": [
            "Didática",
            "Apoio",
            "Tempo",
            "Avaliação",
            "Clima",
            "Respeito",
            "Domínio"
        ],
        "respostas": all_responses
    }

    output_db_path = os.path.join(workspace, "data.json")
    with open(output_db_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)
        
    print(f"Banco de dados SQLite (pesquisa.db) atualizado com sucesso!")
    print(f"Banco de dados unificado JSON exportado para {output_db_path}")
    print(f"Total de registros de avaliações processados: {len(all_responses)}")
    
    conn.close()

if __name__ == '__main__':
    run_processing()
