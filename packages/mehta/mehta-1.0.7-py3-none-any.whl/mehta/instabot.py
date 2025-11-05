"""
DO NOT EDIT! OR MODIFY:
Join us @starexxchat on Telegram
"""
import os, sys, traceback
from instabot import Bot
class instagram:
    def __init__(self):
        self.bot = None
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
    
    def run(self, username, password):
        try:
            self.bot = Bot()
            self.bot.login(username=username, password=password)
            
        except Exception:
            error = self.cleanerror()
            print(f"Error: {error}")
    
    def cleanerror(self):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        return tb_list[-1].strip()
    
    def process(self, result, user_id=None, username=None):
        try:
            if isinstance(result, dict):
                msgtype = result.get('type')
                
                if msgtype == 'dm':
                    text = result.get('text', '')
                    target_user = result.get('username', username)
                    
                    if target_user:
                        user_id = self.bot.get_user_id_from_username(target_user)
                    
                    if user_id:
                        self.bot.send_message(text, [user_id])
                
                elif msgtype == 'post':
                    self.bot.upload_photo(result['file'], caption=result.get('caption', ''))
                
                elif msgtype == 'video':
                    self.bot.upload_video(result['file'], caption=result.get('caption', ''))
                
                elif msgtype == 'story':
                    if result['file'].endswith(('.jpg', '.png', '.jpeg')):
                        self.bot.upload_story_photo(result['file'])
                    else:
                        self.bot.upload_story_video(result['file'])
                
                elif msgtype == 'profile':
                    return self.bot.get_user_info(result.get('username'))
                
                elif msgtype == 'followers':
                    return self.bot.get_user_followers(result.get('username'))
                
                elif msgtype == 'following':
                    return self.bot.get_user_following(result.get('username'))
                
                elif msgtype == 'follow':
                    self.bot.follow(result['username'])
                
                elif msgtype == 'unfollow':
                    self.bot.unfollow(result['username'])
                
                elif msgtype == 'like':
                    self.bot.like(result['media_id'])
                
                elif msgtype == 'unlike':
                    self.bot.unlike(result['media_id'])
                
                elif msgtype == 'comment':
                    self.bot.comment(result['media_id'], result['text'])
                
                elif msgtype == 'reply':
                    self.bot.reply_to_comment(result['media_id'], result['comment_id'], result['text'])
                
                elif msgtype == 'deletecomment':
                    self.bot.delete_comment(result['media_id'], result['comment_id'])
                
                elif msgtype == 'likecomment':
                    self.bot.like_comment(result['comment_id'])
                
                elif msgtype == 'unlikecomment':
                    self.bot.unlike_comment(result['comment_id'])
                
                elif msgtype == 'block':
                    self.bot.block(result['username'])
                
                elif msgtype == 'unblock':
                    self.bot.unblock(result['username'])
                
                elif msgtype == 'approve':
                    self.bot.approve_pending_friend_requests()
                
                elif msgtype == 'ignore':
                    self.bot.ignore_pending_friend_requests()
                
                elif msgtype == 'pending':
                    return self.bot.get_pending_friend_requests()
                
                elif msgtype == 'mediainfo':
                    return self.bot.get_media_info(result['media_id'])
                
                elif msgtype == 'userfeed':
                    return self.bot.get_user_feed(result.get('username'))
                
                elif msgtype == 'hashtagfeed':
                    return self.bot.get_hashtag_feed(result['hashtag'])
                
                elif msgtype == 'locationfeed':
                    return self.bot.get_location_feed(result['location_id'])
                
                elif msgtype == 'geofeed':
                    return self.bot.get_geotag_feed(result['location_id'])
                
                elif msgtype == 'saved':
                    return self.bot.get_saved_media()
                
                elif msgtype == 'archive':
                    self.bot.archive(result['media_id'])
                
                elif msgtype == 'unarchive':
                    self.bot.unarchive(result['media_id'])
                
                elif msgtype == 'highlight':
                    self.bot.create_highlight(result['media_ids'])
                
                elif msgtype == 'deletehighlight':
                    self.bot.delete_highlight(result['highlight_id'])
                
                elif msgtype == 'igtv':
                    self.bot.upload_igtv_video(result['file'], title=result.get('title'), caption=result.get('caption'))
                
                elif msgtype == 'reel':
                    self.bot.upload_reel_video(result['file'], caption=result.get('caption'))
                
                elif msgtype == 'bio':
                    self.bot.set_biography(result['text'])
                
                elif msgtype == 'website':
                    self.bot.set_website(result['url'])
                
                elif msgtype == 'private':
                    self.bot.set_account_private()
                
                elif msgtype == 'public':
                    self.bot.set_account_public()
                
                elif msgtype == 'storypoll':
                    self.bot.upload_story_poll(result['file'], question=result['question'], options=result['options'])
                
                elif msgtype == 'storyquestion':
                    self.bot.upload_story_question(result['file'], question=result['question'])
                
                elif msgtype == 'storyquiz':
                    self.bot.upload_story_quiz(result['file'], question=result['question'], options=result['options'], correct=result['correct'])
                
                elif msgtype == 'storyslider':
                    self.bot.upload_story_slider(result['file'], question=result['question'], emoji=result.get('emoji'))
                
                elif msgtype == 'storycountdown':
                    self.bot.upload_story_countdown(result['file'], text=result['text'], end_ts=result['end_ts'])
                
                elif msgtype == 'storymention':
                    self.bot.upload_story_mention(result['file'], user_ids=result['user_ids'])
                
                elif msgtype == 'storyhashtag':
                    self.bot.upload_story_hashtag(result['file'], hashtag=result['hashtag'])
                
                elif msgtype == 'storylocation':
                    self.bot.upload_story_location(result['file'], location_id=result['location_id'])
                
                elif msgtype == 'analytics':
                    return self.bot.get_insights()
                
                else:
                    return f"Unknown type: {msgtype}"
            else:
                return str(result)
                
        except Exception:
            error = self.cleanerror()
            return f"Error: {error}"