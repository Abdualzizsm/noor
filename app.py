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
gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBiQN8UfRfH8M-IWGd-Nt_xSPZkTwqMWvs")
genai.configure(api_key=gemini_api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        use_web_search = data.get('web_search', False)
        
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
        # التحقق من الأسئلة المتعلقة بالتاريخ والوقت
        import datetime
        import re
        
        # قائمة بالكلمات المفتاحية المتعلقة بالتاريخ والوقت
        date_time_keywords = [
            'تاريخ اليوم', 'اليوم كم', 'كم تاريخ', 'ما هو تاريخ', 'ما هو اليوم', 
            'التاريخ الحالي', 'الوقت الآن', 'الساعة الآن', 'كم الساعة', 'ما هي الساعة'
        ]
        
        # التحقق مما إذا كان السؤال يتعلق بالتاريخ أو الوقت
        is_date_time_query = any(keyword in user_message for keyword in date_time_keywords)
        
        if is_date_time_query:
            # الحصول على التاريخ والوقت الحاليين
            now = datetime.datetime.now()
            
            # تنسيق التاريخ والوقت بالعربية
            arabic_months = {
                1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
                7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
            }
            
            arabic_weekdays = {
                0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 
                3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
            }
            
            # تنسيق التاريخ بالعربية
            formatted_date = f"{now.day} {arabic_months[now.month]} {now.year}"
            weekday = arabic_weekdays[now.weekday()]
            
            # تنسيق الوقت
            formatted_time = now.strftime("%I:%M %p").replace("AM", "صباحاً").replace("PM", "مساءً")
            
            # إعداد الاستجابة بناءً على نوع السؤال
            if any(keyword in user_message for keyword in ['تاريخ', 'اليوم', 'التاريخ']):
                return f"اليوم هو {weekday}، {formatted_date}."
            elif any(keyword in user_message for keyword in ['الوقت', 'الساعة']):
                return f"الوقت الآن هو {formatted_time}."
            else:
                return f"اليوم هو {weekday}، {formatted_date}، والوقت الآن هو {formatted_time}."
        
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
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # تحسين الطلب للبحث عبر الإنترنت
        prompt = f"""
        قم بالبحث الشامل والمتعمق عن: {user_message}
        
        المطلوب:
        1. ابحث عن معلومات دقيقة وحديثة من مصادر موثوقة.
        2. قدم المعلومات بشكل منظم ومفصل.
        3. اذكر المصادر التي استخدمتها في البحث.
        4. تأكد من تقديم معلومات شاملة تغطي جميع جوانب الموضوع.
        5. قدم المعلومات بصيغة نصية واضحة.
        
        ملاحظة: هذه المعلومات الخام ستستخدم لاحقاً لتحليلها وإعادة صياغتها.
        """
        
        response = model.generate_content(prompt)
        
        # التحقق من وجود محتوى في الاستجابة
        if not response.text:
            return "لم يتم العثور على معلومات. يرجى إعادة صياغة طلبك."
        
        # تنظيف وتنسيق النص
        raw_info = response.text.strip()
        
        return raw_info
        
    except Exception as e:
        print(f"خطأ في استخدام Gemini مع البحث على الإنترنت: {str(e)}")
        return f"حدث خطأ أثناء البحث: {str(e)}"

def analyze_and_respond(user_question, raw_info):
    """تحليل المعلومات الخام وإعادة صياغتها بشكل ذكي"""
    try:
        # إنشاء نموذج Gemini لتحليل المعلومات
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 2048,
        }
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config
        )
        
        # تحسين الطلب لتحليل المعلومات
        prompt = f"""
        سؤال المستخدم: {user_question}
        
        المعلومات الخام:
        {raw_info}
        
        المطلوب:
        1. قم بتحليل المعلومات الخام بعناية.
        2. أعد صياغة المعلومات بأسلوب واضح وسلس.
        3. قدم إجابة مباشرة ومفصلة لسؤال المستخدم.
        4. استخدم لغة عربية فصيحة وسهلة الفهم.
        5. نظم الإجابة بشكل منطقي ومتسلسل.
        6. تجنب التكرار والحشو.
        7. أضف استنتاجات أو توصيات إذا كان ذلك مناسباً.
        
        ملاحظة: قدم إجابة شاملة ولكن مختصرة، مع التركيز على النقاط الأكثر أهمية.
        """
        
        response = model.generate_content(prompt)
        
        # التحقق من وجود محتوى في الاستجابة
        if not response.text:
            return "عذراً، لم أتمكن من تحليل المعلومات. يرجى إعادة صياغة سؤالك."
        
        # تنظيف وتنسيق النص
        final_response = response.text.strip()
        
        return final_response
        
    except Exception as e:
        print(f"خطأ في تحليل المعلومات: {str(e)}")
        return f"حدث خطأ أثناء تحليل المعلومات: {str(e)}"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5010))
    print(f"تم تشغيل {app.config['APP_NAME']} على الرابط: http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', debug=False, port=port)
