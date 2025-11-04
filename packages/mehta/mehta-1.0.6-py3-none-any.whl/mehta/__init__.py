from .ext import telegram
import sys
import os
import importlib.util
import re

__all__ = ["telegram"]

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command.startswith('run:'):
            parts = command[4:].split()
            filename = parts[0]
            
            token = None
            for part in parts[1:]:
                if part.startswith('token='):
                    token = part[6:]
            
            run_bot_file(filename, token)

def run_bot_file(filename, token=None):
    try:
        if not filename.endswith('.py'):
            filename += '.py'
        
        if not os.path.exists(filename):
            print(f"Error: File {filename} not found")
            return
        
        spec = importlib.util.spec_from_file_location("bot_module", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, 'bot') and isinstance(module.bot, telegram):
            if token:
                module.bot.run(token)
            else:
                print("No token provided")
        else:
            print("No bot instance found in file")
                
    except Exception as e:
        print(f"Error: {e}")