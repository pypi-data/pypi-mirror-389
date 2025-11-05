**Note**: This package requires pyTeleBot for Telegram features and instabot for Instagram functionality. These dependencies will be automatically installed with Mehta. Make sure to use Instagram automation responsibly to avoid account restrictions from the platform.


## Installation
```sh
pip install mehta
```

## Telegram Setup
```python
from mehta import telegram

bot = telegram()

@bot.commands(['start'])
def welcome(message):
    return {
        'type': 'text',
        'text': 'Hello World!'
    } 

bot.run("BOT_TOKEN")
```

## Instagram Setup
```python
from mehta import instagram

bot = instagram()

@bot.commands(['start'])
def welcome(message):
    return {
        'type': 'dm',
        'text': 'Hello World!'
    }

bot.run(username="your_username", password="your_password")
```

## CLI
To run your python file `main.py`
```shell
mehta run:bot
```
