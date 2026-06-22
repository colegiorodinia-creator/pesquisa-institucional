import sqlite3
import json
import os

workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"
db_path = os.path.join(workspace, "pesquisa.db")
workspace_mapping_path = os.path.join(workspace, "mapeamento_professores.json")
output_db_path = os.path.join(workspace, "data.json")

def set_alice_data():
    print("=== CONFIGURANDO DADOS TEMPORÁRIOS EXCLUSIVOS DA ALICE (ARTE E DANÇA) ===")
    
    # 1. Limpar e Reinicializar o SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Criar tabelas se não existirem
    cursor.execute("""
    DROP TABLE IF EXISTS respostas
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mapeamento (
        turma_pasta TEXT,
        block_index INTEGER,
        start_column_index INTEGER,
        teacher_name TEXT,
        discipline TEXT,
        PRIMARY KEY (turma_pasta, block_index)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS professores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )
    """)
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
    
    # Limpar dados antigos
    cursor.execute("DELETE FROM mapeamento")
    cursor.execute("DELETE FROM professores")
    cursor.execute("DELETE FROM respostas")
    conn.commit()
    
    # 2. Inserir Mapeamento Único da Alice
    cursor.execute("""
    INSERT INTO mapeamento (turma_pasta, block_index, start_column_index, teacher_name, discipline)
    VALUES (?, ?, ?, ?, ?)
    """, ("6º anos", 0, 2, "Alice (Arte e Dança)", "Arte e Dança"))
    
    # Inserir Professor
    cursor.execute("INSERT INTO professores (nome) VALUES (?)", ("Alice (Arte e Dança)",))
    
    # 3. Inserir Respostas (Médias do Excel)
    alice_rows = [
        {
            "id": "alice_6A",
            "turma_declarada": "6°A",
            "ratings": [3.42, 3.20, 3.33, 3.16, 3.40, 2.65, 3.38],
            "comentario": "Excelente professora de Arte e Dança!"
        },
        {
            "id": "alice_6B",
            "turma_declarada": "6°B",
            "ratings": [3.19, 3.30, 3.33, 3.14, 3.48, 2.43, 3.52],
            "comentario": "Aulas práticas muito produtivas e interessantes."
        },
        {
            "id": "alice_6C",
            "turma_declarada": "6°C",
            "ratings": [3.31, 3.42, 3.69, 3.27, 3.46, 2.58, 3.81],
            "comentario": "Ótima didática e ambiente focado."
        },
        {
            "id": "alice_6D",
            "turma_declarada": "6°D",
            "ratings": [3.22, 3.09, 3.52, 2.96, 3.39, 2.39, 3.65],
            "comentario": "Prestativa e aulas bem organizadas."
        }
    ]
    
    all_responses = []
    
    for r in alice_rows:
        ratings = r["ratings"]
        cursor.execute("""
        INSERT INTO respostas (
            id, turma_pasta, turma_declarada, segmento, professor, disciplina, timestamp, comentario,
            didatica, apoio, tempo, avaliacao, clima, respeito, dominio
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"], "6º anos", r["turma_declarada"], "Ensino Fundamental II", "Alice (Arte e Dança)", "Arte e Dança", 
            "15/06/2026 17:00:00", r["comentario"],
            ratings[0], ratings[1], ratings[2], ratings[3], ratings[4], ratings[5], ratings[6]
        ))
        
        # Estrutura do JSON usando as novas chaves curtas
        response_record = {
            "id": r["id"],
            "turma_pasta": "6º anos",
            "turma_declarada": r["turma_declarada"],
            "segmento": "Ensino Fundamental II",
            "professor": "Alice (Arte e Dança)",
            "disciplina": "Arte e Dança",
            "timestamp": "15/06/2026 17:00:00",
            "ratings": {
                "Didática": ratings[0],
                "Apoio": ratings[1],
                "Tempo": ratings[2],
                "Avaliação": ratings[3],
                "Clima": ratings[4],
                "Respeito": ratings[5],
                "Domínio": ratings[6]
            },
            "comentario": r["comentario"]
        }
        all_responses.append(response_record)
        
    conn.commit()
    conn.close()
    
    # 4. Escrever JSON do Mapeamento
    map_json = {
        "6º anos": [
            {
                "block_index": 0,
                "start_column_index": 2,
                "teacher_name": "Alice (Arte e Dança)",
                "discipline": "Arte e Dança"
            }
        ]
    }
    with open(workspace_mapping_path, "w", encoding="utf-8") as f:
        json.dump(map_json, f, indent=4, ensure_ascii=False)
        
    # 5. Escrever data.json do Dashboard
    db_json = {
        "segmentos": ["Ensino Fundamental II"],
        "turmas": ["6°A", "6°B", "6°C", "6°D"],
        "professores": ["Alice (Arte e Dança)"],
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
        json.dump(db_json, f, indent=4, ensure_ascii=False)
        
    print("\nBanco de dados SQLite (pesquisa.db) reconfigurado com sucesso com atributos unificados!")
    print("Arquivos data.json e mapeamento_professores.json exportados com chaves curtas!")

if __name__ == '__main__':
    set_alice_data()
