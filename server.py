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

    def end_headers(self):
        # Desabilitar cache para que novos dados sempre carreguem instantaneamente
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        # Habilitar CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/save-mapping':
            try:
                # 1. Obter o tamanho dos dados recebidos
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # 2. Decodificar e converter para dicionário
                new_mapping = json.loads(post_data.decode('utf-8'))
                
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
                print(f"[SERVER] Erro ao salvar mapeamento: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

# Mudar o diretório de trabalho do servidor para a raiz da workspace
os.chdir(workspace)

Handler = RodinDashboardHandler

# Evitar erro de endereço em uso
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n=========================================================")
    print(f" Servidor local ativo para o Dashboard do Colégio Rodin")
    print(f" Acesse o painel pelo link abaixo:")
    print(f" http://localhost:{PORT}")
    print(f"=========================================================\n")
    
    # Abrir o navegador automaticamente na URL do servidor
    webbrowser.open(f"http://localhost:{PORT}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
        sys.exit(0)
