import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# الحصول على مفتاح GitHub من المتغيرات البيئية
github_token = os.environ.get('GITHUB_TOKEN')
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

# إعداد تطبيق Flask
app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # الحصول على رسالة المستخدم من طلب POST
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'لا توجد رسالة مقدمة'}), 400
        
        # التحقق من وجود مفتاح GitHub
        if not github_token:
            return jsonify({'error': 'لم يتم تكوين مفتاح GitHub. يرجى تحديث ملف .env'}), 500
        
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
                        "content": "أنت مساعد ذكي يُدعى نور. أنت مساعد لطيف ومفيد ومتعاون. تقدم إجابات دقيقة ومفيدة بأسلوب ودي. تجيب باللغة العربية بشكل أساسي."
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
            
            return jsonify({'response': ai_response})
            
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
                        "content": "أنت مساعد ذكي يُدعى نور. أنت مساعد لطيف ومفيد ومتعاون. تقدم إجابات دقيقة ومفيدة بأسلوب ودي. تجيب باللغة العربية بشكل أساسي."
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
            
            return jsonify({'response': ai_response})
    
    except requests.exceptions.RequestException as e:
        print(f"خطأ في الطلب: {str(e)}")
        return jsonify({'error': f'خطأ في الاتصال بالخادم: {str(e)}'}), 500
    except Exception as e:
        print(f"خطأ: {str(e)}")
        return jsonify({'error': f'حدث خطأ: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    print(f"تم تشغيل {app.config['APP_NAME']} على الرابط: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', debug=False, port=port)
