"""
Telegram Subscriber Bot Service
Allows individual users to start the bot, pick categories, and manage alert preferences.
Handles long-polling in a background thread without blocking the scraper.
"""

import os
import time
import threading
import requests
import html
from typing import Dict, List, Tuple
from ..utils.logger import logger
from ..database import (
    get_or_create_subscriber,
    toggle_subscriber_category,
    toggle_subscriber_active,
    get_subscribers_for_category
)

AVAILABLE_CATEGORIES: List[Tuple[str, str]] = [
    ("Celulares", "📱 Celulares"),
    ("Informática", "💻 Informática"),
    ("Eletrônicos", "📺 Eletrônicos"),
    ("Games", "🎮 Games"),
    ("Casa", "🏠 Casa"),
    ("Bebidas", "🍷 Bebidas"),
    ("Beleza", "💄 Beleza"),
    ("Moda", "👟 Moda"),
    ("Ferramentas", "🛠️ Ferramentas"),
    ("Automotivo", "🚗 Automotivo"),
    ("Outros", "📦 Outros")
]

def build_menu(chat_id: str, first_name: str = None) -> Tuple[str, dict]:
    """
    Builds the interactive menu text and inline keyboard for a subscriber.
    """
    sub = get_or_create_subscriber(chat_id, first_name=first_name)
    current_cats = [c.strip() for c in sub.categories.split(',') if c.strip() and c.strip() != 'Nenhuma']
    is_all = 'Todas' in current_cats
    
    status_emoji = "🔔 <b>Alertas ATIVOS</b>" if sub.is_active else "🛑 <b>Alertas PAUSADOS</b>"
    greeting = f"Olá, <b>{html.escape(first_name or 'amigo')}</b>!" if first_name else "Olá!"
    
    if is_all:
        selected_text = "✨ <b>Todas as categorias ativadas</b>"
    elif current_cats:
        selected_text = f"🎯 <b>Categorias ativas:</b> {', '.join(current_cats)}"
    else:
        selected_text = "⚠️ <i>Nenhuma categoria selecionada. Toque nos botões abaixo para escolher.</i>"

    text = (
        f"👋 {greeting} Seja bem-vindo ao <b>PromoBot Ofertas</b>!\n\n"
        f"Status: {status_emoji}\n"
        f"{selected_text}\n\n"
        f"🎯 <b>Selecione as categorias que deseja receber:</b>\n"
    )
    
    # Text summary of preferences
    for cat_key, cat_label in AVAILABLE_CATEGORIES:
        checked = "✅" if is_all or cat_key in current_cats else "⬜"
        text += f"{checked} {cat_label}\n"
        
    text += "\n<i>Toque nos botões abaixo para marcar ou desmarcar:</i>"
    
    # Inline Keyboard
    keyboard = []
    row = []
    for cat_key, cat_label in AVAILABLE_CATEGORIES:
        is_checked = is_all or cat_key in current_cats
        mark = "✅" if is_checked else "⬜"
        row.append({
            "text": f"{mark} {cat_label}",
            "callback_data": f"cat_{cat_key}"
        })
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # All / Clear Buttons
    all_mark = "✅" if is_all else "⬜"
    keyboard.append([
        {"text": f"{all_mark} ✨ Todas", "callback_data": "cat_Todas"},
        {"text": "❌ Limpar", "callback_data": "cat_Limpar"}
    ])
    
    # Pause/Resume Button
    if sub.is_active:
        keyboard.append([{"text": "🛑 Pausar Notificações", "callback_data": "toggle_active"}])
    else:
        keyboard.append([{"text": "▶️ Reativar Notificações", "callback_data": "toggle_active"}])
        
    return text, {"inline_keyboard": keyboard}


def handle_callback_query(bot_token: str, callback_query: dict):
    """
    Handles inline button clicks from users.
    """
    try:
        cq_id = callback_query.get("id")
        data = callback_query.get("data", "")
        from_user = callback_query.get("from", {})
        chat_id = str(from_user.get("id"))
        first_name = from_user.get("first_name", "")
        message = callback_query.get("message", {})
        message_id = message.get("message_id")
        
        # 1. Process Action
        toast_text = "Preferência atualizada!"
        if data.startswith("cat_"):
            category = data.replace("cat_", "")
            sub = toggle_subscriber_category(chat_id, category)
            if category == "Limpar":
                toast_text = "Categorias limpas!"
            elif category == "Todas":
                toast_text = "Todas as categorias ativadas!" if sub.categories == "Todas" else "Categorias desmarcadas!"
            else:
                is_now_selected = sub.categories == "Todas" or category in sub.categories
                toast_text = f"{'✅ Ativado' if is_now_selected else '⬜ Desativado'}: {category}"
        elif data == "toggle_active":
            sub = toggle_subscriber_active(chat_id)
            toast_text = "Alertas ativados!" if sub.is_active else "Alertas pausados!"

            
        # 2. Answer Callback Query (removes loading spinner on Telegram)
        base_url = f"https://api.telegram.org/bot{bot_token}"
        try:
            requests.post(
                f"{base_url}/answerCallbackQuery",
                json={"callback_query_id": cq_id, "text": toast_text},
                timeout=5
            )
        except Exception:
            pass
            
        # 3. Edit Message with updated buttons
        new_text, new_markup = build_menu(chat_id, first_name=first_name)
        requests.post(
            f"{base_url}/editMessageText",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": new_text,
                "parse_mode": "HTML",
                "reply_markup": new_markup
            },
            timeout=8
        )
    except Exception as e:
        logger.error(f"Error handling Telegram callback: {e}")


def handle_message(bot_token: str, msg: dict):
    """
    Handles regular text messages (/start, /menu, /categorias).
    """
    try:
        chat = msg.get("chat", {})
        chat_id = str(chat.get("id"))
        from_user = msg.get("from", {})
        first_name = from_user.get("first_name", "")
        username = from_user.get("username", "")
        text = msg.get("text", "").strip().lower()
        
        # We only handle private chats for individual subscriptions
        if chat.get("type") != "private":
            return
            
        # Register subscriber
        get_or_create_subscriber(chat_id, username=username, first_name=first_name)
        
        if text.startswith("/start") or text.startswith("/menu") or text.startswith("/categoria") or text.startswith("/ajuda"):
            base_url = f"https://api.telegram.org/bot{bot_token}"
            menu_text, reply_markup = build_menu(chat_id, first_name=first_name)
            
            requests.post(
                f"{base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": menu_text,
                    "parse_mode": "HTML",
                    "reply_markup": reply_markup
                },
                timeout=10
            )
            logger.info(f"Sent interactive menu to subscriber {first_name} ({chat_id})")
    except Exception as e:
        logger.error(f"Error handling Telegram message: {e}")


def run_telegram_listener():
    """
    Background worker that continuously polls for incoming /start commands and button clicks.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token or bot_token == "seu_token":
        logger.warning("TELEGRAM_BOT_TOKEN not configured. Subscriber bot listener disabled.")
        return
        
    logger.info("Telegram Subscriber Listener started (polling for /start and category choices)...")
    offset = None
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    while True:
        try:
            params = {"timeout": 20, "limit": 20}
            if offset:
                params["offset"] = offset
                
            resp = requests.get(f"{base_url}/getUpdates", params=params, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "callback_query" in update:
                        handle_callback_query(bot_token, update["callback_query"])
                    elif "message" in update:
                        handle_message(bot_token, update["message"])
            else:
                time.sleep(2)
        except requests.exceptions.RequestException:
            time.sleep(5)
        except Exception as e:
            logger.error(f"Telegram listener error: {e}")
            time.sleep(3)


def start_subscriber_listener_thread():
    """Starts the listener thread in background."""
    t = threading.Thread(target=run_telegram_listener, daemon=True, name="TelegramListenerThread")
    t.start()
    return t
