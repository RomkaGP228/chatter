import requests
from data.config import TOKEN


def telegram(chat_id, message):
    bot_token = TOKEN
    send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.post(send_message_url, data=payload)
    print(response.json())
