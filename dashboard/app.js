// API Base URL
const API_URL = 'http://localhost:5000';

// Refresh data every 30 seconds
let refreshInterval;
let currentCategory = 'Todas';
let currentStore = 'Todas';

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCategories().then(() => {
        loadDashboard();
    });
    startAutoRefresh();

    // Store Checkboxes
    const storeBtns = document.querySelectorAll('.store-btn');
    storeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            storeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentStore = btn.dataset.store;
            loadDeals();
        });
    });

    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadDashboard();
    });

    // Save Interval
    document.getElementById('save-interval-btn').addEventListener('click', async () => {
        const interval = document.getElementById('interval-input').value;
        try {
            const res = await fetch(`${API_URL}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval })
            });
            if (res.ok) alert('✅ Intervalo salvo com sucesso!');
            else alert('❌ Erro ao salvar intervalo.');
        } catch (e) {
            console.error(e);
            alert('❌ Erro de conexão.');
        }
    });

    // Trigger Run
    document.getElementById('trigger-btn').addEventListener('click', async () => {
        if (!confirm('Deseja iniciar a busca de ofertas agora?')) return;

        try {
            const res = await fetch(`${API_URL}/trigger`, { method: 'POST' });
            if (res.ok) {
                alert('🚀 Bot iniciado! As ofertas aparecerão em breve.');
                // Refresh stats immediately to see "Running..." if we had that status
            }
            else alert('❌ Erro ao iniciar bot.');
        } catch (e) {
            console.error(e);
            alert('❌ Erro de conexão.');
        }
    });
    // Clear Deals
    document.getElementById('clear-deals-btn').addEventListener('click', async () => {
        if (!confirm('⚠️ ATENÇÃO: Isso excluirá TODAS as ofertas do banco de dados.\nDeseja continuar?')) return;

        try {
            const res = await fetch(`${API_URL}/clear-deals`, { method: 'POST' });
            if (res.ok) {
                alert('🗑️ Todas as ofertas foram removidas.');
                loadDashboard();
            }
            else alert('❌ Erro ao limpar ofertas.');
        } catch (e) {
            console.error(e);
            alert('❌ Erro de conexão.');
        }
    });

});

async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const categories = await response.json();

        const container = document.getElementById('categories-bar');

        // Always add 'Todas' first
        let html = `<button class="category-btn ${currentCategory === 'Todas' ? 'active' : ''}" data-category="Todas">Todas</button>`;

        // Add other categories
        categories.forEach(cat => {
            if (cat && cat !== 'Todas') {
                html += `<button class="category-btn ${currentCategory === cat ? 'active' : ''}" data-category="${cat}">${cat}</button>`;
            }
        });

        container.innerHTML = html;

        // Add listeners
        setupCategoryListeners();

    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function setupCategoryListeners() {
    const buttons = document.querySelectorAll('.category-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update UI
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Update Data
            currentCategory = btn.dataset.category;
            loadDeals();
        });
    });
}

function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadDashboard();
    }, 30000); // 30 seconds
}

async function loadDashboard() {
    try {
        await Promise.all([
            loadStats(),
            loadDeals(),
            loadConfig(),
            loadCategories() // Update categories dynamically
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const stats = await response.json();

        document.getElementById('total-deals').textContent = stats.total_deals;
        document.getElementById('sent-deals').textContent = stats.sent_deals;
        document.getElementById('total-savings').textContent = `R$ ${stats.total_savings.toFixed(2)}`;
        document.getElementById('avg-discount').textContent = `${stats.avg_discount}%`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadDeals() {
    try {
        let url = `${API_URL}/deals`;
        let params = [];

        if (currentCategory !== 'Todas') params.push(`category=${encodeURIComponent(currentCategory)}`);
        if (currentStore !== 'Todas') params.push(`store=${encodeURIComponent(currentStore)}`);

        if (params.length > 0) {
            url += '?' + params.join('&');
        }

        const response = await fetch(url);
        const deals = await response.json();

        const dealsList = document.getElementById('deals-list');

        if (deals.length === 0) {
            dealsList.innerHTML = `<div class="loading">Nenhuma oferta encontrada em ${currentCategory}.</div>`;
            return;
        }

        dealsList.innerHTML = deals.map(deal => createDealCard(deal)).join('');
    } catch (error) {
        console.error('Error loading deals:', error);
        document.getElementById('deals-list').innerHTML =
            '<div class="loading">Erro ao carregar ofertas. Verifique se a API está rodando.</div>';
    }
}

function createDealCard(deal) {
    const discount = deal.old_price && deal.old_price > deal.price
        ? Math.round(((deal.old_price - deal.price) / deal.old_price) * 100)
        : 0;

    const imageUrl = deal.image_url || 'https://via.placeholder.com/100';
    const affiliateUrl = deal.affiliate_url || deal.original_url;
    // Safe URL handling
    const safeAffiliateUrl = affiliateUrl.replace(/"/g, '&quot;').replace(/'/g, '&#39;');

    // Status badges
    const telegramBadge = deal.sent_to_telegram
        ? '<span class="status-badge telegram-sent">📱 Enviado ao Telegram</span>'
        : '<span class="status-badge telegram-not-sent">🔕 Modo Debug</span>';

    const affiliateBadge = deal.has_affiliate
        ? '<span class="status-badge affiliate-yes">🔗 Link Afiliado</span>'
        : '<span class="status-badge affiliate-no">🔗 Link Original</span>';

    return `
        <div class="deal-card">
            <img src="${imageUrl}" alt="${deal.title}" class="deal-image" onerror="this.src='https://via.placeholder.com/100'">
            <div class="deal-info">
                <h3>${deal.title}</h3>
                <div class="deal-prices">
                    ${deal.old_price ? `<span class="old-price">R$ ${deal.old_price.toFixed(2)}</span>` : ''}
                    <span class="new-price">R$ ${deal.price.toFixed(2)}</span>
                    ${discount > 0 ? `<span class="discount-badge">${discount}% OFF</span>` : ''}
                </div>
                <div class="deal-meta">
                    <span class="category-tag">📂 ${deal.category || 'Outros'}</span>
                    <span>📅 ${formatDate(deal.sent_at)}</span>
                </div>
                <div class="deal-status">
                    ${telegramBadge}
                    ${affiliateBadge}
                </div>
            </div>
            <div class="deal-actions">
                <a href="${affiliateUrl}" target="_blank" class="btn-link">🔗 Ver Oferta</a>
                <button class="btn-copy" data-url="${safeAffiliateUrl}">📋 Copiar Link</button>
            </div>
        </div>
    `;
}

// Add global event listener for copy buttons
document.addEventListener('click', function (e) {
    if (e.target && e.target.classList.contains('btn-copy')) {
        const url = e.target.getAttribute('data-url');
        if (url) {
            copyLink(url);
        }
    }
});

function copyLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        // Show temporary notification
        const notification = document.createElement('div');
        notification.className = 'copy-notification';
        notification.textContent = '✅ Link copiado!';
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 2000);
    });
}

async function loadConfig() {
    try {
        const response = await fetch(`${API_URL}/config`);
        const config = await response.json();

        // Debug Mode
        const debugBadge = document.getElementById('debug-mode');
        debugBadge.textContent = config.debug_mode ? 'Ativo' : 'Desativado';
        debugBadge.className = `badge ${config.debug_mode ? 'warning' : 'success'}`;

        // Telegram Status
        const telegramBadge = document.getElementById('telegram-status');
        telegramBadge.textContent = config.telegram_configured ? 'Configurado' : 'Não Configurado';
        telegramBadge.className = `badge ${config.telegram_configured ? 'success' : 'danger'}`;

        // AI Status
        const aiBadge = document.getElementById('ai-status');
        aiBadge.textContent = config.ai_configured ? 'Ativo' : 'Não Configurado';
        aiBadge.className = `badge ${config.ai_configured ? 'success' : 'danger'}`;

        // Last Run
        document.getElementById('last-run').textContent = config.last_run
            ? formatDate(config.last_run)
            : 'Nunca';
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.max(0, now - date); // Ensure non-negative

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (seconds < 60) return `Há ${seconds}s`;
    if (minutes < 60) return `Há ${minutes} min`;
    if (hours < 24) {
        const remainingMinutes = minutes % 60;
        return `Há ${hours}h ${remainingMinutes}m`;
    }
    if (days < 7) return `Há ${days} dias`;

    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}
