import http.server
import socketserver
import os
import json
import urllib.parse
import webbrowser
import sys

# Forçar UTF-8 no console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8000
workspace = r"c:\Users\MARKETING 03\Documents\Antigravity\Pesquisa Institucional"

# Importar a função de processamento de dados do process_data.py
sys.path.append(workspace)
try:
    from process_data import run_processing
except ImportError:
    def run_processing():
        print("Erro: Não foi possível importar run_processing de process_data.py")

class RodinDashboardHandler(http.server.SimpleHTTPRequestHandler):
    # Garantir que o Windows sirva os tipos MIME corretos (principalmente text/css)
    extensions_map = http.server.SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        '.css': 'text/css',
        '.js': 'text/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.svg': 'image/svg+xml',
        '.otf': 'font/otf',
        '.ttf': 'font/ttf',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '': 'application/octet-stream',
    })

    def get_session_info(self):
        cookie_header = self.headers.get('Cookie', '')
        if 'session=' not in cookie_header:
            return None
        try:
            parts = cookie_header.split('session=')
            if len(parts) > 1:
                session_val = parts[1].split(';')[0].strip()
                session_val_decoded = urllib.parse.unquote(session_val)
                info = {}
                for item in session_val_decoded.split('|'):
                    if ':' in item:
                        k, v = item.split(':', 1)
                        info[k] = v
                return info
        except Exception as e:
            print(f"[SERVER] Erro ao parsear cookie de sessão: {e}")
        return None

    def is_authorized(self):
        info = self.get_session_info()
        return info is not None

    def end_headers(self):
        # Desabilitar cache para que novos dados sempre carreguem instantaneamente
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path_clean = parsed_url.path
        
        if path_clean == '/api/config':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            url = os.environ.get('SUPABASE_URL', '')
            key = os.environ.get('SUPABASE_ANON_KEY', '')
            service_role_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
            
            if not url or not key or not service_role_key:
                try:
                    env_path = os.path.join(workspace, ".env")
                    if os.path.exists(env_path):
                        with open(env_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip() and not line.startswith('#'):
                                    parts = line.strip().split('=', 1)
                                    if len(parts) == 2:
                                        k_val = parts[0].strip()
                                        v_val = parts[1].strip()
                                        if k_val == 'SUPABASE_URL':
                                            url = v_val
                                        elif k_val == 'SUPABASE_ANON_KEY':
                                            key = v_val
                                        elif k_val == 'SUPABASE_SERVICE_ROLE_KEY':
                                            service_role_key = v_val
                except Exception as e:
                    print(f"[SERVER] Erro ao ler .env manualmente: {e}")
            
            response = {
                "SUPABASE_URL": url,
                "SUPABASE_ANON_KEY": key,
                "SUPABASE_SERVICE_ROLE_KEY": service_role_key
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return

        if path_clean == '/api/session':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            session_info = self.get_session_info()
            if session_info:
                self.wfile.write(json.dumps(session_info).encode('utf-8'))
            else:
                self.wfile.write(b"{}")
            return

        # Allowlist de arquivos que podem ser servidos pelo Handler (CWE-306)
        allowed_paths = [
            '/', '/index.html', '/app.js', '/style.css', '/colors_and_type.css',
            '/data.json', '/mapeamento_professores.json', '/favicon.png', '/favicon.ico',
            '/migracao.html'
        ]
        
        # Permitir arquivos de fontes locais da pasta fonts
        is_font = path_clean.startswith('/fonts/') and (
            path_clean.lower().endswith('.otf') or 
            path_clean.lower().endswith('.ttf') or 
            path_clean.lower().endswith('.ttc')
        )
        
        # Rotas especiais que contornam a allowlist de arquivos estáticos
        if path_clean in ['/api/config', '/api/session', '/api/migration-data']:
            pass
        elif path_clean not in allowed_paths and not is_font:
            self.send_error(403, "Acesso Proibido: Arquivo nao autorizado para leitura externa.")
            return
            
        # Proteger acesso a arquivos de dados sensíveis (CWE-306)
        if path_clean in ['/data.json', '/mapeamento_professores.json']:
            session_info = self.get_session_info()
            if not session_info:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "unauthorized", "message": "Acesso não autorizado. Faça login para visualizar os dados."}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            
            # Regras baseadas em papéis (RBAC) para professores
            if session_info.get("role") == "professor":
                # Professor NÃO pode ler o mapeamento
                if path_clean == '/mapeamento_professores.json':
                    self.send_error(403, "Acesso Proibido: Professores nao possuem acesso ao mapeamento de turmas.")
                    return
                
                # Professor pode ler o data.json, mas ele é FILTRADO em tempo real no backend
                if path_clean == '/data.json':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    
                    data_path = os.path.join(workspace, "data.json")
                    try:
                        with open(data_path, "r", encoding="utf-8") as f:
                            full_data = json.load(f)
                            
                        prof_name = session_info.get("nome_professor") or session_info.get("name")
                        
                        # Buscar disciplinas (nomes de exibição) do professor logado nas credenciais
                        creds_path = os.path.join(workspace, "professores_credenciais.json")
                        nomes_exibicao = [prof_name]
                        if os.path.exists(creds_path):
                            try:
                                with open(creds_path, "r", encoding="utf-8") as f:
                                    creds = json.load(f)
                                if prof_name in creds:
                                    nomes_exibicao = creds[prof_name].get("nomes_exibicao", [prof_name])
                            except Exception as e:
                                print(f"[SERVER] Erro ao carregar credenciais para filtro: {e}")
                        
                        # Manter apenas respostas do próprio professor logado
                        filtered_respostas = [r for r in full_data.get("respostas", []) if r.get("professor") in nomes_exibicao]
                        
                        filtered_data = {
                            "segmentos": full_data.get("segmentos", []),
                            "turmas": sorted(list(set(r.get("turma_declarada") for r in filtered_respostas))),
                            "professores": nomes_exibicao,
                            "atributos": full_data.get("atributos", []),
                            "respostas": filtered_respostas
                        }
                        self.wfile.write(json.dumps(filtered_data, ensure_ascii=False).encode('utf-8'))
                    except Exception as e:
                        print(f"[SERVER] Erro ao filtrar data.json localmente: {e}")
                        self.wfile.write(b"{}")
                    return

        # Rota de dados de migração local (bypassa autenticação apenas localmente)
        if path_clean == '/api/migration-data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            try:
                data_path = os.path.join(workspace, "data.json")
                map_path = os.path.join(workspace, "mapeamento_professores.json")
                creds_path = os.path.join(workspace, "professores_credenciais.json")
                
                data_content = {}
                if os.path.exists(data_path):
                    with open(data_path, "r", encoding="utf-8") as f:
                        data_content = json.load(f)
                        
                map_content = {}
                if os.path.exists(map_path):
                    with open(map_path, "r", encoding="utf-8") as f:
                        map_content = json.load(f)
                        
                creds_content = {}
                if os.path.exists(creds_path):
                    with open(creds_path, "r", encoding="utf-8") as f:
                        creds_content = json.load(f)
                        
                response = {
                    "data": data_content,
                    "mapping": map_content,
                    "credentials": creds_content
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                print(f"[SERVER] Erro ao carregar dados de migração: {e}")
                self.wfile.write(b"{}")
            return

        super().do_GET()

    def do_POST(self):
        if self.path == '/api/login':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                credentials = json.loads(post_data.decode('utf-8'))
                
                username = credentials.get('username')
                password = credentials.get('password')
                
                # 1. Tentar login como Diretor
                if username == 'Diretor' and password == '@Diretor112358*':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    cookie_val = urllib.parse.quote("role:admin")
                    self.send_header('Set-Cookie', f'session={cookie_val}; Path=/; HttpOnly; SameSite=Strict')
                    self.end_headers()
                    response = {"status": "success", "role": "admin", "message": "Autenticado com sucesso como Diretor!"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # 2. Tentar login como Professor usando professores_credenciais.json
                creds_path = os.path.join(workspace, "professores_credenciais.json")
                prof_creds = {}
                if os.path.exists(creds_path):
                    with open(creds_path, "r", encoding="utf-8") as f:
                        prof_creds = json.load(f)
                
                matched_prof = None
                for prof_name, c in prof_creds.items():
                    if c["login"].lower() == username.lower() and c["password"] == password:
                        matched_prof = prof_name
                        break
                
                if matched_prof:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    cookie_val = urllib.parse.quote(f"role:professor|nome_professor:{matched_prof}")
                    self.send_header('Set-Cookie', f'session={cookie_val}; Path=/; HttpOnly; SameSite=Strict')
                    self.end_headers()
                    response = {
                        "status": "success", 
                        "role": "professor", 
                        "nome_professor": matched_prof,
                        "message": f"Autenticado como {matched_prof}!"
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                else:
                    self.send_response(401)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {"status": "error", "message": "Usuário ou senha incorretos."}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
            except Exception as e:
                print(f"[SERVER] Erro no processamento de login: {e}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": "Dados de login inválidos."}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/api/logout':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Set-Cookie', 'session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Strict')
            self.end_headers()
            response = {"status": "success", "message": "Desconectado com sucesso."}
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/api/save-mapping':
            session_info = self.get_session_info()
            if not session_info or session_info.get("role") != "admin":
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "forbidden", "message": "Acesso não autorizado para alteração de mapeamento."}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            try:
                # 1. Obter o tamanho dos dados recebidos
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # 2. Decodificar e converter para dicionário
                new_mapping = json.loads(post_data.decode('utf-8'))
                
                # Validação de Schema Server-Side (CWE-20)
                if not isinstance(new_mapping, dict):
                    raise ValueError("Mapeamento inválido: Esperado um objeto JSON.")
                
                valid_folders = ["6º anos", "7º anos", "8º anos", "9º anos", "1ª séries", "2ª séries", "3ª série"]
                for key, val in new_mapping.items():
                    if key not in valid_folders:
                        raise ValueError(f"Série/Pasta inválida: {key}")
                    if not isinstance(val, list):
                        raise ValueError(f"A lista de blocos para {key} deve ser uma lista.")
                    for block in val:
                        required_keys = {"block_index", "start_column_index", "teacher_name", "discipline"}
                        if not all(k in block for k in required_keys):
                            raise ValueError(f"Campos estruturais ausentes no bloco de mapeamento para {key}")
                        if not isinstance(block["block_index"], int) or not isinstance(block["start_column_index"], int):
                            raise ValueError(f"Valores numéricos de índices inválidos no mapeamento de {key}")
                
                # 3. Salvar no arquivo mapeamento_professores.json
                mapping_path = os.path.join(workspace, "mapeamento_professores.json")
                with open(mapping_path, "w", encoding="utf-8") as f:
                    json.dump(new_mapping, f, indent=4, ensure_ascii=False)
                print(f"\n[SERVER] Novo mapeamento recebido via API e salvo em: {mapping_path}")
                
                # 4. Re-executar o processamento dos dados
                print("[SERVER] Reprocessando dados...")
                run_processing()
                print("[SERVER] Dados reprocessados com sucesso!")
                
                # 5. Enviar resposta de sucesso
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "success", "message": "Mapeamento atualizado e dados reprocessados com sucesso!"}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                # Ocultar mensagem de erro crua com caminho absoluto (CWE-209)
                print(f"[SERVER] Erro ao salvar mapeamento: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": "Erro interno no servidor local ao processar dados."}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

# Mudar o diretório de trabalho do servidor para a raiz da workspace
os.chdir(workspace)

Handler = RodinDashboardHandler

# Evitar erro de endereço em uso
socketserver.TCPServer.allow_reuse_address = True

# Vincular apenas ao loopback local (127.0.0.1) para impedir conexões da rede externa/Wi-Fi (CWE-306)
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"\n=========================================================")
    print(f" Servidor local ativo para o Dashboard do Colégio Rodin")
    print(f" Acesse o painel pelo link abaixo (Conexões locais apenas):")
    print(f" http://127.0.0.1:{PORT}")
    print(f"=========================================================\n")
    
    # Abrir o navegador automaticamente na URL do servidor
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
        sys.exit(0)
