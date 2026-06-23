import json
import os
import sys
import urllib.request
import urllib.error

# Definir a pasta atual (raiz do projeto)
workspace = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(workspace, ".env")
creds_path = os.path.join(workspace, "professores_credenciais.json")

# Carregar variáveis do .env manualmente
supabase_url = ""
service_role_key = ""

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.strip().split('=', 1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()
                    if k == 'SUPABASE_URL':
                        supabase_url = v
                    elif k == 'SUPABASE_SERVICE_ROLE_KEY':
                        service_role_key = v

if not supabase_url or not service_role_key:
    print("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não encontradas no arquivo .env")
    sys.exit(1)

# Garantir que a URL não termine com barra
supabase_url = supabase_url.rstrip('/')

print(f"Conectando ao Supabase em: {supabase_url}")

# Helper para fazer requisições HTTP REST
def make_request(url, method, headers, data=None):
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode('utf-8')
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as res:
            body = res.read().decode('utf-8')
            if body:
                return json.loads(body)
            return {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_body)
            err_msg = err_json.get('msg') or err_json.get('message') or err_body
        except:
            err_msg = err_body
        raise Exception(f"HTTP {e.code}: {err_msg}")

# 1. Obter todos os usuários existentes no Supabase Auth para evitar duplicações
auth_headers = {
    "Authorization": f"Bearer {service_role_key}",
    "apikey": service_role_key,
    "Content-Type": "application/json"
}

existing_users = {}
try:
    print("Buscando usuários cadastrados no Supabase Auth...")
    users_url = f"{supabase_url}/auth/v1/admin/users?per_page=200"
    res = make_request(users_url, "GET", auth_headers)
    users_list = res.get('users', [])
    for u in users_list:
        existing_users[u['email'].lower()] = u['id']
    print(f"Total de usuários encontrados no Auth: {len(existing_users)}")
except Exception as e:
    print(f"Aviso ao listar usuários existentes: {e}. Prosseguindo com criação direta.")

# 2. Carregar logins e senhas dos professores
if not os.path.exists(creds_path):
    print(f"Erro: Arquivo {creds_path} não encontrado.")
    sys.exit(1)

with open(creds_path, "r", encoding="utf-8") as f:
    professores_creds = json.load(f)

# Adicionar também a conta do Diretor admin
diretor_email = "diretor@colegiorodin.com.br"
diretor_password = "@Diretor112358*"
diretor_name = "Diretoria"

contas_a_criar = []
# Adicionar diretor
contas_a_criar.append({
    "nome": diretor_name,
    "email": diretor_email,
    "password": diretor_password,
    "nomes_exibicao": [diretor_name],
    "role": "admin"
})

# Adicionar professores
for nome, c in professores_creds.items():
    contas_a_criar.append({
        "nome": nome,
        "email": c["login"],
        "password": c["password"],
        "nomes_exibicao": c.get("nomes_exibicao", [nome]),
        "role": "professor"
    })

print(f"\nIniciando cadastro de {len(contas_a_criar)} contas no Supabase Auth...")

perfis_db = []

for idx, conta in enumerate(contas_a_criar):
    email = conta["email"].lower()
    nome = conta["nome"]
    pwd = conta["password"]
    role = conta["role"]
    nomes_exib = conta["nomes_exibicao"]
    
    user_id = None
    
    # Se o usuário já existe, reaproveita o ID
    if email in existing_users:
        user_id = existing_users[email]
        print(f"[{idx+1}/{len(contas_a_criar)}] Usuário {email} já cadastrado (ID: {user_id})")
    else:
        # Se não existe, cria
        try:
            create_url = f"{supabase_url}/auth/v1/admin/users"
            payload = {
                "email": email,
                "password": pwd,
                "email_confirm": True
            }
            res = make_request(create_url, "POST", auth_headers, payload)
            user_id = res.get('id')
            print(f"[{idx+1}/{len(contas_a_criar)}] Criado com sucesso: {email} (ID: {user_id})")
        except Exception as e:
            print(f"[{idx+1}/{len(contas_a_criar)}] Erro ao criar {email}: {e}")
            continue
            
    if user_id:
        perfis_db.append({
            "id": user_id,
            "email": email,
            "nome_professor": nome,
            "nomes_exibicao": nomes_exib,
            "role": role
        })

# 3. Salvar os perfis na tabela professores_perfis
print("\nSalvando perfis de professores na tabela 'professores_perfis'...")
rest_headers = {
    "Authorization": f"Bearer {service_role_key}",
    "apikey": service_role_key,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

perfis_url = f"{supabase_url}/rest/v1/professores_perfis"
try:
    make_request(perfis_url, "POST", rest_headers, perfis_db)
    print(f"Sucesso! {len(perfis_db)} perfis de professores vinculados e salvos no PostgreSQL do Supabase.")
except Exception as e:
    print(f"Erro ao salvar perfis no banco de dados: {e}")
    sys.exit(1)

print("\nProcesso de sincronização de credenciais concluído com sucesso!")
