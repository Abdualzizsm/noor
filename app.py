import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'

# التحقق من وجود مفتاح GitHub
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

openai.api_key = github_token

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'الرسالة فارغة'}), 400
        
        # استدعاء OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي يدعى نور، تم تطويره بواسطة فريق ستيف وفريقه السعودي. أنت تجيب باللغة العربية بشكل أساسي، وتقدم معلومات دقيقة ومفيدة."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # استخراج الرد
        bot_response = response.choices[0].message.content
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'حدث خطأ أثناء معالجة طلبك'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    print(f"تم تشغيل {app.config['APP_NAME']} على الرابط: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', debug=False, port=port)
