import sqlite3
import pandas as pd
import json
import os

workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"
excel_path = os.path.join(workspace, "6º anos", "Pesquisa - 6° Ano.xlsx")
db_path = os.path.join(workspace, "pesquisa.db")
output_db_path = os.path.join(workspace, "data.json")
workspace_mapping_path = os.path.join(workspace, "mapeamento_professores.json")

def load_excel():
    print("=== IMPORTANDO DADOS OFICIAIS DO 6º ANO A PARTIR DO EXCEL ===")
    
    if not os.path.exists(excel_path):
        print(f"Erro: Arquivo Excel não encontrado em: {excel_path}")
        return
        
    # 1. Ler Excel consolidado
    df = pd.read_excel(excel_path)
    print(f"Lidas {len(df)} linhas do Excel.")
    
    # 2. Conectar ao SQLite e limpar dados anteriores para substituição completa
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
    
    # 3. Inserir dados do Excel no SQLite
    all_responses = []
    classes_set = set()
    teachers_set = set()
    
    for idx, row in df.iterrows():
        # Tratar nulos ou vazios
        if pd.isna(row['Nome']) or str(row['Nome']).strip() == "":
            continue
            
        segmento = str(row['Segmento']).strip()
        # Mapear "Ensino Fundamental" para "Ensino Fundamental II" para manter compatibilidade com filtros
        if segmento == "Ensino Fundamental":
            segmento = "Ensino Fundamental II"
            
        turma = str(row['Turma']).strip()
        classes_set.add(turma)
        
        prof_name = str(row['Nome']).strip()
        # Adicionar a disciplina ao nome do professor para ficar amigável e único
        discipline = str(row['Disciplina']).strip()
        prof_display_name = f"{prof_name} ({discipline})"
        teachers_set.add(prof_display_name)
        
        # Obter notas
        didatica = float(row['Didática']) if not pd.isna(row['Didática']) else None
        apoio = float(row['Apoio']) if not pd.isna(row['Apoio']) else None
        tempo = float(row['Tempo']) if not pd.isna(row['Tempo']) else None
        avaliacao = float(row['Avaliação']) if not pd.isna(row['Avaliação']) else None
        clima = float(row['Clima']) if not pd.isna(row['Clima']) else None
        respeito = float(row['Respeito']) if not pd.isna(row['Respeito']) else None
        dominio = float(row['Domínio']) if not pd.isna(row['Domínio']) else None
        
        resp_id = f"6ano_{idx}_{prof_name.replace(' ', '_')}"
        
        cursor.execute("""
        INSERT INTO respostas (
            id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resp_id, "6º anos", turma, segmento, prof_display_name, discipline, "", "",
            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
        ))
        
        # Adicionar na lista do data.json
        response_record = {
            "id": resp_id,
            "turma_pasta": "6º anos",
            "turma_declarada": turma,
            "segmento": segmento,
            "professor": prof_display_name,
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
        
    # 5. Gravar mapeamento_professores.json vazio para o 6° ano
    mapping_data = {
        "6º anos": []
    }
    # Gerar mapeamento inicial fake baseado no Excel para que o usuário possa ver as disciplinas na tela administrativa se quiser
    for idx, row in df.iterrows():
        prof_name = str(row['Nome']).strip()
        discipline = str(row['Disciplina']).strip()
        prof_display_name = f"{prof_name} ({discipline})"
        
        # Evitar duplicados no mapeamento do JSON
        exists = any(item["teacher_name"] == prof_display_name for item in mapping_data["6º anos"])
        if not exists:
            mapping_data["6º anos"].append({
                "block_index": len(mapping_data["6º anos"]),
                "start_column_index": 2 + len(mapping_data["6º anos"]) * 7,
                "teacher_name": prof_display_name,
                "discipline": discipline
            })
            
    with open(workspace_mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f, indent=4, ensure_ascii=False)
        
    print(f"\nImportação concluída com sucesso!")
    print(f"Banco de dados SQLite (pesquisa.db) atualizado.")
    print(f"Arquivo data.json gerado com {len(all_responses)} registros de avaliações de professores.")
    print(f"Mapeamento administrativo inicial gerado em mapeamento_professores.json.")

if __name__ == '__main__':
    load_excel()
