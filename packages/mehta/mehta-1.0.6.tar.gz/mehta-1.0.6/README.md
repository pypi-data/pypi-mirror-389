**Installation**:
```sh
pip install mehta
```

**Basic Setup**:
```py
from mehta import telegram

bot = telegram()

@bot.commands(['start'])
def welcome(message):
    return "Hello World!"

bot.run("TOKEN")
```