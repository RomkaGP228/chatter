import requests


def telegram(chat_id, message):
    bot_token = '7519668045:AAH643SvGHNjqK_ivjhBs7uL5gQc-teg4gg'
    send_message_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': message
    }

    response = requests.post(send_message_url, data=payload)
    print(response.json())
