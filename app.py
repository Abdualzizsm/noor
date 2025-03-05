import os
import requests
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import argparse
from datetime import datetime
import pytz
from hijri_converter import Gregorian, Hijri
from thinking_engine import ThinkingEngine
from reasoning_engine import ReasoningEngine, create_initial_knowledge_base
from knowledge_manager import KnowledgeManager

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'

# إنشاء محرك التفكير العالمي
thinking_engine = ThinkingEngine()

# إنشاء محرك الاستدلال المنطقي مع قاعدة معرفية أولية
knowledge_base = create_initial_knowledge_base()
reasoning_engine = ReasoningEngine(knowledge_base)

# إنشاء مدير قاعدة المعرفة
knowledge_manager = KnowledgeManager(knowledge_base)

# التحقق من وجود مفتاح GitHub
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

# إعداد مفتاح OpenAI API
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("تحذير: لم يتم تعيين OPENAI_API_KEY في ملف .env")

# إعداد مفتاح Google Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBiQN8UfRfH8M-IWGd-Nt_xSPZkTwqMWvs")
genai.configure(api_key=gemini_api_key)

# متغير عالمي لتخزين سجل المحادثة
conversation_history = []

@app.route('/')
def index():
    # إعادة تعيين سجل المحادثة عند بدء جلسة جديدة
    global conversation_history
    conversation_history = []
    return render_template('index.html', app_name=app.config['APP_NAME'])

@app.route('/knowledge')
def knowledge_base_manager():
    """صفحة إدارة قاعدة المعرفة"""
    return render_template('knowledge.html', app_name=app.config['APP_NAME'])

@app.route('/api/concepts', methods=['GET'])
def get_concepts():
    """الحصول على قائمة المفاهيم"""
    concepts = []
    for concept_id, concept in knowledge_manager.knowledge_graph.concepts.items():
        concepts.append({
            'id': concept.id,
            'name': concept.name,
            'description': concept.description,
            'category': concept.category
        })
    return jsonify(concepts)

@app.route('/api/concepts', methods=['POST'])
def add_concept():
    """إضافة مفهوم جديد"""
    data = request.json
    concept_id = knowledge_manager.add_concept(
        name=data.get('name', ''),
        description=data.get('description', ''),
        category=data.get('category', ''),
        related_concepts=data.get('related_concepts', []),
        attributes=data.get('attributes', {})
    )
    
    if concept_id:
        return jsonify({'success': True, 'id': concept_id})
    else:
        return jsonify({'success': False, 'message': 'فشل في إضافة المفهوم'}), 400

@app.route('/api/concepts/<concept_id>', methods=['PUT'])
def update_concept(concept_id):
    """تحديث مفهوم موجود"""
    data = request.json
    success = knowledge_manager.update_concept(
        concept_id=concept_id,
        name=data.get('name'),
        description=data.get('description'),
        category=data.get('category'),
        related_concepts=data.get('related_concepts'),
        attributes=data.get('attributes')
    )
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'فشل في تحديث المفهوم'}), 400

@app.route('/api/concepts/<concept_id>', methods=['DELETE'])
def delete_concept(concept_id):
    """حذف مفهوم"""
    success = knowledge_manager.delete_concept(concept_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'فشل في حذف المفهوم'}), 400

@app.route('/api/relations', methods=['GET'])
def get_relations():
    """الحصول على قائمة العلاقات"""
    relations = []
    for source, target in knowledge_manager.knowledge_graph.graph.edges():
        edge_data = knowledge_manager.knowledge_graph.graph.get_edge_data(source, target)
        relations.append({
            'source': source,
            'source_name': knowledge_manager.knowledge_graph.concepts[source].name,
            'target': target,
            'target_name': knowledge_manager.knowledge_graph.concepts[target].name,
            'relation_type': edge_data.get('relation_type', 'related_to'),
            'strength': edge_data.get('strength', 0.5),
            'description': edge_data.get('description', '')
        })
    return jsonify(relations)

@app.route('/api/relations', methods=['POST'])
def add_relation():
    """إضافة علاقة جديدة"""
    data = request.json
    success = knowledge_manager.add_relation(
        source_name=data.get('source_name', ''),
        target_name=data.get('target_name', ''),
        relation_type=data.get('relation_type', ''),
        strength=data.get('strength', 0.5),
        description=data.get('description', ''),
        bidirectional=data.get('bidirectional', False)
    )
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'فشل في إضافة العلاقة'}), 400

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """الحصول على قائمة الفئات الفريدة"""
    categories = set()
    for concept in knowledge_manager.knowledge_graph.concepts.values():
        categories.add(concept.category)
    return jsonify(list(categories))

@app.route('/api/export', methods=['GET'])
def export_knowledge_base():
    """تصدير قاعدة المعرفة"""
    format_type = request.args.get('format', 'json')
    data = knowledge_manager.export_knowledge_base(format_type)
    
    if data:
        return jsonify({'success': True, 'data': data})
    else:
        return jsonify({'success': False, 'message': 'فشل في تصدير قاعدة المعرفة'}), 400

@app.route('/api/import', methods=['POST'])
def import_knowledge_base():
    """استيراد قاعدة المعرفة"""
    data = request.json
    success = knowledge_manager.import_knowledge_base(
        data_str=data.get('data', ''),
        format_type=data.get('format', 'json')
    )
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'فشل في استيراد قاعدة المعرفة'}), 400

@app.route('/api/batch/concepts', methods=['POST'])
def batch_process_concepts():
    """معالجة مجموعة من المفاهيم على دفعات"""
    data = request.json
    concepts_data = data.get('concepts', [])
    batch_size = data.get('batch_size', None)
    
    if batch_size:
        knowledge_manager.set_batch_size(int(batch_size))
    
    success_count, fail_count = knowledge_manager.batch_process_concepts(concepts_data)
    
    return jsonify({
        'success': True,
        'stats': {
            'success_count': success_count,
            'fail_count': fail_count,
            'total': success_count + fail_count
        }
    })

@app.route('/api/batch/relations', methods=['POST'])
def batch_process_relations():
    """معالجة مجموعة من العلاقات على دفعات"""
    data = request.json
    relations_data = data.get('relations', [])
    batch_size = data.get('batch_size', None)
    
    if batch_size:
        knowledge_manager.set_batch_size(int(batch_size))
    
    success_count, fail_count = knowledge_manager.batch_process_relations(relations_data)
    
    return jsonify({
        'success': True,
        'stats': {
            'success_count': success_count,
            'fail_count': fail_count,
            'total': success_count + fail_count
        }
    })

@app.route('/api/optimize', methods=['POST'])
def optimize_knowledge_base():
    """تحسين وتنظيف قاعدة المعرفة"""
    stats = knowledge_manager.optimize_knowledge_base()
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.route('/api/clear-cache', methods=['POST'])
def clear_knowledge_cache():
    """مسح الذاكرة المؤقتة لمدير المعرفة"""
    knowledge_manager.clear_caches()
    
    return jsonify({
        'success': True,
        'message': 'تم مسح الذاكرة المؤقتة بنجاح'
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        global conversation_history
        data = request.json
        user_message = data.get('message', '')
        use_web_search = data.get('web_search', False)
        
        if not user_message:
            return jsonify({'error': 'الرسالة فارغة'}), 400
        
        # إضافة رسالة المستخدم إلى سجل المحادثة
        conversation_history.append({"role": "user", "content": user_message})
        
        # استجابة مؤقتة للاختبار
        if use_web_search:
            # الحصول على معلومات من الإنترنت أولاً
            raw_info = use_gemini_with_web_search(user_message)
            
            # ثم تحليل المعلومات وإعادة صياغتها بشكل ذكي مع مراعاة سياق المحادثة
            final_response = analyze_and_respond(user_message, raw_info, conversation_history)
            
            # إضافة رد النموذج إلى سجل المحادثة
            conversation_history.append({"role": "assistant", "content": final_response["response"]})
            
            # الحفاظ على سجل محادثة محدود (آخر 10 رسائل فقط)
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
            
            return jsonify({
                'raw_info': raw_info,
                'response': final_response["response"],
                'thinking_process': final_response["thinking_process"]
            })
        else:
            response_data = process_message(user_message, conversation_history)
            
            # إضافة رد النموذج إلى سجل المحادثة
            conversation_history.append({"role": "assistant", "content": response_data["response"]})
            
            # الحفاظ على سجل محادثة محدود (آخر 10 رسائل فقط)
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
                
            return jsonify(response_data)
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'حدث خطأ في معالجة طلبك'}), 500

def process_message(user_message, conversation_history):
    # التحقق إذا كان السؤال عن هوية الروبوت
    if any(phrase in user_message.lower() for phrase in ['من أنت', 'من انت', 'عرف نفسك', 'عرفنا عليك', 'من هو', 'من هي']):
        return {
            "response": "أنا ذكاء نور الخارق، كيف يمكنني مساعدتك اليوم؟",
            "thinking_process": "تحليل السؤال: سؤال عن الهوية\nالاستجابة: تقديم معلومات عن هوية نور"
        }
    
    # التحقق من طلبات التاريخ والوقت
    if any(keyword in user_message.lower() for keyword in ['تاريخ', 'اليوم', 'التاريخ', 'الوقت', 'الساعة']):
        response = handle_date_time_query(user_message, conversation_history)
        return response
    
    try:
        # تحليل السؤال وتخطيط الحل باستخدام محرك التفكير
        question_analysis = thinking_engine.analyze_question(user_message)
        solution_steps = thinking_engine.plan_solution(question_analysis)
        
        # تنفيذ كل خطوة من خطوات التفكير
        context = {
            'user_message': user_message,
            'conversation_history': conversation_history,
            'web_search_enabled': True
        }
        
        for step in solution_steps:
            thinking_engine.execute_thinking_step(step, context)
        
        # الحصول على نتيجة التفكير المنطقي
        thinking_process = thinking_engine.format_thinking_process()
        
        # تطبيق التفكير الاستنتاجي
        reasoning_result = reasoning_engine.reason(user_message)
        reasoning_output = reasoning_engine.format_reasoning_result(reasoning_result)
        
        # دمج نتائج التفكير المنطقي والاستنتاجي
        combined_thinking = f"{thinking_process}\n\n{reasoning_output}"
        
        # إعداد الطلب إلى واجهة برمجة تطبيقات GitHub AI
        messages = [
            {
                "role": "system",
                "content": """أنت ذكاء نور الخارق. ساعد المستخدم بإجابات مختصرة ومفيدة.
                استخدم نتائج التفكير المنطقي والاستنتاجي المقدمة لتحسين إجابتك.
                حافظ على سياق المحادثة وقدم إجابات دقيقة ومفيدة."""
            },
            {
                "role": "system",
                "content": f"نتائج التفكير:\n{combined_thinking}"
            }
        ]
        
        # إضافة آخر 10 رسائل من سجل المحادثة
        for message in conversation_history[-10:]:
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        # إعداد بيانات الطلب
        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # إعداد الطلب إلى واجهة برمجة تطبيقات GitHub AI
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
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
        response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        if not response_text:
            return {
                "response": "لم يتم الحصول على رد من النموذج",
                "thinking_process": "حدث خطأ في الاتصال بالنموذج"
            }
        
        # إعداد الاستجابة
        return {
            "response": response_text,
            "thinking_process": combined_thinking
        }
        
    except requests.exceptions.RequestException as e:
        print(f"فشل طلب GitHub AI: {str(e)}. جاري المحاولة مرة أخرى...")
        
        try:
            # محاولة استخدام نقطة نهاية بديلة
            endpoint = endpoints[1]  # استخدام النقطة البديلة الأولى
            print(f"استخدام نقطة النهاية البديلة: {endpoint}")
            
            # إرسال الطلب مرة أخرى
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
                return {
                    "response": "لم يتم الحصول على رد من النموذج",
                    "thinking_process": "حدث خطأ في الاتصال بالنموذج"
                }
            
            # إنشاء عملية تفكير بديلة
            fallback_thinking = "عملية التفكير:\n"
            fallback_thinking += f"1. تم استلام الرسالة: '{user_message}'\n"
            fallback_thinking += "2. تم تحليل الرسالة باستخدام محرك التفكير\n"
            fallback_thinking += "3. تم إنشاء استجابة مناسبة\n"
            
            return {
                "response": ai_response,
                "thinking_process": combined_thinking
            }
            
        except requests.exceptions.RequestException as e2:
            print(f"فشل طلب GitHub AI البديل: {str(e2)}. جاري استخدام النقطة الثالثة...")
            
            try:
                # محاولة استخدام نقطة نهاية بديلة ثانية
                endpoint = endpoints[2]  # استخدام النقطة البديلة الثانية
                print(f"استخدام نقطة النهاية البديلة الثانية: {endpoint}")
                
                # إرسال الطلب مرة أخرى
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
                    return {
                        "response": "لم يتم الحصول على رد من النموذج",
                        "thinking_process": "حدث خطأ في الاتصال بالنموذج"
                    }
                
                # إنشاء عملية تفكير بديلة
                fallback_thinking = "عملية التفكير:\n"
                fallback_thinking += f"1. تم استلام الرسالة: '{user_message}'\n"
                fallback_thinking += "2. تم تحليل الرسالة باستخدام محرك التفكير\n"
                fallback_thinking += "3. تم إنشاء استجابة مناسبة\n"
                
                return {
                    "response": ai_response,
                    "thinking_process": combined_thinking
                }
                
            except Exception as e3:
                print(f"فشلت جميع محاولات الاتصال: {str(e3)}")
                return {
                    "response": "عذراً، حدث خطأ في الاتصال بالنموذج. يرجى المحاولة مرة أخرى لاحقاً.",
                    "thinking_process": "حدث خطأ في الاتصال بجميع نقاط النهاية المتاحة."
                }

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
            
            # تحويل التاريخ الميلادي إلى هجري
            hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
            
            # أسماء الأشهر الهجرية
            hijri_months = {
                1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني", 
                5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
                9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
            }
            
            # تنسيق التاريخ الهجري
            formatted_hijri_date = f"{hijri_date.day} {hijri_months[hijri_date.month]} {hijri_date.year}"
            
            # التحقق من طلب التاريخ الهجري
            is_hijri_request = False
            
            # فحص الرسالة الحالية
            if any(keyword in user_message.lower() for keyword in ['هجري', 'بالهجري', 'الهجري', 'إسلامي']):
                is_hijri_request = True
            
            # فحص سياق المحادثة السابقة إذا كانت الرسالة الحالية قصيرة
            if len(user_message.split()) <= 2 and not is_hijri_request:
                # البحث في آخر رسالتين من المحادثة
                for i in range(min(4, len(conversation_history))):
                    if i > 0 and conversation_history[-i]["role"] == "user":
                        prev_msg = conversation_history[-i]["content"].lower()
                        if any(keyword in prev_msg for keyword in ['تاريخ', 'اليوم', 'التاريخ']):
                            if any(keyword in user_message.lower() for keyword in ['هجري', 'بالهجري', 'الهجري', 'إسلامي']):
                                is_hijri_request = True
                                break
            
            # إعداد الاستجابة بناءً على نوع السؤال
            if is_hijri_request:
                return {
                    "response": f"التاريخ الهجري اليوم هو {formatted_hijri_date}.",
                    "thinking_process": "تحليل استعلام متعلق بالتاريخ والوقت:\n"
                }
            elif any(keyword in user_message for keyword in ['تاريخ', 'اليوم', 'التاريخ']):
                if any(keyword in user_message for keyword in ['هجري', 'بالهجري', 'الهجري', 'إسلامي']):
                    return {
                        "response": f"التاريخ الهجري اليوم هو {formatted_hijri_date}.",
                        "thinking_process": "تحليل استعلام متعلق بالتاريخ والوقت:\n"
                    }
                else:
                    return {
                        "response": f"اليوم هو {weekday}، {formatted_date}، والتاريخ الهجري الموافق هو {formatted_hijri_date}.",
                        "thinking_process": "تحليل استعلام متعلق بالتاريخ والوقت:\n"
                    }
            elif any(keyword in user_message for keyword in ['الوقت', 'الساعة']):
                return {
                    "response": f"الوقت الآن هو {formatted_time}.",
                    "thinking_process": "تحليل استعلام متعلق بالتاريخ والوقت:\n"
                }
            else:
                return {
                    "response": f"اليوم هو {weekday}، {formatted_date}، والتاريخ الهجري الموافق هو {formatted_hijri_date}، والوقت الآن هو {formatted_time}.",
                    "thinking_process": "تحليل استعلام متعلق بالتاريخ والوقت:\n"
                }
        
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
        
        thinking_process = "عملية البحث والتحليل:\n"
        thinking_process += f"1. تم استلام الاستعلام: '{user_message}'\n"
        thinking_process += "2. تم تحديد أن الاستعلام يتطلب بحثًا على الإنترنت\n"
        thinking_process += "3. جاري البحث عن معلومات دقيقة ومحدثة...\n"
        
        response = model.generate_content(prompt)
        
        # التحقق من وجود محتوى في الاستجابة
        if not response.text:
            return {
                "response": "لم يتم العثور على معلومات. يرجى إعادة صياغة طلبك.",
                "thinking_process": thinking_process + "4. لم يتم العثور على معلومات كافية. فشل البحث."
            }
        
        # تنظيف وتنسيق النص
        raw_info = response.text.strip()
        thinking_process += "4. تم العثور على معلومات ذات صلة\n"
        thinking_process += "5. تنظيم وتنسيق المعلومات للعرض\n"
        
        return {
            "response": raw_info,
            "thinking_process": thinking_process
        }
        
    except Exception as e:
        print(f"خطأ في استخدام Gemini مع البحث على الإنترنت: {str(e)}")
        return {
            "response": f"حدث خطأ أثناء البحث: {str(e)}",
            "thinking_process": f"حدث خطأ أثناء معالجة الاستعلام: {str(e)}"
        }

def analyze_and_respond(user_question, raw_info, conversation_history):
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
        قم بتحليل المعلومات التالية وإعادة صياغتها بشكل ذكي لتقديم إجابة على سؤال المستخدم.
        
        سؤال المستخدم: {user_question}
        
        المعلومات الخام:
        {raw_info}
        
        المطلوب:
        1. قم بتحليل المعلومات وتلخيصها بشكل ذكي.
        2. قدم إجابة مباشرة ومفيدة على سؤال المستخدم.
        3. تأكد من أن الإجابة شاملة وتغطي جميع جوانب السؤال.
        4. استخدم أسلوباً واضحاً وسهل الفهم.
        5. قدم الإجابة باللغة العربية الفصحى.
        
        ملاحظة: يجب أن تكون الإجابة دقيقة وموثوقة ومستندة إلى المعلومات المقدمة.
        """
        
        thinking_process = "عملية تحليل المعلومات والإجابة:\n"
        thinking_process += f"1. تحليل سؤال المستخدم: '{user_question}'\n"
        thinking_process += "2. مراجعة المعلومات الخام المتوفرة\n"
        thinking_process += "3. استخراج المعلومات ذات الصلة بالسؤال\n"
        thinking_process += "4. تنظيم المعلومات وتلخيصها\n"
        thinking_process += "5. صياغة إجابة شاملة ومباشرة\n"
        
        response = model.generate_content(prompt)
        
        # التحقق من وجود محتوى في الاستجابة
        if not response.text:
            return {
                "response": "لم أتمكن من تحليل المعلومات بشكل صحيح. يرجى إعادة صياغة سؤالك.",
                "thinking_process": thinking_process + "6. فشل في تحليل المعلومات وتقديم إجابة مناسبة."
            }
        
        # تنظيف وتنسيق النص
        answer = response.text.strip()
        thinking_process += "6. تم تقديم إجابة مناسبة بناءً على المعلومات المتاحة\n"
        
        return {
            "response": answer,
            "thinking_process": thinking_process
        }
        
    except Exception as e:
        print(f"خطأ في تحليل المعلومات: {str(e)}")
        return {
            "response": f"حدث خطأ أثناء تحليل المعلومات: {str(e)}",
            "thinking_process": f"حدث خطأ أثناء تحليل المعلومات: {str(e)}"
        }

def handle_date_time_query(user_message, conversation_history):
    """معالجة استفسارات التاريخ والوقت مع دعم التاريخ الهجري"""
    try:
        from datetime import datetime
        import pytz
        from hijri_converter import Gregorian, Hijri
        
        # الحصول على التاريخ والوقت الحاليين
        now = datetime.now()
        
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
        
        # تحويل التاريخ الميلادي إلى هجري
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        
        # أسماء الأشهر الهجرية
        hijri_months = {
            1: "محرم", 2: "صفر", 3: "ربيع الأول", 4: "ربيع الثاني", 
            5: "جمادى الأولى", 6: "جمادى الآخرة", 7: "رجب", 8: "شعبان",
            9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
        }
        
        # تنسيق التاريخ الهجري
        formatted_hijri_date = f"{hijri_date.day} {hijri_months[hijri_date.month]} {hijri_date.year}"
        
        # إعداد عملية التفكير
        thinking_process = "تحليل استعلام متعلق بالتاريخ والوقت:\n"
        thinking_process += "1. تم التعرف على استعلام متعلق بالتاريخ/الوقت\n"
        thinking_process += f"2. التاريخ الميلادي الحالي: {formatted_date}\n"
        thinking_process += f"3. اليوم الحالي: {weekday}\n"
        thinking_process += f"4. التاريخ الهجري الحالي: {formatted_hijri_date}\n"
        thinking_process += f"5. الوقت الحالي: {formatted_time}\n"
        
        # التحقق من طلب التاريخ الهجري
        is_hijri_request = any(keyword in user_message.lower() for keyword in ['هجري', 'بالهجري', 'الهجري', 'إسلامي'])
        
        # إعداد الاستجابة بناءً على نوع السؤال
        response_text = ""
        
        if is_hijri_request:
            response_text = f"التاريخ الهجري اليوم هو {formatted_hijri_date}."
            thinking_process += "6. تم تحديد أن الاستعلام متعلق بالتاريخ الهجري\n"
        elif any(keyword in user_message for keyword in ['تاريخ', 'اليوم', 'التاريخ']):
            response_text = f"اليوم هو {weekday}، {formatted_date}، والتاريخ الهجري الموافق هو {formatted_hijri_date}."
            thinking_process += "6. تم تحديد أن الاستعلام متعلق بالتاريخ\n"
        elif any(keyword in user_message for keyword in ['الوقت', 'الساعة']):
            response_text = f"الوقت الآن هو {formatted_time}."
            thinking_process += "6. تم تحديد أن الاستعلام متعلق بالوقت/الساعة\n"
        else:
            response_text = f"اليوم هو {weekday}، {formatted_date}، والتاريخ الهجري الموافق هو {formatted_hijri_date}، والوقت الآن هو {formatted_time}."
            thinking_process += "6. تم تحديد أن الاستعلام متعلق بكل من التاريخ والوقت\n"
        
        return {
            "response": response_text,
            "thinking_process": thinking_process
        }
        
    except Exception as e:
        print(f"خطأ في معالجة استعلام التاريخ والوقت: {str(e)}")
        return {
            "response": "عذراً، حدث خطأ أثناء معالجة استعلام التاريخ والوقت.",
            "thinking_process": f"حدث خطأ أثناء معالجة استعلام التاريخ والوقت: {str(e)}"
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='تشغيل تطبيق نور')
    parser.add_argument('--port', type=int, default=5010, help='رقم المنفذ للتشغيل')
    args = parser.parse_args()
    
    print(f"تم تشغيل نور (Noor) على الرابط: http://127.0.0.1:{args.port}")
    app.run(host='0.0.0.0', port=args.port)
