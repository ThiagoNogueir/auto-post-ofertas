"""
API REST para o Dashboard do PromoBot.
Serve estatísticas e dados das ofertas.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database.models import Deal, db, init_database

app = Flask(__name__, static_folder='../dashboard', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Initialize database
init_database()


@app.route('/')
def index():
    """Serve the dashboard."""
    return app.send_static_file('index.html')


@app.route('/stats')
def get_stats():
    """Get statistics about deals."""
    try:
        total_deals = Deal.select().count()
        
        # Calculate savings and average discount
        deals = Deal.select()
        total_savings = 0
        total_discount = 0
        count_with_discount = 0
        
        for deal in deals:
            # Try to calculate savings from title or assume 20% average
            # In a real scenario, you'd store old_price in the database
            price = float(deal.price)  # Convert Decimal to float
            estimated_old_price = price * 1.3  # Assume 30% discount average
            savings = estimated_old_price - price
            total_savings += savings
            
            discount = ((estimated_old_price - price) / estimated_old_price) * 100
            total_discount += discount
            count_with_discount += 1
        
        avg_discount = int(total_discount / count_with_discount) if count_with_discount > 0 else 0
        
        return jsonify({
            'total_deals': total_deals,
            'sent_deals': total_deals,  # All deals in DB were sent
            'total_savings': float(total_savings),
            'avg_discount': avg_discount
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/deals')
def get_deals():
    """Get list of deals."""
    category = request.args.get('category')
    store = request.args.get('store')
    
    try:
        query = Deal.select().order_by(Deal.sent_at.desc()).limit(50)
        
        if category and category != 'Todas':
            query = query.where(Deal.category == category)
            
        if store and store != 'Todas':
            query = query.where(Deal.store == store)
            
        deals = query
        
        deals_list = []
        for deal in deals:
            try:
                # Safe type conversion
                price = float(deal.price) if deal.price else 0.0
                old_price = price * 1.3
                
                # Handle dates - convert to ISO format
                if deal.sent_at:
                    try:
                        sent_at = deal.sent_at.isoformat()
                    except:
                        sent_at = str(deal.sent_at)
                else:
                    sent_at = datetime.now().isoformat()
                
                # Check config
                debug_mode = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
                telegram_configured = bool(os.getenv('TELEGRAM_BOT_TOKEN')) and os.getenv('TELEGRAM_BOT_TOKEN') != 'seu_token'
                sent_to_telegram = not debug_mode and telegram_configured
                
                # Clean URLs
                original_url = str(deal.original_url).strip().strip('"').strip("'")
                affiliate_url = str(deal.affiliate_url or deal.original_url).strip().strip('"').strip("'")
                
                deals_list.append({
                    'id': deal.id,
                    'title': str(deal.title),
                    'price': price,
                    'old_price': old_price,
                    'original_url': original_url,
                    'affiliate_url': affiliate_url,
                    'image_url': deal.image_url,
                    'category': getattr(deal, 'category', 'Outros'),
                    'store': getattr(deal, 'store', 'Outros'),
                    'sent_at': sent_at,
                    'sent_to_telegram': sent_to_telegram,
                    'has_affiliate': bool(deal.affiliate_url)
                })
            except Exception as e:
                print(f"Error processing deal {deal.id}: {e}")
                continue
        
        return jsonify(deals_list)
    except Exception as e:
        print(f"Critical error in /deals: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/categories')
def get_categories():
    """Get list of distinct categories."""
    try:
        # Get distinct categories that are not null/empty
        categories_query = Deal.select(Deal.category).distinct().order_by(Deal.category)
        
        categories = []
        for c in categories_query:
            if c.category:
                categories.append(c.category)
                
        return jsonify(categories)
    except Exception as e:
        print(f"Error getting categories: {e}")
        return jsonify([])


@app.route('/config')
def get_config():
    """Get bot configuration status."""
    try:
        debug_mode = os.getenv('DEBUG_MODE', 'True').lower() == 'true'
        telegram_configured = bool(os.getenv('TELEGRAM_BOT_TOKEN')) and os.getenv('TELEGRAM_BOT_TOKEN') != 'seu_token'
        ai_configured = bool(os.getenv('GROQ_API_KEY')) and os.getenv('GROQ_API_KEY') != 'sua_chave_groq_aqui'
        
        # Get last deal time as last run
        last_deal = Deal.select().order_by(Deal.sent_at.desc()).first()
        last_run = last_deal.sent_at.isoformat() if last_deal else None
        
        return jsonify({
            'debug_mode': debug_mode,
            'telegram_configured': telegram_configured,
            'ai_configured': ai_configured,
            'last_run': last_run
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/settings', methods=['POST'])
def update_settings():
    """Update bot settings (interval)."""
    try:
        data = request.json
        interval = data.get('interval')
        
        if interval:
            import json
            config_file = 'config.json'
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {"interval_minutes": 30, "force_run": False}
            
            config['interval_minutes'] = int(interval)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return jsonify({'status': 'success', 'message': f'Interval updated to {interval} minutes'})
            
        return jsonify({'error': 'Missing interval parameter'}), 400
    except Exception as e:
        print(f"Error in /settings: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/trigger', methods=['POST'])
def trigger_run():
    """Force run the bot immediately."""
    try:
        import json
        config_file = 'config.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {"interval_minutes": 30, "force_run": False}
        
        config['force_run'] = True
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return jsonify({'status': 'success', 'message': 'Job triggered successfully'})
    except Exception as e:
        print(f"Error in /trigger: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-deals', methods=['POST'])
def clear_deals():
    """Clear all deals from database."""
    try:
        query = Deal.delete()
        count = query.execute()
        return jsonify({'status': 'success', 'message': f'Deleted {count} deals'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups-config', methods=['GET'])
def get_groups_config():
    """Get groups configuration"""
    try:
        import json
        config_file = 'groups_config.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {
                "telegram_groups": {"default": ""},
                "whatsapp_groups": {"default": ""},
                "category_routing": {"enabled": True, "send_to_telegram": True, "send_to_whatsapp": False}
            }
        
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/groups-config', methods=['POST'])
def update_groups_config():
    """Update groups configuration"""
    try:
        import json
        config_file = 'groups_config.json'
        data = request.json
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/urls', methods=['GET'])
def get_urls():
    """Get monitored URLs configuration."""
    try:
        urls_config_file = os.path.join(os.path.dirname(__file__), '..', 'urls_config.json')
        
        # Create file with defaults if it doesn't exist
        if not os.path.exists(urls_config_file):
            default_config = {
                "urls_to_monitor": [
                    "https://lista.mercadolivre.com.br/celulares-telefones/_Orden_sold_quantity",
                    "https://lista.mercadolivre.com.br/computadores/_Orden_sold_quantity"
                ]
            }
            with open(urls_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        with open(urls_config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/urls', methods=['POST'])
def update_urls():
    """Update monitored URLs configuration."""
    try:
        # Use absolute path
        urls_config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'urls_config.json'))
        data = request.json
        
        print(f"Saving URLs to: {urls_config_file}")
        print(f"Data received: {data}")
        
        # Validate data
        if not data or 'urls_to_monitor' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        with open(urls_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"URLs saved successfully!")
        return jsonify({'status': 'success', 'message': 'URLs updated successfully'})
    except Exception as e:
        print(f"Error saving URLs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
