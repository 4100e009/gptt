from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import openai
import os

app = Flask(__name__)

# 從環境變量獲取 LINE 和 OpenAI 的設定值
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.client = os.getenv('OPENAI_API_KEY')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 使用 OpenAI GPT-4 來生成回應
    try:
        stream = openai.chat.completions.create(
            model="gpt-4",
            
            messages=[
                {"role": "system", "content": "用中文回答"},
                {"role": "user", "content": user_message}],
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                reply_text = chunk.choices[0].delta.content, end=""
    except Exception as e:
        app.logger.error(f"Error in OpenAI response: {e}")
        reply_text = "抱歉，我無法回答這個問題。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run()


