import sqlite3
import pandas as pd
import json
import os

workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"
excel_path = os.path.join(workspace, "6º anos", "Pesquisa - 6° Ano.xlsx")
db_path = os.path.join(workspace, "pesquisa.db")
output_db_path = os.path.join(workspace, "data.json")
workspace_mapping_path = os.path.join(workspace, "mapeamento_professores.json")

def clean_turma(name):
    if not isinstance(name, str):
        return "6°A"
    name_clean = name.strip().upper()
    # Remove palavras comuns para evitar falsos positivos (como o 'A' em 'ANO')
    name_no_words = name_clean.replace("ANO", "").replace("SÉRIE", "").replace("SERIE", "").replace("SÉRIES", "").replace("SERIES", "")
    
    if 'A' in name_no_words:
        return "6°A"
    elif 'B' in name_no_words:
        return "6°B"
    elif 'C' in name_no_words:
        return "6°C"
    elif 'D' in name_no_words:
        return "6°D"
    return "6°A"

def format_teacher_name(col_name):
    parts = col_name.split(' - ')
    if len(parts) > 1:
        return f"{parts[0].strip()} ({parts[1].strip()})"
    return col_name.strip()

def load_excel_raw():
    print("=== IMPORTANDO DADOS BRUTOS DO 6º ANO (SEG UMA ABA '6ºAno') ===")
    
    if not os.path.exists(excel_path):
        print(f"Erro: Arquivo Excel não encontrado em: {excel_path}")
        return
        
    xl = pd.ExcelFile(excel_path)
    sheet_name = [s for s in xl.sheet_names if '6' in s][0]
    
    # 1. Ler a aba de dados brutos
    # A linha 0 é o cabeçalho (nomes dos professores nas colunas), e a linha 1 são os números das perguntas
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    print(f"Lidas {len(df)} linhas da aba '{sheet_name}'.")
    
    # O df lido pelo pandas tem o cabeçalho de colunas como linha de cabeçalho padrão
    # O primeiro registro df.iloc[0] são os números de perguntas (1.0, 2.0, 3.0, etc.)
    # O dados dos alunos começam em df.iloc[1:]
    
    # Conectar ao SQLite e reinicializar tabelas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS respostas")
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
    cursor.execute("DELETE FROM mapeamento")
    cursor.execute("DELETE FROM professores")
    conn.commit()
    
    all_responses = []
    classes_set = set()
    teachers_set = set()
    
    # Identificar blocos de colunas de professores
    cols = list(df.columns)
    teacher_blocks = []
    
    for i, col in enumerate(cols):
        if not col.startswith('Unnamed:'):
            if i > 0: # Ignorar a coluna 0 ('Unnamed: 0') que é a turma
                prof_display = format_teacher_name(col)
                discipline = col.split(' - ')[1].strip() if ' - ' in col else "Geral"
                teacher_blocks.append({
                    "teacher_name": prof_display,
                    "discipline": discipline,
                    "start_col": i
                })
                teachers_set.add(prof_display)
                
    print(f"Encontrados {len(teacher_blocks)} blocos de professores para importação.")
    
    # Iterar pelas linhas de dados dos alunos (a partir do índice 1)
    response_count = 0
    for row_idx in range(1, len(df)):
        row = df.iloc[row_idx]
        
        # Coluna 0 é a turma
        raw_turma = row.iloc[0]
        if pd.isna(raw_turma) or str(raw_turma).strip() == "":
            continue
            
        turma_declarada = clean_turma(raw_turma)
        classes_set.add(turma_declarada)
        
        # Para cada professor, extrair os 7 votos
        for block in teacher_blocks:
            start_col = block["start_col"]
            prof_display = block["teacher_name"]
            discipline = block["discipline"]
            
            # Obter os votos individuais
            votos = []
            has_votes = False
            for offset in range(7):
                val = row.iloc[start_col + offset]
                if not pd.isna(val):
                    try:
                        val_float = float(val)
                        # O valor deve ser um voto válido entre 1 e 4
                        if 1.0 <= val_float <= 4.0:
                            votos.append(val_float)
                            has_votes = True
                        else:
                            votos.append(None)
                    except ValueError:
                        votos.append(None)
                else:
                    votos.append(None)
                    
            if has_votes:
                didatica = votos[0]
                apoio = votos[1]
                tempo = votos[2]
                avaliacao = votos[3]
                clima = votos[4]
                respeito = votos[5]
                dominio = votos[6]
                
                resp_id = f"6ano_{row_idx}_{prof_display.replace(' ', '_').replace('(', '').replace(')', '')}"
                
                # Inserir no SQLite
                cursor.execute("""
                INSERT INTO respostas (
                    id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
                    didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    resp_id, "6º anos", turma_declarada, "Ensino Fundamental II", prof_display, discipline, "", "",
                    didatica, apoio, tempo, avaliacao, clima, respeito, dominio
                ))
                
                # Record para o JSON
                response_record = {
                    "id": resp_id,
                    "turma_pasta": "6º anos",
                    "turma_declarada": turma_declarada,
                    "segmento": "Ensino Fundamental II",
                    "professor": prof_display,
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
                response_count += 1
                
    # Inserir na tabela de professores
    for p in sorted(list(teachers_set)):
        cursor.execute("INSERT INTO professores (nome) VALUES (?)", (p,))
        
    conn.commit()
    conn.close()
    
    # 4. Gravar data.json consolidado
    db_data = {
        "segmentos": ["Ensino Fundamental II"],
        "turmas": sorted(list(classes_set)),
        "professores": sorted(list(teachers_set)),
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
        
    # 5. Gravar mapeamento_professores.json admin
    mapping_data = {
        "6º anos": []
    }
    for idx, block in enumerate(teacher_blocks):
        mapping_data["6º anos"].append({
            "block_index": idx,
            "start_column_index": block["start_col"],
            "teacher_name": block["teacher_name"],
            "discipline": block["discipline"]
        })
        
    with open(workspace_mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nImportação de respostas brutas concluída com sucesso!")
    print(f"Total de registros de avaliações processados: {response_count}")
    print(f"Banco de dados SQLite (pesquisa.db) atualizado.")
    print(f"data.json gerado.")
    print(f"mapeamento_professores.json atualizado.")

if __name__ == '__main__':
    load_excel_raw()
