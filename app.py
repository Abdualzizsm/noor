import os
import requests
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'

# التحقق من وجود مفتاح GitHub
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

# إعداد مفتاح Google Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    print("تحذير: لم يتم تعيين GEMINI_API_KEY في ملف .env")
else:
    genai.configure(api_key=gemini_api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        use_web_search = data.get('use_web_search', False)
        
        if not user_message:
            return jsonify({'error': 'الرسالة فارغة'}), 400
        
        # استجابة مؤقتة للاختبار
        if use_web_search:
            # الحصول على معلومات من الإنترنت أولاً
            raw_info = use_gemini_with_web_search(user_message)
            
            # ثم تحليل المعلومات وإعادة صياغتها بشكل ذكي
            final_response = analyze_and_respond(user_message, raw_info)
            
            return jsonify({
                'raw_info': raw_info,
                'response': final_response
            })
        else:
            response = process_message(user_message)
            return jsonify({'response': response})
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'حدث خطأ في معالجة طلبك'}), 500

def process_message(user_message):
    # التحقق إذا كان السؤال عن هوية الروبوت
    if any(phrase in user_message.lower() for phrase in ['من أنت', 'من انت', 'عرف نفسك', 'عرفنا عليك', 'من هو', 'من هي']):
        return "أنا ذكاء نور الخارق، كيف يمكنني مساعدتك اليوم؟"
    
    # التحقق من وجود مفتاح GitHub
    if not github_token:
        return "لم يتم تكوين مفتاح GitHub. يرجى تحديث ملف .env"
    
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
            return "لم يتم الحصول على رد من النموذج"
        
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
            return "لم يتم الحصول على رد من النموذج"
        
        return ai_response

def use_gemini_with_web_search(user_message):
    """استخدام Google Gemini مع البحث على الإنترنت"""
    try:
        # إنشاء نموذج Gemini مع تمكين البحث على الإنترنت
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # إنشاء نموذج Gemini مع تمكين البحث على الإنترنت
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # إعداد رسالة المستخدم مع توجيه للبحث على الإنترنت
        prompt = f"""
        قم بالبحث على الإنترنت عن: {user_message}
        
        قدم المعلومات الخام من مصادر متعددة. اذكر المصادر بوضوح. 
        لا تقم بتحليل المعلومات أو تلخيصها، فقط قدم المعلومات الأساسية كما هي.
        """
        
        # إنشاء محادثة
        chat = model.start_chat()
        
        # الحصول على استجابة من النموذج
        response = chat.send_message(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"خطأ في استخدام Gemini API: {str(e)}")
        return f"حدث خطأ أثناء البحث على الإنترنت: {str(e)}"

def analyze_and_respond(user_question, raw_info):
    """تحليل المعلومات الخام وإعادة صياغتها بشكل ذكي"""
    try:
        # إنشاء نموذج Gemini للتحليل
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }
        
        # إنشاء نموذج Gemini للتحليل
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config
        )
        
        # إعداد رسالة النظام
        system_message = """
        أنت ذكاء نور الخارق، مساعد ذكي طورته فريق ستيف وفريقه السعودي.
        مهمتك هي تحليل المعلومات الخام وإعادة صياغتها بأسلوب ذكي ومفهوم.
        
        اتبع هذه الإرشادات:
        1. حلل المعلومات الخام بعناية
        2. قدم إجابة مختصرة ومفيدة
        3. استخدم أسلوباً واضحاً وسهل الفهم
        4. تأكد من دقة المعلومات
        5. لا تذكر أبدًا أنك من Google أو أي شركة أخرى
        6. لا تكرر أنك تقوم بتحليل معلومات، فقط قدم الإجابة مباشرة
        """
        
        # إعداد رسالة التحليل
        prompt = f"""
        سؤال المستخدم: {user_question}
        
        المعلومات الخام من البحث على الإنترنت:
        {raw_info}
        
        قم بتحليل هذه المعلومات وقدم إجابة ذكية ومختصرة ومفيدة للمستخدم.
        """
        
        # إنشاء محادثة
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_message]},
            {"role": "model", "parts": ["سأقوم بتحليل المعلومات وتقديم إجابة ذكية ومفيدة."]}
        ])
        
        # الحصول على استجابة من النموذج
        response = chat.send_message(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"خطأ في تحليل المعلومات: {str(e)}")
        return f"حدث خطأ أثناء تحليل المعلومات: {str(e)}"

if __name__ == '__main__':
    print("تم تشغيل نور (Noor) على الرابط: http://127.0.0.1:5030")
    app.run(host='0.0.0.0', port=5030)
