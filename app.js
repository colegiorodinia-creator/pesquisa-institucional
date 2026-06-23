// =============================================================
// Colégio Rodin — Dashboard Logic (app.js)
// =============================================================

console.log("[DEBUG] app.js carregado no navegador com sucesso!");
// Estado Global da Aplicação
let rawData = null;
let mappingData = null;
let activeTab = 'macro';
let currentUserProfile = null; // { role: 'admin'|'professor', nome_professor: '...' }

// Configurações do Supabase (Insira as credenciais do seu projeto abaixo se for hospedar de forma 100% estática)
const SUPABASE_CONFIG = {
    url: "https://aykxsgxzrxpwtaptzodi.supabase.co", 
    anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF5a3hzZ3h6cnhwd3RhcHR6b2RpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIxNTMyNzYsImV4cCI6MjA5NzcyOTI3Nn0.hqjYHYVvlyx2YOTuGZb1PTreVvLy1w9rZ94NXCHTfv8"
};

let supabaseClient = null;

async function initSupabaseClient() {
    // Verificar se as credenciais do Supabase são válidas e não apenas placeholders
    const isPlaceholder = (str) => {
        if (!str) return true;
        const s = String(str).toLowerCase();
        return s.includes("seu-projeto") || s.includes("sua-chave") || s.includes("xxxxx") || s.trim() === "";
    };

    // 1. Tentar obter a configuração dinamicamente do servidor local primeiro (se rodando localmente)
    try {
        const res = await fetch('/api/config');
        if (res.ok) {
            const config = await res.json();
            if (config.SUPABASE_URL && config.SUPABASE_ANON_KEY && 
                !isPlaceholder(config.SUPABASE_URL) && !isPlaceholder(config.SUPABASE_ANON_KEY)) {
                
                if (window.supabase && typeof window.supabase.createClient === 'function') {
                    supabaseClient = window.supabase.createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);
                    console.log("[SUPABASE] Cliente inicializado com as credenciais dinâmicas do servidor local.");
                    return true;
                } else {
                    console.warn("[SUPABASE] Biblioteca do Supabase JS não carregada.");
                }
            }
        }
    } catch (e) {
        // Fallback silencioso para constantes locais
    }
    
    // 2. Fallback para constantes locais
    if (SUPABASE_CONFIG.url && SUPABASE_CONFIG.anonKey && 
        !isPlaceholder(SUPABASE_CONFIG.url) && !isPlaceholder(SUPABASE_CONFIG.anonKey)) {
        
        if (window.supabase && typeof window.supabase.createClient === 'function') {
            supabaseClient = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
            console.log("[SUPABASE] Cliente inicializado com as credenciais estáticas do front-end.");
            return true;
        } else {
            console.warn("[SUPABASE] Biblioteca do Supabase JS não carregada.");
        }
    }
    
    console.log("[INFO] Supabase não inicializado ou chaves são placeholders. Rodando em modo local legado.");
    return false;
}

// Instâncias Globais dos Gráficos do Chart.js (para destruição e recriação)
let chartMacroAtributos = null;
let chartMacroProfessores = null;
let chartMacroTurmas = null;
let chartProfRadar = null;
let chartProfTurmas = null;
let chartProfPizzas = [];

// Atributos Oficiais de Mapeamento Pedagógico
const ATRIBUTOS_OFICIAIS = [
    "Didática",
    "Apoio",
    "Tempo",
    "Avaliação",
    "Clima",
    "Respeito",
    "Domínio"
];

// Cores do Design System do Colégio Rodin
const RODIN_COLORS = {
    orange: '#F45206',
    graphite: '#404545',
    concrete: '#AAA38E',
    coolGray: '#969491',
    beige: '#DBD4C2',
    paper: '#F6F4EF',
    ink: '#1F2222',
    white: '#FFFFFF',
    transparentOrange: 'rgba(244, 82, 6, 0.2)',
    transparentGraphite: 'rgba(64, 69, 69, 0.2)'
};

// Plugins do Chart.js para Linhas de Referência de Média Esperada (8.5)
const targetLineHorizontalPlugin = {
    id: 'targetLineHorizontal',
    afterDraw: function(chart) {
        if (chart.scales.y) {
            const ctx = chart.ctx;
            const yVal = chart.scales.y.getPixelForValue(8.5);
            const xAxis = chart.scales.x;
            
            ctx.save();
            ctx.beginPath();
            ctx.strokeStyle = '#F45206'; // Laranja do Rodin
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 4]); // Tracejado
            ctx.moveTo(xAxis.left, yVal);
            ctx.lineTo(xAxis.right, yVal);
            ctx.stroke();
            
            // Etiqueta de texto "Meta 8.5"
            ctx.fillStyle = '#F45206';
            ctx.font = 'bold 10px Helvetica Neue';
            ctx.fillText('META 8.5', xAxis.right - 55, yVal - 5);
            ctx.restore();
        }
    }
};

const targetLineVerticalPlugin = {
    id: 'targetLineVertical',
    afterDraw: function(chart) {
        if (chart.scales.x) {
            const ctx = chart.ctx;
            const xVal = chart.scales.x.getPixelForValue(8.5);
            const yAxis = chart.scales.y;
            
            ctx.save();
            ctx.beginPath();
            ctx.strokeStyle = '#F45206'; // Laranja do Rodin
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 4]); // Tracejado
            ctx.moveTo(xVal, yAxis.top);
            ctx.lineTo(xVal, yAxis.bottom);
            ctx.stroke();
            
            // Etiqueta de texto "Meta 8.5"
            ctx.fillStyle = '#F45206';
            ctx.font = 'bold 10px Helvetica Neue';
            ctx.fillText('META 8.5', xVal + 5, yAxis.top + 15);
            ctx.restore();
        }
    }
};

const customMarkersPlugin = {
    id: 'customMarkers',
    afterDatasetsDraw: function(chart) {
        const ctx = chart.ctx;
        
        // Encontrar os datasets
        const metaDatasetIdx = chart.data.datasets.findIndex(ds => ds.label === 'Média Geral da Turma');
        const barDatasetIdx = chart.data.datasets.findIndex(ds => ds.label === 'Média do Professor');
        
        if (metaDatasetIdx === -1 || barDatasetIdx === -1) return;
        
        const metaDataset = chart.data.datasets[metaDatasetIdx];
        const metaData = metaDataset.data;
        const barMeta = chart.getDatasetMeta(barDatasetIdx);
        
        ctx.save();
        ctx.strokeStyle = '#000000'; // Traço preto
        ctx.lineWidth = 3; // Espessura do traço
        ctx.setLineDash([4, 3]); // Tracejado
        
        barMeta.data.forEach((bar, idx) => {
            const val = metaData[idx];
            if (val === undefined || val === null || isNaN(val)) return;
            
            const y = chart.scales.y.getPixelForValue(val);
            const xStart = bar.x - bar.width / 2;
            const xEnd = bar.x + bar.width / 2;
            
            ctx.beginPath();
            ctx.moveTo(xStart, y);
            ctx.lineTo(xEnd, y);
            ctx.stroke();
        });
        
        ctx.restore();
    }
};



async function fetchUserProfile(useSupabase) {
    if (useSupabase && supabaseClient) {
        try {
            const { data: { user } } = await supabaseClient.auth.getUser();
            if (user) {
                const { data, error } = await supabaseClient
                    .from('professores_perfis')
                    .select('*')
                    .eq('id', user.id)
                    .single();
                if (!error && data) {
                    currentUserProfile = data;
                    console.log("[AUTH] Perfil carregado do Supabase:", currentUserProfile);
                    return true;
                }
            }
        } catch (e) {
            console.error("Erro ao buscar perfil no Supabase:", e);
        }
    } else {
        // Fallback local legado: carregar dados de sessão do backend Python
        try {
            const res = await fetch('/api/session');
            if (res.ok) {
                const sessionData = await res.json();
                if (sessionData && sessionData.role) {
                    currentUserProfile = {
                        role: sessionData.role,
                        nome_professor: sessionData.nome_professor || sessionData.name || ""
                    };
                    console.log("[AUTH] Perfil carregado da sessão local:", currentUserProfile);
                    return true;
                }
            }
        } catch (e) {
            console.error("Erro ao buscar sessão no servidor local:", e);
        }
    }
    return false;
}

function applyRBACUI() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabsNav = document.querySelector('.tabs-nav');
    
    if (currentUserProfile && currentUserProfile.role === 'professor') {
        console.log("[RBAC] Aplicando restrições de Professor para:", currentUserProfile.nome_professor);
        
        // 1. Ocultar o menu inteiro de abas para o professor
        if (tabsNav) {
            tabsNav.style.display = 'none';
        }
        
        // Ocultar filtros globais da diretoria
        const globalFilters = document.getElementById('global-filters');
        if (globalFilters) {
            globalFilters.style.display = 'none';
        }
        
        // Definir aba ativa como 'professor' por padrão e ocultar as demais classes ativas
        activeTab = 'professor';
        document.querySelectorAll('.tab-content').forEach(content => {
            if (content.id === 'tab-professor') {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
    } else {
        // Diretor / Admin: Mostrar todas as abas e habilitar tudo
        if (tabsNav) {
            tabsNav.style.display = '';
        }
        tabButtons.forEach(btn => {
            btn.style.display = 'inline-block';
        });
        const globalFilters = document.getElementById('global-filters');
        if (globalFilters) {
            globalFilters.style.display = 'block';
        }
        const selectProf = document.getElementById('select-professor');
        if (selectProf) {
            selectProf.disabled = false;
            selectProf.style.backgroundColor = '';
            selectProf.style.cursor = '';
            selectProf.style.opacity = '';
        }
    }
}

async function checkAuthAndInit() {
    console.log("[DEBUG] checkAuthAndInit iniciado!");
    /* 1. Configurar os ouvintes de evento de login/logout síncronos imediatamente */
    setupAuthHandlers();
    
    /* 2. Garantir renderização imediata dos ícones do Lucide na tela de login */
    lucide.createIcons();
    
    /* 3. Inicializar o cliente do Supabase de forma assíncrona */
    const hasSupabase = await initSupabaseClient();
    
    if (hasSupabase && supabaseClient) {
        try {
            // Verificar sessão remota do Supabase
            const { data: { session } } = await supabaseClient.auth.getSession();
            if (session) {
                await fetchUserProfile(true);
                const authenticated = await loadData(true);
                if (authenticated) {
                    const loginOverlay = document.getElementById('login-overlay');
                    const btnLogout = document.getElementById('btn-logout');
                    
                    if (loginOverlay) loginOverlay.classList.add('hidden');
                    if (btnLogout) btnLogout.style.display = 'inline-flex';
                    
                    // Inicializar aplicação
                    await initApp();
                    return;
                }
            } else {
                console.log("[AUTH] Sem sessão do Supabase ativa. Exibindo tela de login obrigatoriamente.");
                const loginOverlay = document.getElementById('login-overlay');
                const btnLogout = document.getElementById('btn-logout');
                if (loginOverlay) loginOverlay.classList.remove('hidden');
                if (btnLogout) btnLogout.style.display = 'none';
                return;
            }
        } catch (e) {
            console.error("[SUPABASE] Erro ao verificar sessão do usuário:", e);
        }
    } else {
        // Fallback local legado (apenas quando Supabase não estiver configurado/ativo)
        await fetchUserProfile(false);
        const authenticated = await loadData(false);
        if (authenticated) {
            const loginOverlay = document.getElementById('login-overlay');
            const btnLogout = document.getElementById('btn-logout');
            
            if (loginOverlay) loginOverlay.classList.add('hidden');
            if (btnLogout) btnLogout.style.display = 'inline-flex';
            
            // Inicializar aplicação
            await initApp();
        } else {
            const loginOverlay = document.getElementById('login-overlay');
            const btnLogout = document.getElementById('btn-logout');
            if (loginOverlay) loginOverlay.classList.remove('hidden');
            if (btnLogout) btnLogout.style.display = 'none';
        }
    }
}

function setupAuthHandlers() {
    const loginForm = document.getElementById('login-form');
    const loginOverlay = document.getElementById('login-overlay');
    const usernameInput = document.getElementById('login-username');
    const passwordInput = document.getElementById('login-password');
    const btnTogglePassword = document.getElementById('btn-toggle-password');
    const iconTogglePassword = document.getElementById('icon-toggle-password');
    const errorMsg = document.getElementById('login-error-msg');
    const errorText = document.getElementById('error-text');
    const btnLogout = document.getElementById('btn-logout');

    // Toggle de exibir/ocultar senha
    if (btnTogglePassword && passwordInput) {
        btnTogglePassword.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            iconTogglePassword.setAttribute('data-lucide', isPassword ? 'eye-off' : 'eye');
            lucide.createIcons();
        });
    }

    // Evento de Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (errorMsg) errorMsg.style.display = 'none';

            const username = usernameInput.value.trim();
            const password = passwordInput.value;

            if (supabaseClient) {
                // Autenticar com o Supabase Auth
                try {
                    // Mapear o username 'Diretor' para o email criado no Supabase Auth
                    const email = username.includes('@') ? username : 'diretor@colegiorodin.com.br';
                    
                    const { data, error } = await supabaseClient.auth.signInWithPassword({
                        email: email,
                        password: password
                    });

                    if (error) {
                        if (errorText) errorText.innerText = 'Usuário ou senha incorretos.';
                        if (errorMsg) errorMsg.style.display = 'flex';
                    } else if (data.session) {
                        if (loginOverlay) loginOverlay.classList.add('hidden');
                        if (btnLogout) btnLogout.style.display = 'inline-flex';
                        
                        // Carregar dados remotos do Supabase
                        const loaded = await loadData(true);
                        if (loaded) {
                            await initApp();
                        } else {
                            if (errorText) errorText.innerText = 'Falha ao buscar dados do Supabase.';
                            if (errorMsg) errorMsg.style.display = 'flex';
                        }
                    }
                } catch (err) {
                    console.error("Erro no login Supabase:", err);
                    if (errorText) errorText.innerText = 'Erro ao se conectar ao Supabase Auth.';
                    if (errorMsg) errorMsg.style.display = 'flex';
                }
            } else {
                // Fallback local
                try {
                    const res = await fetch('/api/login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ username, password })
                    });

                    const data = await res.json();

                    if (res.ok && data.status === 'success') {
                        // Obter dados ANTES de ocultar o overlay para evitar dashboard em branco em caso de erro
                        const loaded = await loadData(false);
                        if (loaded) {
                            if (loginOverlay) loginOverlay.classList.add('hidden');
                            if (btnLogout) btnLogout.style.display = 'inline-flex';
                            await initApp();
                        } else {
                            if (errorText) errorText.innerText = 'Falha ao carregar os dados seguros do servidor.';
                            if (errorMsg) errorMsg.style.display = 'flex';
                        }
                    } else {
                        if (errorText) errorText.innerText = data.message || 'Usuário ou senha incorretos.';
                        if (errorMsg) errorMsg.style.display = 'flex';
                    }
                } catch (err) {
                    console.error("Erro na chamada de login:", err);
                    if (errorText) errorText.innerText = 'Erro de rede ou conexão com o servidor local.';
                    if (errorMsg) errorMsg.style.display = 'flex';
                }
            }
        });
    }

    // Evento de Logout
    if (btnLogout) {
        btnLogout.addEventListener('click', async () => {
            if (supabaseClient) {
                try {
                    await supabaseClient.auth.signOut();
                    window.location.reload();
                } catch (err) {
                    console.error("Erro ao efetuar logout no Supabase:", err);
                    window.location.reload();
                }
            } else {
                try {
                    await fetch('/api/logout', { method: 'POST' });
                    window.location.reload();
                } catch (err) {
                    console.error("Erro ao efetuar logout local:", err);
                    window.location.reload();
                }
            }
        });
    }
}

async function initApp() {
    // Registrar datalabels globalmente e desativar por padrão
    if (typeof ChartDataLabels !== 'undefined') {
        Chart.register(ChartDataLabels);
        Chart.defaults.plugins.datalabels.display = false;
    }
    
    // Garantir que o perfil do usuário esteja carregado e aplicar regras de UI
    const isSupabaseActive = !!supabaseClient;
    await fetchUserProfile(isSupabaseActive);
    applyRBACUI();
    
    // 1. Configurar Controle de Abas
    setupTabControls();
    
    // 2. Configurar Filtros Globais e Eventos
    setupFilters();
    
    // 3. Renderizar Tela Inicial (Visão Macro)
    renderActiveTab();
    
    // Recriar ícones do Lucide para o dashboard recém-exibido
    lucide.createIcons();
}

// -------------------------------------------------------------
// Controle de Abas
// -------------------------------------------------------------
function setupTabControls() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (currentUserProfile && currentUserProfile.role === 'professor') {
                // Impede a troca manual de abas para professores
                return;
            }
            const targetTab = btn.getAttribute('data-tab');
            
            // Alterar botão ativo
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Alterar conteúdo visível
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`tab-${targetTab}`).classList.add('active');
            
            activeTab = targetTab;
            
            // Gerenciar exibição de filtros globais (ocultar no mapeamento e qualitativo)
            const filtersSection = document.getElementById('global-filters');
            if (activeTab === 'mapeamento' || activeTab === 'qualitativo') {
                filtersSection.style.display = 'none';
            } else {
                filtersSection.style.display = 'block';
            }
            
            renderActiveTab();
        });
    });
}

// -------------------------------------------------------------
// Carregamento de Dados (AJAX / Supabase)
// -------------------------------------------------------------
async function loadData(useSupabase = false) {
    if (useSupabase && supabaseClient) {
        try {
            console.log("[SUPABASE] Buscando dados remotos do PostgreSQL...");
            
            // 1. Obter todas as respostas do Supabase usando paginação (limite padrão do PostgREST é 1000)
            let resData = [];
            let start = 0;
            let limit = 1000;
            let hasMore = true;
            
            while (hasMore) {
                const { data: batch, error: errDb } = await supabaseClient
                    .from('respostas')
                    .select('*')
                    .range(start, start + limit - 1);
                    
                if (errDb) throw errDb;
                
                resData = resData.concat(batch);
                if (batch.length < limit) {
                    hasMore = false;
                } else {
                    start += limit;
                }
            }
            
            // 2. Obter mapeamentos do Supabase
            const { data: mapData, error: errMap } = await supabaseClient
                .from('mapeamento')
                .select('*');
                
            if (errMap) throw errMap;
            
            // Converter respostas do Supabase para a estrutura rawData esperada pelo front-end
            const answersConverted = resData.map(r => ({
                id: r.id,
                turma_pasta: r.turma_pasta,
                turma_declarada: r.turma_declarada,
                segmento: r.segmento,
                professor: r.professor,
                disciplina: r.disciplina,
                timestamp: r.timestamp || "",
                comentario: r.comentario || "",
                ratings: {
                    "Didática": r.didatica,
                    "Apoio": r.apoio,
                    "Tempo": r.tempo,
                    "Avaliação": r.avaliacao,
                    "Clima": r.clima,
                    "Respeito": r.respeito,
                    "Domínio": r.dominio
                }
            }));
            
            // Extrair listas únicas de professores e turmas
            const uniqueProfs = [...new Set(answersConverted.map(r => r.professor))].sort();
            const uniqueTurmas = [...new Set(answersConverted.map(r => r.turma_declarada))].sort();
            
            rawData = {
                segmentos: ["Ensino Fundamental II", "Ensino Médio"],
                turmas: uniqueTurmas,
                professores: uniqueProfs,
                atributos: [
                    "Didática",
                    "Apoio",
                    "Tempo",
                    "Avaliação",
                    "Clima",
                    "Respeito",
                    "Domínio"
                ],
                respostas: answersConverted
            };
            
            // Reconstruir o mappingData
            mappingData = {};
            mapData.forEach(m => {
                if (!mappingData[m.turma_pasta]) {
                    mappingData[m.turma_pasta] = [];
                }
                
                let turmasArray = [];
                if (m.turmas) {
                    turmasArray = typeof m.turmas === 'string' ? JSON.parse(m.turmas) : m.turmas;
                }
                
                mappingData[m.turma_pasta].push({
                    block_index: m.block_index,
                    start_column_index: m.start_column_index,
                    teacher_name: m.teacher_name,
                    discipline: m.discipline,
                    turmas: turmasArray
                });
            });
            
            // Ordenar blocos por block_index
            for (const key in mappingData) {
                mappingData[key].sort((a, b) => a.block_index - b.block_index);
            }
            
            return true;
        } catch (e) {
            console.error("Erro ao carregar dados do Supabase:", e);
            return false;
        }
    } else {
        // Lógica local legado
        try {
            const resDb = await fetch('/data.json');
            if (resDb.status === 401) {
                return false;
            }
            rawData = await resDb.json();
            
            if (currentUserProfile && currentUserProfile.role === 'professor') {
                currentUserProfile.nomes_exibicao = rawData.professores || [];
            }
            
            const resMap = await fetch('/mapeamento_professores.json');
            if (resMap.status === 401) {
                return false;
            }
            mappingData = await resMap.json();
            
            return true;
        } catch (e) {
            console.error("Erro ao carregar JSON:", e);
            return false;
        }
    }
}

// -------------------------------------------------------------
// Configuração e Lógica de Filtros Globais
// -------------------------------------------------------------
function updateFilterDropdowns() {
    const filterSegmento = document.getElementById('filter-segmento');
    const filterTurmaPasta = document.getElementById('filter-turma-pasta');
    const filterTurmaDeclarada = document.getElementById('filter-turma-declarada');
    
    const selectedSeg = filterSegmento.value;
    const selectedPasta = filterTurmaPasta.value;
    const selectedDec = filterTurmaDeclarada.value;
    
    // Obter todas as respostas originais
    let responses = rawData.respostas;
    
    // 1. Filtrar opções de Ano/Série (Pasta) baseadas no Segmento
    let validPastas = [...new Set(responses.map(r => r.turma_pasta))];
    if (selectedSeg) {
        validPastas = [...new Set(responses.filter(r => r.segmento === selectedSeg).map(r => r.turma_pasta))];
    }
    validPastas.sort();
    
    // Atualizar dropdown de pasta
    filterTurmaPasta.innerHTML = '<option value="">Todos os Anos/Séries</option>';
    validPastas.forEach(p => {
        filterTurmaPasta.innerHTML += `<option value="${p}">${p}</option>`;
    });
    
    // Restaurar seleção de pasta se ainda válida
    if (selectedPasta && validPastas.includes(selectedPasta)) {
        filterTurmaPasta.value = selectedPasta;
    } else {
        filterTurmaPasta.value = "";
    }
    
    // 2. Filtrar opções de Turma Específica (Declarada) baseadas no Segmento e na Pasta
    const currentPasta = filterTurmaPasta.value;
    let validDeclaradas = responses;
    if (selectedSeg) {
        validDeclaradas = validDeclaradas.filter(r => r.segmento === selectedSeg);
    }
    if (currentPasta) {
        validDeclaradas = validDeclaradas.filter(r => r.turma_pasta === currentPasta);
    }
    
    const uniqueDeclaradas = [...new Set(validDeclaradas.map(r => r.turma_declarada))].sort();
    
    // Atualizar dropdown de declarada
    filterTurmaDeclarada.innerHTML = '<option value="">Todas as Turmas</option>';
    uniqueDeclaradas.forEach(d => {
        filterTurmaDeclarada.innerHTML += `<option value="${d}">${d}</option>`;
    });
    
    // Restaurar seleção de declarada se ainda válida
    if (selectedDec && uniqueDeclaradas.includes(selectedDec)) {
        filterTurmaDeclarada.value = selectedDec;
    } else {
        filterTurmaDeclarada.value = "";
    }
}

function setupFilters() {
    const filterSegmento = document.getElementById('filter-segmento');
    const filterTurmaPasta = document.getElementById('filter-turma-pasta');
    const filterTurmaDeclarada = document.getElementById('filter-turma-declarada');
    const btnReset = document.getElementById('btn-reset-filters');
    
    // Inicializar os dropdowns em cascata
    updateFilterDropdowns();
    
    // Eventos de alteração dos filtros
    filterSegmento.addEventListener('change', () => {
        updateFilterDropdowns();
        triggerFilterUpdate();
    });

    filterTurmaPasta.addEventListener('change', () => {
        // Atualizar apenas o dropdown de turmas declaradas com base na nova pasta selecionada
        const selectedSeg = filterSegmento.value;
        const selectedPasta = filterTurmaPasta.value;
        const selectedDec = filterTurmaDeclarada.value;
        
        let validDeclaradas = rawData.respostas;
        if (selectedSeg) validDeclaradas = validDeclaradas.filter(r => r.segmento === selectedSeg);
        if (selectedPasta) validDeclaradas = validDeclaradas.filter(r => r.turma_pasta === selectedPasta);
        
        const uniqueDeclaradas = [...new Set(validDeclaradas.map(r => r.turma_declarada))].sort();
        
        filterTurmaDeclarada.innerHTML = '<option value="">Todas as Turmas</option>';
        uniqueDeclaradas.forEach(d => {
            filterTurmaDeclarada.innerHTML += `<option value="${d}">${d}</option>`;
        });
        
        if (selectedDec && uniqueDeclaradas.includes(selectedDec)) {
            filterTurmaDeclarada.value = selectedDec;
        } else {
            filterTurmaDeclarada.value = "";
        }
        
        triggerFilterUpdate();
    });
    
    filterTurmaDeclarada.addEventListener('change', triggerFilterUpdate);
    
    btnReset.addEventListener('click', () => {
        filterSegmento.value = '';
        filterTurmaPasta.value = '';
        filterTurmaDeclarada.value = '';
        updateFilterDropdowns();
        triggerFilterUpdate();
    });
}

function triggerFilterUpdate() {
    renderActiveTab();
}

// Obter respostas filtradas com base nos filtros globais ativos
function getFilteredResponses(ignoreDeclarada = false) {
    const seg = document.getElementById('filter-segmento').value;
    const pasta = document.getElementById('filter-turma-pasta').value;
    const dec = document.getElementById('filter-turma-declarada').value;
    
    return rawData.respostas.filter(r => {
        if (seg && r.segmento !== seg) return false;
        if (pasta && r.turma_pasta !== pasta) return false;
        if (!ignoreDeclarada && dec && r.turma_declarada !== dec) return false;
        return true;
    });
}

// -------------------------------------------------------------
// Renderizador da Aba Ativa
// -------------------------------------------------------------
function renderActiveTab() {
    if (activeTab === 'macro') {
        renderVisaoMacro();
    } else if (activeTab === 'professor') {
        renderVisaoProfessor();
    } else if (activeTab === 'turma') {
        renderVisaoTurma();
    } else if (activeTab === 'qualitativo') {
        renderVisaoQualitativo();
    } else if (activeTab === 'mapeamento') {
        renderVisaoMapeamento();
    }
}

// Helper para calcular a média de uma lista de valores ignorando nulos
function getAverage(values) {
    const valid = values.filter(v => v !== null && v !== undefined && !isNaN(v));
    if (valid.length === 0) return 0;
    return valid.reduce((sum, v) => sum + v, 0) / valid.length;
}

// Helper para normalizar a nota de 1-4 para 0-10
function normalizeScore(score) {
    if (score === null || score === undefined || isNaN(score) || score === 0) return 0;
    return ((score - 1) * 10) / 3;
}

// Helper para retornar a cor da nota baseada na escala de 0 a 10
function getScoreColor(score) {
    if (score === null || score === undefined || isNaN(score) || score === 0) return '#AAA38E'; // Concrete / Gray default
    if (score < 5.0) return '#EF5350'; // Vermelho (Crítico)
    if (score < 7.0) return '#FFCA28'; // Amarelo (Regular)
    if (score <= 8.5) return '#66BB6A'; // Verde (Bom)
    return '#42A5F5'; // Azul (Excelente)
}

// Helper para escapar caracteres especiais do HTML contra vulnerabilidades XSS (CWE-79)
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// -------------------------------------------------------------
// VISÃO 1: VISÃO MACRO
// -------------------------------------------------------------
function renderVisaoMacro() {
    const respostas = getFilteredResponses();
    
    // 1. Calcular KPIs
    // Média Geral Escola
    const todasNotas = respostas.flatMap(r => Object.values(r.ratings));
    const mediaGeral = normalizeScore(getAverage(todasNotas));
    document.getElementById('kpi-media-geral').innerText = mediaGeral.toFixed(2);
    
    // Média Fund II
    const notasFund2 = respostas.filter(r => r.segmento === 'Ensino Fundamental II').flatMap(r => Object.values(r.ratings));
    document.getElementById('kpi-media-fund2').innerText = notasFund2.length ? normalizeScore(getAverage(notasFund2)).toFixed(2) : 'N/A';
    
    // Média Ensino Médio
    const notasMedio = respostas.filter(r => r.segmento === 'Ensino Médio').flatMap(r => Object.values(r.ratings));
    document.getElementById('kpi-media-medio').innerText = notasMedio.length ? normalizeScore(getAverage(notasMedio)).toFixed(2) : 'N/A';
    
    // Total Respostas
    document.getElementById('kpi-total-respostas').innerText = respostas.length.toLocaleString('pt-BR');
    
    // 2. Gráfico 1: Média por Atributo
    const mediaAtributos = ATRIBUTOS_OFICIAIS.map(attr => {
        const notasAttr = respostas.map(r => r.ratings[attr]);
        return normalizeScore(getAverage(notasAttr));
    });
    const coresAtributos = mediaAtributos.map(score => getScoreColor(score));
    
    if (chartMacroAtributos) chartMacroAtributos.destroy();
    const ctxAttr = document.getElementById('chart-macro-atributos').getContext('2d');
    chartMacroAtributos = new Chart(ctxAttr, {
        type: 'bar',
        data: {
            labels: ATRIBUTOS_OFICIAIS,
            datasets: [{
                label: 'Média Escola',
                data: mediaAtributos,
                backgroundColor: coresAtributos,
                borderWidth: 0,
                barThickness: 20
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { min: 0, max: 10, grid: { color: 'rgba(31,34,34,0.06)' } },
                y: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false }
            }
        },
        plugins: [targetLineVerticalPlugin]
    });
    
    // 3. Gráfico 2: Ranking de Docentes
    // Agrupar por professor e calcular média
    const profs = [...new Set(respostas.map(r => r.professor))];
    const profRatings = profs.map(p => {
        const vats = respostas.filter(r => r.professor === p).flatMap(r => Object.values(r.ratings));
        return { name: p, score: normalizeScore(getAverage(vats)) };
    }).sort((a, b) => b.score - a.score).slice(0, 15); // Top 15 professores
    
    if (chartMacroProfessores) chartMacroProfessores.destroy();
    const ctxProf = document.getElementById('chart-macro-professores').getContext('2d');
    const coresProf = profRatings.map(p => getScoreColor(p.score));
    chartMacroProfessores = new Chart(ctxProf, {
        type: 'bar',
        data: {
            labels: profRatings.map(p => p.name),
            datasets: [{
                label: 'Média Docente',
                data: profRatings.map(p => p.score),
                backgroundColor: coresProf,
                borderWidth: 0,
                barThickness: 16
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 10, grid: { color: 'rgba(31,34,34,0.06)' } },
                x: { grid: { display: false }, ticks: { autoSkip: false, maxRotation: 45, minRotation: 45 } }
            },
            plugins: {
                legend: { display: false }
            },
            // Integração dinâmica: Ao clicar no professor no gráfico do ranking, navegar para o Qualitativo filtrado!
            onClick: (e, elements) => {
                if (elements.length > 0) {
                    const activeElement = elements[0];
                    const teacherName = chartMacroProfessores.data.labels[activeElement.index];
                    navigateToQualitative(teacherName, '');
                }
            }
        },
        plugins: [targetLineHorizontalPlugin]
    });

    // 4. Gráfico 3: Comparativo entre Turmas
    const turmas = [...new Set(respostas.map(r => r.turma_declarada))].sort();
    const turmaRatings = turmas.map(t => {
        const vats = respostas.filter(r => r.turma_declarada === t).flatMap(r => Object.values(r.ratings));
        return { name: t, score: normalizeScore(getAverage(vats)) };
    });

    if (chartMacroTurmas) chartMacroTurmas.destroy();
    const ctxTurmas = document.getElementById('chart-macro-turmas').getContext('2d');
    const coresTurmas = turmaRatings.map(t => getScoreColor(t.score));
    chartMacroTurmas = new Chart(ctxTurmas, {
        type: 'bar',
        data: {
            labels: turmaRatings.map(t => t.name),
            datasets: [{
                label: 'Média Turma',
                data: turmaRatings.map(t => t.score),
                backgroundColor: coresTurmas,
                borderWidth: 0,
                barThickness: 24
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 10, grid: { color: 'rgba(31,34,34,0.06)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: { display: false }
            },
            onClick: (e, elements) => {
                if (elements.length > 0) {
                    const activeElement = elements[0];
                    const turmaName = chartMacroTurmas.data.labels[activeElement.index];
                    navigateToQualitative('', turmaName);
                }
            }
        },
        plugins: [targetLineHorizontalPlugin]
    });
}

// Navegar para o painel qualitativo aplicando filtros automaticamente
function navigateToQualitative(teacherName, turmaName) {
    const tabQual = document.querySelector('.tab-btn[data-tab="qualitativo"]');
    if (tabQual) {
        tabQual.click(); // Forçar clique na aba qualitativo
        
        // Aplicar filtros na tela
        if (teacherName) {
            document.getElementById('select-qual-prof').value = teacherName;
        }
        if (turmaName) {
            document.getElementById('select-qual-turma').value = turmaName;
        }
        
        // Atualizar visualização qualitativa
        renderVisaoQualitativo();
    }
}

// -------------------------------------------------------------
// VISÃO 2: RAIO-X POR PROFESSOR
// -------------------------------------------------------------
function renderVisaoProfessor() {
    const respostas = getFilteredResponses();
    const selectProf = document.getElementById('select-professor');
    
    // Se for perfil de professor, popular com as suas disciplinas
    if (currentUserProfile && currentUserProfile.role === 'professor') {
        const nomesExib = currentUserProfile.nomes_exibicao || [];
        const prevSelection = selectProf.value;
        
        selectProf.innerHTML = '';
        if (nomesExib.length > 1) {
            selectProf.innerHTML += `<option value="all_mine">Todas as minhas matérias</option>`;
        }
        nomesExib.forEach(p => {
            selectProf.innerHTML += `<option value="${p}">${p}</option>`;
        });
        
        // Restaurar seleção se válida, senão usar default
        if (prevSelection && (prevSelection === "all_mine" || nomesExib.includes(prevSelection))) {
            selectProf.value = prevSelection;
        } else if (nomesExib.length > 1) {
            selectProf.value = "all_mine";
        } else if (nomesExib.length > 0) {
            selectProf.value = nomesExib[0];
        }
        
        if (nomesExib.length > 1) {
            selectProf.disabled = false;
            selectProf.style.backgroundColor = '';
            selectProf.style.cursor = '';
            selectProf.style.opacity = '';
        } else {
            selectProf.disabled = true;
            selectProf.style.backgroundColor = 'var(--bg-2)';
            selectProf.style.cursor = 'not-allowed';
            selectProf.style.opacity = '0.8';
        }
    } else {
        // Obter lista única de professores e preencher dropdown se estiver vazio
        const profs = [...new Set(respostas.map(r => r.professor))].sort();
        const prevSelection = selectProf.value;
        
        selectProf.innerHTML = '';
        profs.forEach(p => {
            selectProf.innerHTML += `<option value="${p}">${p}</option>`;
        });
        
        // Restaurar seleção se ainda válida, senão usar o primeiro
        if (prevSelection && profs.includes(prevSelection)) {
            selectProf.value = prevSelection;
        } else if (profs.length > 0) {
            selectProf.value = profs[0];
        }
        
        selectProf.disabled = false;
        selectProf.style.backgroundColor = '';
        selectProf.style.cursor = '';
        selectProf.style.opacity = '';
    }
    
    const selectedTeacher = selectProf.value;
    if (!selectedTeacher) return;
    
    // Adicionar listener de troca de professor
    selectProf.onchange = renderVisaoProfessor;
    
    // Filtrar dados do professor selecionado
    let profResponses;
    if (selectedTeacher === "all_mine" && currentUserProfile && currentUserProfile.role === 'professor') {
        const nomesExib = currentUserProfile.nomes_exibicao || [];
        profResponses = respostas.filter(r => nomesExib.includes(r.professor));
    } else {
        profResponses = respostas.filter(r => r.professor === selectedTeacher);
    }
    
    // 1. Calcular KPIs do Professor
    const notasProf = profResponses.flatMap(r => Object.values(r.ratings));
    const mediaProfVal = normalizeScore(getAverage(notasProf));
    document.getElementById('kpi-prof-media').innerText = mediaProfVal.toFixed(2);
    document.getElementById('kpi-prof-total').innerText = profResponses.length.toLocaleString('pt-BR');
    
    // Descobrir Destaques (> 9.0) e Pontos de Atenção (< 6.0)
    const destaques = [];
    const atencoes = [];
    
    const mediaAtributosProf = ATRIBUTOS_OFICIAIS.map(attr => {
        const scores = profResponses.map(r => r.ratings[attr]);
        const avg = getAverage(scores);
        const normScore = normalizeScore(avg);
        
        if (normScore > 9.0) {
            destaques.push(attr);
        } else if (normScore < 6.0) {
            atencoes.push(attr);
        }
        
        return normScore;
    });
    
    const destaquesText = destaques.length > 0 ? destaques.join(', ') : 'Nenhum';
    const atencoesText = atencoes.length > 0 ? atencoes.join(', ') : 'Nenhum';
    
    const elForte = document.getElementById('kpi-prof-forte');
    elForte.innerText = destaquesText;
    elForte.style.whiteSpace = 'normal';
    elForte.style.fontSize = destaques.length > 1 ? '13px' : '20px';
    elForte.style.lineHeight = '1.2';
    
    const elFraco = document.getElementById('kpi-prof-fraco');
    elFraco.innerText = atencoesText;
    elFraco.style.whiteSpace = 'normal';
    elFraco.style.fontSize = atencoes.length > 1 ? '13px' : '20px';
    elFraco.style.lineHeight = '1.2';
    
    // 2. Gráfico 1: Radar de Competências (Docente vs. Suas Turmas vs. Meta Esperada)
    // Obter as turmas em que o professor selecionado atua
    const turmasDoProfessor = [...new Set(profResponses.map(r => r.turma_declarada))];
    
    // Calcular a média geral de todas as respostas das turmas em que o professor dá aula
    const respostasDasTurmas = respostas.filter(r => turmasDoProfessor.includes(r.turma_declarada));
    const mediaAtributosTurmas = ATRIBUTOS_OFICIAIS.map(attr => {
        const scores = respostasDasTurmas.map(r => r.ratings[attr]);
        return normalizeScore(getAverage(scores));
    });
    
    // Média esperada estática (Meta de 8.5 para todos os atributos)
    const mediaEsperada = ATRIBUTOS_OFICIAIS.map(() => 8.5);
    
    // Cores específicas de cada ponto (atributo) do professor
    const pointColors = mediaAtributosProf.map(score => getScoreColor(score));
    
    if (chartProfRadar) chartProfRadar.destroy();
    const ctxRadar = document.getElementById('chart-prof-radar').getContext('2d');
    chartProfRadar = new Chart(ctxRadar, {
        type: 'radar',
        data: {
            labels: ATRIBUTOS_OFICIAIS.map(a => a.split(' ')), // divide palavras em array para quebrar linha no radar
            datasets: [
                {
                    label: selectedTeacher === "all_mine" ? (currentUserProfile ? currentUserProfile.nome_professor : "Consolidado") : selectedTeacher,
                    data: mediaAtributosProf,
                    backgroundColor: 'rgba(244, 82, 6, 0.12)', // Laranja translúcido
                    borderColor: '#F45206', // Laranja do Colégio Rodin
                    borderWidth: 2.5,
                    pointBackgroundColor: pointColors,
                    pointBorderColor: pointColors,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointBorderWidth: 2
                },
                {
                    label: 'Média das Suas Turmas',
                    data: mediaAtributosTurmas,
                    backgroundColor: 'rgba(64, 69, 69, 0.02)',
                    borderColor: '#404545', // Grafite para a média das turmas
                    borderWidth: 1.5,
                    pointBackgroundColor: '#404545',
                    pointBorderColor: '#404545',
                    pointRadius: 3,
                    borderDash: [3, 3]
                },
                {
                    label: 'Média Esperada (8.5)',
                    data: mediaEsperada,
                    backgroundColor: 'rgba(2, 136, 209, 0.01)',
                    borderColor: '#0288D1', // Azul ciano para a meta esperada
                    borderWidth: 1.2,
                    pointBackgroundColor: '#0288D1',
                    pointBorderColor: '#0288D1',
                    pointRadius: 2.5,
                    borderDash: [2, 4] // Pontilhado fino
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    min: 0,
                    max: 10,
                    ticks: { stepSize: 2, showLabelBackdrop: false, font: { size: 10 } },
                    grid: { color: 'rgba(31,34,34,0.06)' },
                    angleLines: { color: 'rgba(31,34,34,0.06)' }
                }
            },
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
    
    // 3. Gráfico 2: Desempenho por Turma
    const profTurmas = [...new Set(profResponses.map(r => r.turma_declarada))].sort();
    const profTurmaScores = profTurmas.map(t => {
        const vats = profResponses.filter(r => r.turma_declarada === t).flatMap(r => Object.values(r.ratings));
        return normalizeScore(getAverage(vats));
    });
    const turmaGeralScores = profTurmas.map(t => {
        const vats = respostas.filter(r => r.turma_declarada === t).flatMap(r => Object.values(r.ratings));
        return normalizeScore(getAverage(vats));
    });
    
    if (chartProfTurmas) chartProfTurmas.destroy();
    const ctxProfTurmas = document.getElementById('chart-prof-turmas').getContext('2d');
    const coresProfTurmas = profTurmaScores.map(score => getScoreColor(score));
    chartProfTurmas = new Chart(ctxProfTurmas, {
        data: {
            labels: profTurmas,
            datasets: [
                {
                    type: 'bar',
                    label: 'Média do Professor',
                    data: profTurmaScores,
                    backgroundColor: coresProfTurmas,
                    borderWidth: 0,
                    barThickness: 20,
                    order: 2
                },
                {
                    type: 'line',
                    label: 'Média Geral da Turma',
                    data: turmaGeralScores,
                    showLine: false, // Ocultar linha de conexão
                    pointRadius: 0, // Ocultar pontos nativos
                    pointHoverRadius: 0,
                    borderColor: '#000000', // Linha preta na legenda
                    borderWidth: 2.5, // Espessura na legenda
                    borderDash: [4, 3], // Tracejado na legenda
                    fill: false,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 10, grid: { color: 'rgba(31,34,34,0.06)' } },
                x: { grid: { display: false } }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        font: { size: 11 }
                    }
                }
            }
        },
        plugins: [targetLineHorizontalPlugin, customMarkersPlugin]
    });

    // 4. Renderizar Distribuição Likert (Gráficos de Pizza/Setores - Doughnut)
    const distGrid = document.getElementById('likert-dist-grid');
    
    // Destruir gráficos de pizza anteriores para evitar vazamento de memória e sobreposição
    if (chartProfPizzas && chartProfPizzas.length > 0) {
        chartProfPizzas.forEach(c => c.destroy());
    }
    chartProfPizzas = [];
    
    distGrid.innerHTML = '';
    
    // 4.1 Injetar elementos Canvas no DOM
    ATRIBUTOS_OFICIAIS.forEach((attr, idx) => {
        distGrid.innerHTML += `
            <div class="likert-attr-card" style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 270px; padding: var(--space-4);">
                <div class="likert-attr-title" style="margin-bottom: var(--space-3); text-align: center; font-weight: 700; font-size: 13px;">${attr}</div>
                <div style="position: relative; width: 100%; height: 180px; display: flex; align-items: center; justify-content: center;">
                    <canvas id="chart-likert-pie-${idx}"></canvas>
                </div>
            </div>
        `;
    });
    
    // 4.2 Instanciar gráficos de setores para cada atributo
    ATRIBUTOS_OFICIAIS.forEach((attr, idx) => {
        const answers = profResponses.map(r => r.ratings[attr]).filter(v => v !== null && v !== undefined);
        const count = answers.length;
        
        const canvas = document.getElementById(`chart-likert-pie-${idx}`);
        if (!canvas) return;
        
        if (count === 0) {
            const card = canvas.parentElement;
            card.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 180px; color: var(--fg-3); font-style: italic; font-size: 12px; text-align: center;">Sem respostas registradas</div>`;
            return;
        }
        
        let cSempre = answers.filter(v => v === 4).length;
        let cQuaseSempre = answers.filter(v => v === 3).length;
        let cPoucasVezes = answers.filter(v => v === 2).length;
        let cNunca = answers.filter(v => v === 1).length;
        
        const ctxPie = canvas.getContext('2d');
        const chartPie = new Chart(ctxPie, {
            type: 'doughnut',
            data: {
                labels: ['Sempre (4)', 'Quase sempre (3)', 'Poucas vezes (2)', 'Nunca (1)'],
                datasets: [{
                    data: [cSempre, cQuaseSempre, cPoucasVezes, cNunca],
                    backgroundColor: [
                        '#4CAF50', // Verde (Sempre)
                        '#8BC34A', // Verde Claro (Quase Sempre)
                        '#FFEB3B', // Amarelo (Poucas Vezes)
                        '#F44336'  // Vermelho (Nunca)
                    ],
                    borderWidth: 1.5,
                    borderColor: '#ffffff'
                }]
            },
            plugins: [ChartDataLabels],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw;
                                const pct = count > 0 ? ((val / count) * 100).toFixed(0) : 0;
                                return `${context.label}: ${val} votos (${pct}%)`;
                            }
                        }
                    },
                    datalabels: {
                        display: function(context) {
                            const val = context.dataset.data[context.dataIndex];
                            return val > 0; // Mostra apenas se houver votos (> 0%)
                        },
                        color: function(context) {
                            // Poucas vezes (Amarelo, index 2) usa cor escura, o resto branco
                            return context.dataIndex === 2 ? '#1F2222' : '#FFFFFF';
                        },
                        font: {
                            weight: 'bold',
                            size: 11,
                            family: 'Helvetica Neue, Helvetica, Arial, sans-serif'
                        },
                        formatter: function(value, context) {
                            const pct = count > 0 ? ((value / count) * 100).toFixed(0) : 0;
                            return `${pct}%`;
                        }
                    }
                },
                cutout: '55%'
            }
        });
        
        chartProfPizzas.push(chartPie);
    });
}

// -------------------------------------------------------------
// VISÃO 3: RAIO-X POR TURMA (DIAGNÓSTICO DE CLIMA)
// -------------------------------------------------------------
function renderVisaoTurma() {
    const respostas = getFilteredResponses(true);
    const selectTurma = document.getElementById('select-turma');
    
    // Preencher select de turmas
    const turmas = [...new Set(respostas.map(r => r.turma_declarada))].sort();
    const prevSelection = selectTurma.value;
    
    selectTurma.innerHTML = '';
    turmas.forEach(t => {
        selectTurma.innerHTML += `<option value="${t}">${t}</option>`;
    });
    
    if (prevSelection && turmas.includes(prevSelection)) {
        selectTurma.value = prevSelection;
    } else if (turmas.length > 0) {
        selectTurma.value = turmas[0];
    }
    
    const selectedTurma = selectTurma.value;
    if (!selectedTurma) return;
    
    selectTurma.onchange = renderVisaoTurma;
    
    // Filtrar dados da turma selecionada
    const turmaResponses = respostas.filter(r => r.turma_declarada === selectedTurma);
    
    // 1. KPIs da Turma
    const notasTurma = turmaResponses.flatMap(r => Object.values(r.ratings));
    document.getElementById('kpi-turma-media').innerText = normalizeScore(getAverage(notasTurma)).toFixed(2);
    document.getElementById('kpi-turma-total').innerText = turmaResponses.length.toLocaleString('pt-BR');
    
    // Identificar melhor professor na turma
    const turmaProfs = [...new Set(turmaResponses.map(r => r.professor))];
    let bestProf = 'N/A';
    let bestScore = -1;
    
    const tableBody = document.querySelector('#heatmap-table-element tbody');
    tableBody.innerHTML = '';
    
    // Atributos de cabeçalho curto para a tabela
    const attrShortNames = {
        "Didática": "Didática",
        "Apoio": "Apoio",
        "Tempo": "Tempo",
        "Avaliação": "Avaliação",
        "Clima": "Clima",
        "Respeito": "Respeito",
        "Domínio": "Domínio"
    };
    
    // Mapeamento de cor da célula baseada na nota
    function getScoreClass(score) {
        if (score === null || score === undefined || isNaN(score) || score === 0) return '';
        if (score < 5.0) return 'score-critico';
        if (score < 7.0) return 'score-regular';
        if (score <= 8.5) return 'score-bom';
        return 'score-excelente';
    }
    
    // 2. Construir Linhas do Heatmap (Professores da Turma)
    turmaProfs.forEach(prof => {
        const profRes = turmaResponses.filter(r => r.professor === prof);
        const ratingsArray = [];
        
        let rowHtml = `<tr><td class="bold">${prof}</td>`;
        
        ATRIBUTOS_OFICIAIS.forEach(attr => {
            const scores = profRes.map(r => r.ratings[attr]);
            const avg = getAverage(scores);
            const normAvg = avg > 0 ? normalizeScore(avg) : 0;
            if (avg > 0) ratingsArray.push(normAvg);
            
            const cellVal = avg > 0 ? normAvg.toFixed(2) : '-';
            const cellClass = getScoreClass(normAvg);
            rowHtml += `<td class="cell-score ${cellClass}">${cellVal}</td>`;
        });
        
        // Calcular média do professor nessa turma específica
        const profAvg = getAverage(ratingsArray);
        if (profAvg > bestScore) {
            bestScore = profAvg;
            bestProf = prof;
        }
        
        const avgClass = getScoreClass(profAvg);
        rowHtml += `<td class="cell-score ${avgClass} bold">${profAvg > 0 ? profAvg.toFixed(2) : '-'}</td></tr>`;
        tableBody.innerHTML += rowHtml;
    });
    
    document.getElementById('kpi-turma-destaque-prof').innerText = bestProf.split(' ')[0];
    
    // Atributo Mais Forte da Turma
    let bestAttr = 'N/A';
    let maxAttrScore = -1;
    ATRIBUTOS_OFICIAIS.forEach(attr => {
        const scores = turmaResponses.map(r => r.ratings[attr]);
        const avg = getAverage(scores);
        if (avg > maxAttrScore) {
            maxAttrScore = avg;
            bestAttr = attrShortNames[attr];
        }
    });
    document.getElementById('kpi-turma-destaque-attr').innerText = bestAttr;
}

// -------------------------------------------------------------
// VISÃO 4: PAINEL QUALITATIVO (STUDENT INSIGHTS)
// -------------------------------------------------------------
function renderVisaoQualitativo() {
    const selectProf = document.getElementById('select-qual-prof');
    const selectTurma = document.getElementById('select-qual-turma');
    const inputSearch = document.getElementById('search-comments');
    const commentsCount = document.getElementById('comments-count');
    const tableBody = document.querySelector('#comments-table-element tbody');
    
    // PreencherDropdowns se estiverem vazios
    if (selectProf.options.length <= 1) {
        const profs = rawData.professores.sort();
        selectProf.innerHTML = '';
        if (currentUserProfile && currentUserProfile.role === 'professor') {
            selectProf.innerHTML += `<option value="">Todas as minhas matérias</option>`;
        } else {
            selectProf.innerHTML += `<option value="">Todos os Professores</option>`;
        }
        profs.forEach(p => {
            selectProf.innerHTML += `<option value="${p}">${p}</option>`;
        });
    }
    
    if (selectTurma.options.length <= 1) {
        const turmas = rawData.turmas.sort();
        turmas.forEach(t => {
            selectTurma.innerHTML += `<option value="${t}">${t}</option>`;
        });
    }
    
    // Lógica de filtro e renderização de comentários
    const filterAndRender = () => {
        const prof = selectProf.value;
        const turma = selectTurma.value;
        const query = inputSearch.value.trim().toLowerCase();
        
        // Filtrar as respostas que tenham comentários
        let filtered = rawData.respostas.filter(r => r.comentario !== null && r.comentario !== undefined && r.comentario !== '');
        
        if (prof) {
            filtered = filtered.filter(r => r.professor === prof);
        }
        if (turma) {
            filtered = filtered.filter(r => r.turma_declarada === turma);
        }
        if (query) {
            // Filtrar comentários que contenham o termo de busca, ou que o professor/turma corresponda
            filtered = filtered.filter(r => {
                const textMatch = r.comentario.toLowerCase().includes(query);
                const profMatch = r.professor.toLowerCase().includes(query);
                return textMatch || profMatch;
            });
        }
        
        // Limitar a exibição a no máximo 300 comentários para manter o scroll leve e rápido
        const limit = 300;
        const displayList = filtered.slice(0, limit);
        
        // Atualizar contador de forma inteligente
        if (filtered.length > limit) {
            commentsCount.innerText = `Exibindo ${limit} de ${filtered.length} comentários (use a busca ou filtros para refinar)`;
        } else {
            commentsCount.innerText = `Exibindo ${filtered.length} comentário${filtered.length !== 1 ? 's' : ''}`;
        }
        
        // Renderizar linhas de uma só vez (Performance Batching)
        tableBody.innerHTML = '';
        if (filtered.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="3" style="text-align: center; color: var(--fg-3); font-style: italic; padding: var(--space-5);">Nenhum comentário encontrado para os filtros selecionados.</td></tr>`;
            return;
        }
        
        const htmlRows = [];
        displayList.forEach(r => {
            htmlRows.push(`
                <tr>
                    <td class="bold">${escapeHTML(r.turma_declarada)}</td>
                    <td><span class="badge u-graphite-bg" style="padding: var(--space-1) var(--space-2); color: white; font-size: 11px;">${escapeHTML(r.professor)}</span></td>
                    <td class="comment-text">${escapeHTML(r.comentario)}</td>
                </tr>
            `);
        });
        tableBody.innerHTML = htmlRows.join('');
    };
    
    // Configurar listeners se ainda não configurados
    selectProf.onchange = filterAndRender;
    selectTurma.onchange = filterAndRender;
    inputSearch.oninput = filterAndRender;
    
    // Rodar filtro inicial
    filterAndRender();
}

// -------------------------------------------------------------
// VISÃO 5: MAPEAMENTO ATIVO (TELA ADMINISTRATIVA)
// -------------------------------------------------------------
function renderVisaoMapeamento() {
    const selectMapTurma = document.getElementById('select-map-turma');
    const tableBody = document.querySelector('#mapping-table-element tbody');
    const btnSave = document.getElementById('btn-save-mapping');
    
    // Preencher select de turmas para mapear
    const turmasMapeamento = Object.keys(mappingData).sort();
    const prevSelection = selectMapTurma.value;
    
    selectMapTurma.innerHTML = '';
    turmasMapeamento.forEach(t => {
        selectMapTurma.innerHTML += `<option value="${t}">${t}</option>`;
    });
    
    if (prevSelection && turmasMapeamento.includes(prevSelection)) {
        selectMapTurma.value = prevSelection;
    } else if (turmasMapeamento.length > 0) {
        selectMapTurma.value = turmasMapeamento[0];
    }
    
    const selectedTurma = selectMapTurma.value;
    if (!selectedTurma) return;
    
    selectMapTurma.onchange = renderVisaoMapeamento;
    
    const blocks = mappingData[selectedTurma] || [];
    
    // Preencher Tabela de Mapeamento
    tableBody.innerHTML = '';
    blocks.forEach((b, idx) => {
        tableBody.innerHTML += `
            <tr data-block-index="${b.block_index}">
                <td class="bold">Professor Bloco ${b.block_index + 1}</td>
                <td>Coluna ${b.start_column_index}</td>
                <td>
                    <input type="text" class="input-map-name" value="${escapeHTML(b.teacher_name)}" style="padding: var(--space-1) var(--space-2); width: 100%;">
                </td>
                <td>
                    <input type="text" class="input-map-discipline" value="${escapeHTML(b.discipline)}" style="padding: var(--space-1) var(--space-2); width: 100%;">
                </td>
                <td>
                    <input type="text" class="input-map-classes" value="${escapeHTML(b.turmas ? b.turmas.join(', ') : '')}" placeholder="Ex: 1ª série A, 1ª série C" style="padding: var(--space-1) var(--space-2); width: 100%;">
                </td>
            </tr>
        `;
    });
    
    // Configurar Evento de Salvar Alterações
    btnSave.onclick = async () => {
        // 1. Coletar os valores da tabela
        const rows = tableBody.querySelectorAll('tr');
        const updatedBlocks = [];
        
        rows.forEach(row => {
            const bIdx = parseInt(row.getAttribute('data-block-index'));
            const teacherName = row.querySelector('.input-map-name').value.trim();
            const discipline = row.querySelector('.input-map-discipline').value.trim();
            const classesInput = row.querySelector('.input-map-classes').value.trim();
            
            const turmas = classesInput ? classesInput.split(',').map(s => s.trim()).filter(s => s.length > 0) : [];
            
            // Localizar bloco correspondente original
            const originalBlock = blocks.find(b => b.block_index === bIdx);
            if (originalBlock) {
                updatedBlocks.push({
                    block_index: bIdx,
                    start_column_index: originalBlock.start_column_index,
                    teacher_name: teacherName,
                    discipline: discipline,
                    turmas: turmas.length > 0 ? turmas : undefined
                });
            }
        });
        
        // 2. Atualizar no nosso mappingData global do cliente
        mappingData[selectedTurma] = updatedBlocks;
        
        btnSave.disabled = true;
        btnSave.innerText = "SALVANDO...";
        
        if (supabaseClient) {
            try {
                // Preparar dados para o Supabase
                const dbBlocks = updatedBlocks.map(b => ({
                    turma_pasta: selectedTurma,
                    block_index: b.block_index,
                    start_column_index: b.start_column_index,
                    teacher_name: b.teacher_name,
                    discipline: b.discipline,
                    turmas: b.turmas || []
                }));
                
                const { error } = await supabaseClient
                    .from('mapeamento')
                    .upsert(dbBlocks);
                    
                if (error) throw error;
                
                alert("Mapeamento atualizado no Supabase com sucesso!");
                await loadData(true);
                renderVisaoMapeamento();
            } catch (err) {
                console.error("Erro ao salvar mapeamento no Supabase:", err);
                alert("Erro ao salvar mapeamento no Supabase: " + (err.message || err));
            } finally {
                btnSave.disabled = false;
                btnSave.innerText = "SALVAR ALTERAÇÕES";
            }
            return;
        }
        
        // Fallback local legado
        try {
            const response = await fetch('/api/save-mapping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(mappingData)
            });
            
            const resData = await response.json();
            if (resData.status === 'success') {
                alert("Mapeamento atualizado e dados consolidados com sucesso!");
                await loadData(false);
                renderVisaoMapeamento();
            } else {
                alert("Erro ao salvar mapeamento: " + resData.message);
            }
        } catch (err) {
            console.error("Erro no salvamento do mapeamento:", err);
            alert("Erro de conexão ao salvar as alterações no mapeamento.");
        } finally {
            btnSave.disabled = false;
            btnSave.innerText = "SALVAR ALTERAÇÕES";
        }
    };
}

/* Inicialização e Controle de Autenticação */
console.log("[DEBUG] Bloco de inicialização final executado. document.readyState =", document.readyState);
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log("[DEBUG] Evento DOMContentLoaded disparado!");
        checkAuthAndInit();
    });
} else {
    checkAuthAndInit();
}
