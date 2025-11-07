import os
import sys
import traceback
from telethon import TelegramClient
from telethon.tl.types import Message

class telethon:
    def __init__(self):
        self.client = None
        self.commandhandlers = {}
        self.messagehandler = None
        
    def commands(self, commandlist):
        def decorator(func):
            for cmd in commandlist:
                self.commandhandlers[cmd] = func
            return func
        return decorator
    
    def message(self):
        def decorator(func):
            self.messagehandler = func
            return func
        return decorator
    
    def run(self, id, hash):
        try:
            self.client = TelegramClient('session', id, hash)
            
            @self.client.on(Message)
            async def handler(event):
                if event.text and event.text.startswith('/'):
                    command = event.text[1:].split()[0]
                    if command in self.commandhandlers:
                        result = self.commandhandlers[command](event)
                        await self.process(event, result)
                elif self.messagehandler:
                    result = self.messagehandler(event)
                    await self.process(event, result)
            
            print("Enter your phone number!")
            phone = input("Phone: ")
            
            self.client.start(phone=phone)
            
            print("Creating session with your provided details, Please enter OTP!")
            otp = input("OTP: ")
            
            self.client.sign_in(phone=phone, code=otp)
            
            self.client.run_until_disconnected()
            
        except Exception:
            error = self.cleanerror()
            print(f"Error: {error}")
    
    def cleanerror(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        return tb_list[-1].strip()
    
    async def process(self, event, result):
        try:
            if isinstance(result, dict):
                msgtype = result.get('type', 'text')
                
                if msgtype == 'text':
                    await event.reply(result['text'])
                
                elif msgtype == 'photo':
                    await event.reply(file=result['file'], message=result.get('caption'))
                
                elif msgtype == 'document':
                    await event.reply(file=result['file'], message=result.get('caption'))
                
                else:
                    await event.reply(str(result))
            else:
                await event.reply(str(result))
                
        except Exception:
            error = self.cleanerror()
            print(f"Error: {error}")