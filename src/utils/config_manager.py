
import json
import os
import time

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG = {
    "interval_minutes": 30,
    "force_run": False,
    "last_run_timestamp": 0
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def should_run():
    config = load_config()
    
    # 1. Force run
    if config.get('force_run'):
        config['force_run'] = False
        save_config(config)
        return True
    
    # 2. Check interval
    last_run = config.get('last_run_timestamp', 0)
    interval_minutes = config.get('interval_minutes', 30)
    
    # Se intervalo for invalido (<=0), assumir 30min
    if interval_minutes <= 0: interval_minutes = 30
    
    elapsed_minutes = (time.time() - last_run) / 60
    
    if elapsed_minutes >= interval_minutes:
        return True
        
    return False

def update_last_run():
    config = load_config()
    config['last_run_timestamp'] = time.time()
    save_config(config)

def set_force_run():
    config = load_config()
    config['force_run'] = True
    save_config(config)

def set_interval(minutes):
    config = load_config()
    config['interval_minutes'] = int(minutes)
    save_config(config)
