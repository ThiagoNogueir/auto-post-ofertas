const API_URL = 'http://localhost:8000';

// Load configuration on page load
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
});

async function loadConfig() {
    try {
        const response = await fetch(`${API_URL}/groups-config`);
        const config = await response.json();

        // General settings
        document.getElementById('routing-enabled').checked = config.category_routing?.enabled || false;
        document.getElementById('send-telegram').checked = config.category_routing?.send_to_telegram || false;
        document.getElementById('send-whatsapp').checked = config.category_routing?.send_to_whatsapp || false;

        // Telegram groups
        document.getElementById('telegram-default').value = config.telegram_groups?.default || '';
        document.getElementById('telegram-celulares').value = config.telegram_groups?.Celulares || '';
        document.getElementById('telegram-eletronicos').value = config.telegram_groups?.Eletrônicos || '';
        document.getElementById('telegram-informatica').value = config.telegram_groups?.Informática || '';
        document.getElementById('telegram-casa').value = config.telegram_groups?.Casa || '';

        // WhatsApp groups
        document.getElementById('whatsapp-default').value = config.whatsapp_groups?.default || '';
        document.getElementById('whatsapp-celulares').value = config.whatsapp_groups?.Celulares || '';
        document.getElementById('whatsapp-eletronicos').value = config.whatsapp_groups?.Eletrônicos || '';
        document.getElementById('whatsapp-informatica').value = config.whatsapp_groups?.Informática || '';
        document.getElementById('whatsapp-casa').value = config.whatsapp_groups?.Casa || '';

    } catch (error) {
        console.error('Error loading config:', error);
        alert('❌ Erro ao carregar configurações');
    }
}

async function saveConfig() {
    try {
        const config = {
            category_routing: {
                enabled: document.getElementById('routing-enabled').checked,
                send_to_telegram: document.getElementById('send-telegram').checked,
                send_to_whatsapp: document.getElementById('send-whatsapp').checked
            },
            telegram_groups: {
                default: document.getElementById('telegram-default').value,
                Celulares: document.getElementById('telegram-celulares').value,
                Eletrônicos: document.getElementById('telegram-eletronicos').value,
                Informática: document.getElementById('telegram-informatica').value,
                Casa: document.getElementById('telegram-casa').value
            },
            whatsapp_groups: {
                default: document.getElementById('whatsapp-default').value,
                Celulares: document.getElementById('whatsapp-celulares').value,
                Eletrônicos: document.getElementById('whatsapp-eletronicos').value,
                Informática: document.getElementById('whatsapp-informatica').value,
                Casa: document.getElementById('whatsapp-casa').value
            }
        };

        const response = await fetch(`${API_URL}/groups-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        if (response.ok) {
            alert('✅ Configurações salvas com sucesso!');
        } else {
            alert('❌ Erro ao salvar configurações');
        }

    } catch (error) {
        console.error('Error saving config:', error);
        alert('❌ Erro ao salvar configurações');
    }
}

async function testWhatsApp(category) {
    const inputId = `whatsapp-${category}`;
    const groupId = document.getElementById(inputId).value;

    if (!groupId) {
        alert('⚠️ Por favor, preencha o ID do grupo primeiro');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/test-whatsapp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ group_id: groupId })
        });

        const result = await response.json();

        if (response.ok) {
            alert('✅ Mensagem de teste enviada com sucesso! Verifique o grupo do WhatsApp.');
        } else {
            alert(`❌ Erro: ${result.error}`);
        }

    } catch (error) {
        console.error('Error testing WhatsApp:', error);
        alert('❌ Erro ao enviar mensagem de teste');
    }
}
