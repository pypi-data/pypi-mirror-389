# JsonBot

# Installation
```shell
pip install jsonbot
```

# Usage
```python
from jsonbot import JsonBot

JsonBot("token", {
    "/start", {"response": "hello *{first_name}*", "parse_mode": "MarkdownV2", "reply_markup"},
    "/help": {"response": "Hello how can i help you"}
}).run()
```
## you can generate code to osonbot library itself (but not fully prepared)
```python
from jsonbot import JsonBot

JsonBot("token", {
    "/start", {"response": "hello *{first_name}*", "parse_mode": "MarkdownV2", "reply_markup"},
    "/help": {"response": "Hello how can i help you"}
}).generate_code(library="osonbot", file="main.py")
```
# Done