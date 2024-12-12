import requests

def send_telegram_alert(message, bot_token, chat_id):
    """Telegram 알림 전송"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        # print(f"Sending message to chat_id: {chat_id}")  # 디버그 로그
        # print(f"Using bot_token: {bot_token[:20]}...")   # 토큰의 일부만 출력
        response = requests.post(url, json=payload)
        # print(f"Response status: {response.status_code}")  # 응답 상태 코드
        # print(f"Response text: {response.text}")          # 자세한 에러 메시지
        
        if response.status_code == 200:
            print("Telegram message sent successfully")
        else:
            print(f"Failed to send Telegram message: {response.status_code}")
            print(f"Error details: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}") 