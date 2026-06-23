import os
import sys
import sqlite3
import pandas as pd
import json
from dotenv import load_dotenv
import urllib.request
import urllib.error
import re

# Forçar console UTF-8 para evitar caracteres quebrados em Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar arquivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

IS_SUPABASE_CONFIGURED = (
    SUPABASE_URL and 
    "seu-projeto" not in SUPABASE_URL and 
    SUPABASE_KEY and 
    "sua-chave" not in SUPABASE_KEY
)

workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"
excel_path = os.path.join(workspace, "Pesquisa - 2026.xlsx")
db_path = os.path.join(workspace, "pesquisa.db")
output_db_path = os.path.join(workspace, "data.json")
workspace_mapping_path = os.path.join(workspace, "mapeamento_professores.json")

SHEET_FOLDER_MAP = {
    "6": ("6º anos", "Ensino Fundamental II"),
    "7": ("7º anos", "Ensino Fundamental II"),
    "8": ("8º anos", "Ensino Fundamental II"),
    "9": ("9º anos", "Ensino Fundamental II"),
    "1": ("1ª séries", "Ensino Médio"),
    "2": ("2ª séries", "Ensino Médio"),
    "3": ("3ª série", "Ensino Médio")
}

def clean_turma(name, sheet_name):
    if not isinstance(name, str) or pd.isna(name):
        return "A"  # fallback
    
    name_upper = name.strip().upper()
    letra = None
    
    # Usar regex para encontrar a letra isolada da turma (A, B, C, D)
    match = re.search(r'\b([A-D])\b', name_upper)
    if match:
        letra = match.group(1)
        
    if not letra:
        letra = 'A'
        
    # Retornar o formato adequado dependendo da série
    for digit, (folder, segment) in SHEET_FOLDER_MAP.items():
        if digit in sheet_name:
            if segment == "Ensino Fundamental II":
                return f"{digit}º{letra}"
            else:
                return f"{digit}ª{letra}"
                
    return name.strip()

def clean_rating(val):
    if pd.isna(val):
        return None
    
    # Suportar tipos de dados numéricos (incluindo numpy.int64/float64) de forma robusta
    try:
        val_float = float(val)
        if 1.0 <= val_float <= 4.0:
            return val_float
    except (ValueError, TypeError):
        pass
        
    if isinstance(val, str):
        val_clean = val.strip().lower()
        if val_clean == "sempre":
            return 4.0
        elif val_clean == "quase sempre":
            return 3.0
        elif val_clean in ["poucas vezes", "poucas vezez", "poucas vezes.", "poucas vezez."]:
            return 2.0
        elif val_clean == "nunca":
            return 1.0
            
    return None

def format_teacher_display_name(col_name):
    parts = col_name.split(' - ')
    if len(parts) > 1:
        # Remover sufixos como BNCC, Itinerário, etc. para limpar a exibição
        disc = parts[1].strip()
        disc_clean = disc.replace(" BNCC", "").replace(" Itinerário", "").replace(" Itinerario", "")
        return f"{parts[0].strip()} ({disc_clean})", disc_clean
    return col_name.strip(), "Geral"

def main():
    print(f"=== INICIANDO IMPORTAÇÃO DO ARQUIVO: Pesquisa - 2026.xlsx ===")
    
    if not os.path.exists(excel_path):
        print(f"Erro: Arquivo {excel_path} não encontrado!")
        sys.exit(1)
        
    # Configurar funções REST auxiliares para o Supabase usando urllib nativo
    def make_supabase_request(url, method, data=None):
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        req_data = None
        if data is not None:
            req_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as res:
                body = res.read().decode('utf-8')
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {err_body}")

    # Inicializar e limpar Supabase remoto
    supabase_active = False
    if IS_SUPABASE_CONFIGURED:
        print("[SUPABASE] Supabase configurado! Inicializando conexão remota via REST API...")
        try:
            clean_url = SUPABASE_URL.rstrip('/')
            # Apagar respostas antigas
            print("[SUPABASE] Removendo dados antigos de 'respostas'...")
            make_supabase_request(f"{clean_url}/rest/v1/respostas?id=neq.dummy", "DELETE")
            # Apagar mapeamentos antigos
            print("[SUPABASE] Removendo dados antigos de 'mapeamento'...")
            make_supabase_request(f"{clean_url}/rest/v1/mapeamento?turma_pasta=neq.dummy", "DELETE")
            print("[SUPABASE] Dados antigos removidos das tabelas remotas com sucesso.")
            supabase_active = True
        except Exception as e:
            print(f"[SUPABASE] Erro ao conectar ou limpar Supabase: {e}. Executando apenas importação local.")
            supabase_active = False
    else:
        print("[INFO] Supabase não configurado no .env. Executando apenas importação local.")

    # 1. Excluir o banco de dados anterior
    if os.path.exists(db_path):
        print(f"Removendo banco de dados SQLite anterior em: {db_path}")
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Erro ao remover banco de dados: {e}. Certifique-se de que nenhum processo o está bloqueando.")
            sys.exit(1)
            
    # 2. Criar novo banco e tabelas locais
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE respostas (
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
    
    cursor.execute("""
    CREATE TABLE professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )
    """)
    
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
    conn.commit()
    
    xl = pd.ExcelFile(excel_path)
    
    all_responses = []
    supabase_responses_batch = []
    classes_global = set()
    teachers_global = set()
    mapping_dict = {}
    
    # 3. Processar cada aba válida do Excel
    for sheet_name in xl.sheet_names:
        if sheet_name == "Valores Gerais":
            continue
            
        # Detectar a série
        digit = None
        for d in SHEET_FOLDER_MAP.keys():
            if d in sheet_name:
                digit = d
                break
                
        if not digit:
            print(f"Aba '{sheet_name}' ignorada (não corresponde a nenhuma série conhecida).")
            continue
            
        folder_name, segmento = SHEET_FOLDER_MAP[digit]
        print(f"\nProcessando aba '{sheet_name}' -> Pasta: '{folder_name}' | Segmento: '{segmento}'")
        
        df = pd.read_excel(xl, sheet_name=sheet_name)
        print(f"  Lidas {len(df)} linhas e {len(df.columns)} colunas.")
        
        # Identificar blocos de professores
        teacher_blocks = []
        cols = list(df.columns)
        
        for i, col in enumerate(cols):
            if i > 0 and not col.startswith("Unnamed:"):
                prof_display, discipline = format_teacher_display_name(col)
                teacher_blocks.append({
                    "block_index": len(teacher_blocks),
                    "start_column_index": i,
                    "teacher_name": prof_display,
                    "discipline": discipline,
                    "turmas": []
                })
                teachers_global.add(prof_display)
                
        print(f"  Detectados {len(teacher_blocks)} blocos de professores na aba.")
        
        # Salvar mapeamento local
        mapping_dict[folder_name] = teacher_blocks
        for b in teacher_blocks:
            cursor.execute("""
            INSERT INTO mapeamento (turma_pasta, block_index, start_column_index, teacher_name, discipline, turmas)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (folder_name, b["block_index"], b["start_column_index"], b["teacher_name"], b["discipline"], "[]"))
            
        # Processar as linhas de respostas dos alunos (começando em row_idx 1)
        response_count = 0
        for row_idx in range(1, len(df)):
            row = df.iloc[row_idx]
            
            raw_turma = row.iloc[0]
            if pd.isna(raw_turma) or str(raw_turma).strip() == "" or str(raw_turma).strip() == "Perguntas":
                continue
                
            turma_declarada = clean_turma(raw_turma, sheet_name)
            classes_global.add(turma_declarada)
            
            # Para cada professor, extrair os 7 votos
            for block in teacher_blocks:
                start_col = block["start_column_index"]
                prof_name = block["teacher_name"]
                discipline = block["discipline"]
                
                votos = []
                has_votes = False
                for offset in range(7):
                    col_idx = start_col + offset
                    val = row.iloc[col_idx] if col_idx < len(row) else None
                    val_cleaned = clean_rating(val)
                    if val_cleaned is not None:
                        has_votes = True
                    votos.append(val_cleaned)
                    
                if has_votes:
                    didatica = votos[0]
                    apoio = votos[1]
                    tempo = votos[2]
                    avaliacao = votos[3]
                    clima = votos[4]
                    respeito = votos[5]
                    dominio = votos[6]
                    
                    # Gerar um ID amigável e único
                    clean_folder = folder_name.replace(' ', '_').replace('º', '').replace('ª', '').replace('é', 'e')
                    resp_id = f"2026_{clean_folder}_{row_idx}_{block['block_index']}"
                    
                    # Inserir local SQLite
                    cursor.execute("""
                    INSERT INTO respostas (
                        id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
                        didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        resp_id, folder_name, turma_declarada, segmento, prof_name, discipline, "", "",
                        didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                    ))
                    
                    # Record local do JSON
                    response_record = {
                        "id": resp_id,
                        "turma_pasta": folder_name,
                        "turma_declarada": turma_declarada,
                        "segmento": segmento,
                        "professor": prof_name,
                        "disciplina": discipline,
                        "timestamp": "",
                        "ratings": {
                            "Didática": didatica,
                            "Apoio": apoio,
                            "Tempo": tempo,
                            "Avaliação": avaliacao,
                            "Clima": clima,
                            "Respeito": respeito,
                            "Domínio": dominio
                        },
                        "comentario": ""
                    }
                    all_responses.append(response_record)
                    
                    # Record do Supabase
                    if supabase_active:
                        supabase_responses_batch.append({
                            "id": resp_id,
                            "turma_pasta": folder_name,
                            "turma_declarada": turma_declarada,
                            "segmento": segmento,
                            "professor": prof_name,
                            "disciplina": discipline,
                            "timestamp": "",
                            "comentario": "",
                            "didatica": didatica,
                            "apoio": apoio,
                            "tempo": tempo,
                            "avaliacao": avaliacao,
                            "clima": clima,
                            "respeito": respeito,
                            "dominio": dominio
                        })
                    
                    response_count += 1
                    
        print(f"  Importadas {response_count} avaliações de professores na aba '{sheet_name}'.")
        
    # 4. Inserir todos os professores únicos no SQLite
    for p in sorted(list(teachers_global)):
        cursor.execute("INSERT OR IGNORE INTO professores (nome) VALUES (?)", (p,))
        
    conn.commit()
    conn.close()
    
    # 5. Enviar respostas em batches para o Supabase
    if supabase_active and supabase_responses_batch:
        print(f"\n[SUPABASE] Enviando {len(supabase_responses_batch)} registros em lotes para o Supabase PostgreSQL...")
        batch_size = 500
        clean_url = SUPABASE_URL.rstrip('/')
        for i in range(0, len(supabase_responses_batch), batch_size):
            batch = supabase_responses_batch[i:i+batch_size]
            try:
                insert_url = f"{clean_url}/rest/v1/respostas"
                make_supabase_request(insert_url, "POST", batch)
                print(f"  - Enviado lote {i // batch_size + 1} ({len(batch)} registros)")
            except Exception as ex:
                print(f"  - [ERRO] Falha ao enviar lote de respostas no Supabase: {ex}")
                
        # Enviar mapeamento para o Supabase
        print("[SUPABASE] Enviando dados de mapeamento administrativo...")
        supabase_mapeamentos = []
        for folder_name, blocks in mapping_dict.items():
            for b in blocks:
                supabase_mapeamentos.append({
                    "turma_pasta": folder_name,
                    "block_index": b["block_index"],
                    "start_column_index": b["start_column_index"],
                    "teacher_name": b["teacher_name"],
                    "discipline": b["discipline"],
                    "turmas": b.get("turmas", [])
                })
        try:
            insert_map_url = f"{clean_url}/rest/v1/mapeamento"
            make_supabase_request(insert_map_url, "POST", supabase_mapeamentos)
            print("[SUPABASE] Mapeamento administrativo enviado com sucesso.")
        except Exception as ex:
            print(f"[SUPABASE] [ERRO] Falha ao enviar mapeamentos: {ex}")

    # 6. Salvar o arquivo data.json consolidado
    db_data = {
        "segmentos": ["Ensino Fundamental II", "Ensino Médio"],
        "turmas": sorted(list(classes_global)),
        "professores": sorted(list(teachers_global)),
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
    
    with open(output_db_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)
        
    # 7. Salvar o arquivo mapeamento_professores.json consolidado
    with open(workspace_mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping_dict, f, indent=4, ensure_ascii=False)
        
    print(f"\n=======================================================")
    print(f" IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f" Banco SQLite (pesquisa.db) recriado e populado.")
    print(f" data.json exportado com {len(all_responses)} avaliações.")
    print(f" mapeamento_professores.json gerado.")
    print(f" Total de professores cadastrados: {len(teachers_global)}")
    print(f" Total de turmas encontradas: {len(classes_global)}")
    if supabase_active:
        print(f" SUPABASE ATUALIZADO: {len(supabase_responses_batch)} registros remotos.")
    print(f"=======================================================\n")

if __name__ == '__main__':
    main()
