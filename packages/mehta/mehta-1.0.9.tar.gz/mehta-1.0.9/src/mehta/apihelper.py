"""
DO NOT EDIT! OR MODIFY:
Join us @starexxchat on Telegram
"""
import sys, traceback, os, requests
from telebot.types import *
from io import BytesIO
import telebot

# main content telegram()
class telegram:
    def __init__(self):
        self.bot = None
        self.commandhandlers = {}
        self.messagehandler = None
        self.callbackhandler = None
        
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
    
    def callback(self):
        def decorator(func):
            self.callbackhandler = func
            return func
        return decorator
    
    def run(self, token):
        try:
            self.bot = telebot.TeleBot(token)
            
            for cmd, handler in self.commandhandlers.items():
                @self.bot.message_handler(commands=[cmd])
                def handlecommand(message, handler=handler):
                    try:
                        result = handler(message)
                        self.send(message, result)
                    except Exception:
                        error = self.cleanerror()
                        print(f"Error: {error}")
            
            if self.messagehandler:
                @self.bot.message_handler(func=lambda m: True)
                def handlemessage(message):
                    try:
                        result = self.messagehandler(message)
                        self.send(message, result)
                    except Exception:
                        error = self.cleanerror()
                        print(f"Error: {error}")
            
            if self.callbackhandler:
                @self.bot.callback_query_handler(func=lambda call: True)
                def handlecallback(call):
                    try:
                        result = self.callbackhandler(call)
                        self.send(call.message, result)
                    except Exception:
                        error = self.cleanerror()
                        print(f"Error: {error}")
            
            self.bot.polling(none_stop=True, timeout=60)
            
        except Exception:
            error = self.cleanerror()
            print(f"Error: {error}")
    
    def cleanerror(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for i, line in enumerate(tb_list):
            line = line.replace('telebot.', 'mehta.')
            tb_list[i] = line
        return tb_list[-1].strip()
    
    def getfile(self, fileinput):
        if isinstance(fileinput, str):
            if fileinput.startswith(('http://', 'https://')):
                response = requests.get(fileinput)
                return BytesIO(response.content)
            elif os.path.exists(fileinput):
                with open(fileinput, 'rb') as f:
                    return BytesIO(f.read())
            else:
                return fileinput
        return fileinput
    
    def send(self, message, result):
        try:
            if isinstance(result, dict):
                msgtype = result.get('type', 'text')
                parse = result.get('parse')
                receiver = result.get('receiver', message.chat.id)
                replyto = result.get('reply_to', message.message_id)
                preview = result.get('preview', True)
                notify = result.get('notify', True)
                
                if msgtype == 'text':
                    self.bot.send_message(receiver, result['text'], parse_mode=parse, 
                                        reply_to_message_id=replyto, disable_web_page_preview=not preview, 
                                        disable_notification=not notify)
                
                elif msgtype == 'photo':
                    file = self.getfile(result['file'])
                    self.bot.send_photo(receiver, file, caption=result.get('caption'), 
                                      parse_mode=parse, reply_to_message_id=replyto, 
                                      disable_notification=not notify)
                
                elif msgtype == 'video':
                    file = self.getfile(result['file'])
                    self.bot.send_video(receiver, file, caption=result.get('caption'), 
                                      parse_mode=parse, reply_to_message_id=replyto, 
                                      disable_notification=not notify)
                
                elif msgtype == 'audio':
                    file = self.getfile(result['file'])
                    self.bot.send_audio(receiver, file, caption=result.get('caption'), 
                                      parse_mode=parse, reply_to_message_id=replyto, 
                                      disable_notification=not notify)
                
                elif msgtype == 'document':
                    file = self.getfile(result['file'])
                    self.bot.send_document(receiver, file, caption=result.get('caption'), 
                                         parse_mode=parse, reply_to_message_id=replyto, 
                                         disable_notification=not notify)
                
                elif msgtype == 'sticker':
                    file = self.getfile(result['file'])
                    self.bot.send_sticker(receiver, file, reply_to_message_id=replyto, 
                                        disable_notification=not notify)
                
                elif msgtype == 'voice':
                    file = self.getfile(result['file'])
                    self.bot.send_voice(receiver, file, caption=result.get('caption'), 
                                      parse_mode=parse, reply_to_message_id=replyto, 
                                      disable_notification=not notify)
                
                elif msgtype == 'animation':
                    file = self.getfile(result['file'])
                    self.bot.send_animation(receiver, file, caption=result.get('caption'), 
                                          parse_mode=parse, reply_to_message_id=replyto, 
                                          disable_notification=not notify)
                
                elif msgtype == 'location':
                    self.bot.send_location(receiver, result['lat'], result['lon'], 
                                         reply_to_message_id=replyto, disable_notification=not notify)
                
                elif msgtype == 'venue':
                    self.bot.send_venue(receiver, result['lat'], result['lon'], 
                                      result['title'], result['address'], reply_to_message_id=replyto, 
                                      disable_notification=not notify)
                
                elif msgtype == 'contact':
                    self.bot.send_contact(receiver, result['phone'], result['first_name'], 
                                        result.get('last_name'), reply_to_message_id=replyto, 
                                        disable_notification=not notify)
                
                elif msgtype == 'poll':
                    self.bot.send_poll(receiver, result['question'], result['options'], 
                                     reply_to_message_id=replyto, disable_notification=not notify)
                
                elif msgtype == 'dice':
                    self.bot.send_dice(receiver, result.get('emoji', '🎲'), 
                                     reply_to_message_id=replyto, disable_notification=not notify)
                
                elif msgtype == 'mediagroup':
                    media = []
                    for item in result['media']:
                        file = self.getfile(item['file'])
                        if item['type'] == 'photo':
                            media.append(InputMediaPhoto(file, caption=item.get('caption'), parse_mode=parse))
                        elif item['type'] == 'video':
                            media.append(InputMediaVideo(file, caption=item.get('caption'), parse_mode=parse))
                    self.bot.send_media_group(receiver, media, disable_notification=not notify)
                
                elif msgtype == 'keyboard':
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    for row in result['buttons']:
                        markup.add(*[KeyboardButton(btn) for btn in row])
                    self.bot.send_message(receiver, result['text'], reply_markup=markup, 
                                        parse_mode=parse, reply_to_message_id=replyto, 
                                        disable_web_page_preview=not preview, disable_notification=not notify)
                
                elif msgtype == 'inline':
                    markup = InlineKeyboardMarkup()
                    for row in result['buttons']:
                        rowbuttons = []
                        for btn in row:
                            if btn.get('url'):
                                rowbuttons.append(InlineKeyboardButton(btn['text'], url=btn['url']))
                            elif btn.get('data'):
                                rowbuttons.append(InlineKeyboardButton(btn['text'], callback_data=btn['data']))
                            else:
                                rowbuttons.append(InlineKeyboardButton(btn['text']))
                        markup.add(*rowbuttons)
                    self.bot.send_message(receiver, result['text'], reply_markup=markup, 
                                        parse_mode=parse, reply_to_message_id=replyto, 
                                        disable_web_page_preview=not preview, disable_notification=not notify)
                
                elif msgtype == 'removekeyboard':
                    self.bot.send_message(receiver, result['text'], 
                                        reply_markup=ReplyKeyboardRemove(), parse_mode=parse, 
                                        reply_to_message_id=replyto, disable_web_page_preview=not preview, 
                                        disable_notification=not notify)
                
                elif msgtype == 'forcereply':
                    self.bot.send_message(receiver, result['text'], 
                                        reply_markup=ForceReply(), parse_mode=parse, 
                                        reply_to_message_id=replyto, disable_web_page_preview=not preview, 
                                        disable_notification=not notify)
                
                elif msgtype == 'delete':
                    self.bot.delete_message(receiver, result.get('message_id', message.message_id))
                
                elif msgtype == 'edittext':
                    self.bot.edit_message_text(result['text'], receiver, 
                                             result.get('message_id', message.message_id), 
                                             parse_mode=parse, disable_web_page_preview=not preview)
                
                elif msgtype == 'editcaption':
                    self.bot.edit_message_caption(receiver, result.get('message_id', message.message_id), 
                                                caption=result['caption'], parse_mode=parse)
                
                elif msgtype == 'editmarkup':
                    markup = InlineKeyboardMarkup()
                    for row in result['buttons']:
                        rowbuttons = []
                        for btn in row:
                            if btn.get('url'):
                                rowbuttons.append(InlineKeyboardButton(btn['text'], url=btn['url']))
                            elif btn.get('data'):
                                rowbuttons.append(InlineKeyboardButton(btn['text'], callback_data=btn['data']))
                            else:
                                rowbuttons.append(InlineKeyboardButton(btn['text']))
                        markup.add(*rowbuttons)
                    self.bot.edit_message_reply_markup(receiver, result.get('message_id', message.message_id), 
                                                     reply_markup=markup)
                
                elif msgtype == 'pin':
                    self.bot.pin_chat_message(receiver, result.get('message_id', message.message_id), 
                                            disable_notification=not notify)
                
                elif msgtype == 'unpin':
                    self.bot.unpin_chat_message(receiver, result.get('message_id', message.message_id))
                
                elif msgtype == 'unpinall':
                    self.bot.unpin_all_chat_messages(receiver)
                
                elif msgtype == 'forward':
                    self.bot.forward_message(result['to'], receiver, 
                                           result.get('message_id', message.message_id), 
                                           disable_notification=not notify)
                
                elif msgtype == 'copy':
                    self.bot.copy_message(result['to'], receiver, 
                                        result.get('message_id', message.message_id), 
                                        caption=result.get('caption'), parse_mode=parse, 
                                        disable_notification=not notify)
                
                elif msgtype == 'ban':
                    self.bot.ban_chat_member(receiver, result['user'], 
                                           until_date=result.get('until'))
                
                elif msgtype == 'unban':
                    self.bot.unban_chat_member(receiver, result['user'])
                
                elif msgtype == 'kick':
                    self.bot.kick_chat_member(receiver, result['user'])
                
                elif msgtype == 'leave':
                    self.bot.leave_chat(receiver)
                
                elif msgtype == 'restrict':
                    self.bot.restrict_chat_member(receiver, result['user'], 
                                                until_date=result.get('until'),
                                                can_send_messages=result.get('send', False),
                                                can_send_media_messages=result.get('media', False),
                                                can_send_polls=result.get('polls', False),
                                                can_send_other_messages=result.get('other', False),
                                                can_add_web_page_previews=result.get('previews', False))
                
                elif msgtype == 'promote':
                    self.bot.promote_chat_member(receiver, result['user'],
                                               can_change_info=result.get('change_info', False),
                                               can_post_messages=result.get('post', False),
                                               can_edit_messages=result.get('edit', False),
                                               can_delete_messages=result.get('delete', False),
                                               can_invite_users=result.get('invite', False),
                                               can_restrict_members=result.get('restrict', False),
                                               can_pin_messages=result.get('pin', False),
                                               can_promote_members=result.get('promote', False))
                
                elif msgtype == 'settitle':
                    self.bot.set_chat_title(receiver, result['title'])
                
                elif msgtype == 'setdescription':
                    self.bot.set_chat_description(receiver, result['description'])
                
                elif msgtype == 'setphoto':
                    file = self.getfile(result['file'])
                    self.bot.set_chat_photo(receiver, file)
                
                elif msgtype == 'deletephoto':
                    self.bot.delete_chat_photo(receiver)
                
                elif msgtype == 'invitelink':
                    link = self.bot.export_chat_invite_link(receiver)
                    return f"{link}"
                
                elif msgtype == 'chatinfo':
                    info = self.bot.get_chat(receiver)
                    return str(info)
                
                elif msgtype == 'membercount':
                    count = self.bot.get_chat_members_count(receiver)
                    return f"{count}"
                
                elif msgtype == 'memberinfo':
                    info = self.bot.get_chat_member(receiver, result['user'])
                    return str(info)
                
                elif msgtype == 'answer':
                    self.bot.answer_callback_query(message.id, 
                                                 text=result.get('text'),
                                                 show_alert=result.get('alert', False))
                
                else:
                    self.bot.send_message(receiver, str(result), parse_mode=parse, 
                                        reply_to_message_id=replyto, disable_web_page_preview=not preview, 
                                        disable_notification=not notify)
            else:
                self.bot.reply_to(message, str(result))
                
        except Exception:
            error = self.cleanerror()
            print(f"Error: {error}")
            
            
            
            
            
            
            
            
            
            
            # DEV: @realstarexx / @starexx