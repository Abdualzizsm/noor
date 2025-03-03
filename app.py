import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'

# التحقق من وجود مفتاح GitHub
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'الرسالة فارغة'}), 400
        
        # هنا يمكن إضافة منطق معالجة الرسالة واستدعاء API الذكاء الاصطناعي
        
        # استجابة مؤقتة للاختبار
        response = process_message(user_message)
        
        return jsonify({'response': response})
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'حدث خطأ في معالجة طلبك'}), 500

def process_message(user_message):
    # التحقق من وجود مفتاح GitHub
    if not github_token:
        return jsonify({'error': 'لم يتم تكوين مفتاح GitHub. يرجى تحديث ملف .env'}), 500
    
    # التحقق إذا كان السؤال عن هوية الروبوت
    if any(phrase in user_message.lower() for phrase in ['من أنت', 'من انت', 'عرف نفسك', 'عرفنا عليك', 'من هو', 'من هي']):
        return "أنا ذكاء نور الخارق، كيف يمكنني مساعدتك اليوم؟"
    
    # طباعة معلومات تصحيح الأخطاء
    print(f"استخدام المفتاح: {github_token[:5]}...{github_token[-5:] if len(github_token) > 10 else ''}")
    
    # تجربة استخدام واجهة برمجة تطبيقات OpenAI
    try:
        # إعداد الطلب إلى واجهة برمجة تطبيقات OpenAI
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json"
        }
        
        # إعداد بيانات الطلب
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "أنت ذكاء نور الخارق. ساعد المستخدم بإجابات مختصرة ومفيدة. لا تذكر أبدًا أنك من OpenAI أو أي شركة أخرى."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # نقطة النهاية المستخدمة
        endpoint = "https://api.openai.com/v1/chat/completions"
        print(f"استخدام نقطة النهاية: {endpoint}")
        
        # إرسال الطلب إلى واجهة برمجة التطبيقات
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload
        )
        
        # التحقق من نجاح الطلب
        response.raise_for_status()
        
        # استخراج الرد من النموذج
        response_data = response.json()
        ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not ai_response:
            return jsonify({'error': 'لم يتم الحصول على رد من النموذج'}), 500
        
        return ai_response
        
    except requests.exceptions.RequestException as e:
        # إذا فشلت واجهة برمجة تطبيقات OpenAI، نجرب واجهة برمجة تطبيقات GitHub AI
        print(f"فشل طلب OpenAI: {str(e)}. جاري تجربة GitHub AI...")
        
        # إعداد الطلب إلى واجهة برمجة تطبيقات GitHub AI
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # إعداد بيانات الطلب
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": ""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 1,
            "max_tokens": 2048,
            "top_p": 1
        }
        
        # نقطة النهاية المستخدمة
        endpoints = [
            "https://models.github.ai/inference/chat/completions",  # الأصلية
            "https://api.github.com/models/chat/completions",  # تجربة 1
            "https://api.github.com/models/gpt-4o-mini/chat/completions"  # تجربة 2
        ]
        
        # استخدام النقطة الأصلية
        endpoint = endpoints[0]
        print(f"استخدام نقطة النهاية: {endpoint}")
        
        # إرسال الطلب إلى واجهة برمجة التطبيقات
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload
        )
        
        # التحقق من نجاح الطلب
        response.raise_for_status()
        
        # استخراج الرد من النموذج
        response_data = response.json()
        ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not ai_response:
            return jsonify({'error': 'لم يتم الحصول على رد من النموذج'}), 500
        
        return ai_response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    print(f"تم تشغيل {app.config['APP_NAME']} على الرابط: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', debug=False, port=port)
