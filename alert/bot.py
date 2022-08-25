import telegram as tel
from env import TELEGRAM_TOKEN, CHAT_ID


class TelegramBot:
    def __init__(self):
        self.bot = tel.Bot(token=TELEGRAM_TOKEN)
        self.log_queue = []

    def log(self, msg):
        self.log_queue.append(str(msg))

    def clear_logs(self):
        self.log_queue = []

    def send_logs(self):
        if len(self.log_queue) == 0:
            return

        joined_log = "\n".join(self.log_queue)
        if len(joined_log) > 1990:
            full_msg = f"""{joined_log[:1990]}..."""
        else:
            full_msg = f"""{joined_log}"""

        self.bot.sendMessage(chat_id=CHAT_ID, text=full_msg)
        self.log_queue = []


if "__main__" == __name__:
    telegram_bot = TelegramBot()
    telegram_bot.log("qve to the moon")
    telegram_bot.send_logs()
