import os
import requests
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
import argparse
from datetime import datetime, timedelta
import pytz
from hijri_converter import Gregorian, Hijri
import re
import uuid

# تحميل المتغيرات البيئية
load_dotenv()

app = Flask(__name__)
app.config['APP_NAME'] = 'نور (Noor)'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default_secret_key_change_in_production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///noor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
db = SQLAlchemy(app)

# نماذج قاعدة البيانات
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversations = db.relationship('Conversation', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, default="محادثة جديدة")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' أو 'assistant'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

# إعداد مدير تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# التحقق من وجود مفتاح GitHub
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    print("تحذير: لم يتم تعيين GITHUB_TOKEN في ملف .env")

# إعداد مفتاح Google Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBiQN8UfRfH8M-IWGd-Nt_xSPZkTwqMWvs")
genai.configure(api_key=gemini_api_key)

# تكوين نظام الذاكرة المتقدم للمحادثة
class ConversationMemory:
    def __init__(self, max_messages=20, max_topics=5):
        self.messages = []  # سجل الرسائل الكامل
        self.topics = {}    # المواضيع المكتشفة في المحادثة
        self.entities = {}  # الكيانات المستخرجة من المحادثة
        self.max_messages = max_messages
        self.max_topics = max_topics
        self.importance_scores = {}  # درجات أهمية الرسائل
    
    def add_message(self, role, content):
        """إضافة رسالة جديدة إلى الذاكرة"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "id": len(self.messages)
        }
        self.messages.append(message)
        
        # تحديث المواضيع والكيانات
        self._update_topics_and_entities(message)
        
        # حساب درجة الأهمية
        self._calculate_importance(message)
        
        # الحفاظ على الحد الأقصى للرسائل
        if len(self.messages) > self.max_messages:
            # حذف الرسائل الأقل أهمية بدلاً من الأقدم فقط
            self._prune_messages()
    
    def _update_topics_and_entities(self, message):
        """تحديث المواضيع والكيانات المستخرجة من الرسالة"""
        content = message["content"].lower()
        
        # قائمة بالمواضيع المحتملة والكلمات المفتاحية المرتبطة بها
        potential_topics = {
            "تاريخ": ["تاريخ", "هجري", "ميلادي", "سنة", "شهر", "يوم"],
            "وقت": ["وقت", "ساعة", "دقيقة", "صباح", "مساء"],
            "طقس": ["طقس", "حرارة", "درجة", "مطر", "رياح", "جو"],
            "أخبار": ["خبر", "أخبار", "حدث", "عاجل", "تقرير"],
            "تقنية": ["تقنية", "برمجة", "حاسوب", "إنترنت", "ذكاء اصطناعي"],
            "دين": ["إسلام", "قرآن", "حديث", "صلاة", "دعاء", "رمضان"],
            "رياضة": ["رياضة", "كرة", "مباراة", "فريق", "لاعب"],
            "صحة": ["صحة", "مرض", "علاج", "دواء", "طبيب"],
            "تعليم": ["تعليم", "دراسة", "مدرسة", "جامعة", "طالب"]
        }
        
        # تحديث المواضيع
        for topic, keywords in potential_topics.items():
            for keyword in keywords:
                if keyword in content:
                    self.topics[topic] = self.topics.get(topic, 0) + 1
        
        # الحفاظ على الحد الأقصى للمواضيع
        if len(self.topics) > self.max_topics:
            # الاحتفاظ بالمواضيع الأكثر تكراراً فقط
            self.topics = dict(sorted(self.topics.items(), key=lambda x: x[1], reverse=True)[:self.max_topics])
        
        # استخراج الكيانات (مثل الأسماء والأماكن والتواريخ)
        # هذا تنفيذ مبسط، يمكن استخدام مكتبات NLP متقدمة مثل spaCy
        entities = self._extract_entities(content)
        for entity, entity_type in entities:
            if entity_type not in self.entities:
                self.entities[entity_type] = []
            if entity not in self.entities[entity_type]:
                self.entities[entity_type].append(entity)
    
    def _extract_entities(self, text):
        """استخراج الكيانات من النص (تنفيذ مبسط)"""
        entities = []
        
        # استخراج التواريخ المحتملة
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\d{1,2}\s+(?:يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                entities.append((match, "تاريخ"))
        
        # استخراج الأماكن المحتملة (قائمة مبسطة)
        places = ["الرياض", "جدة", "مكة", "المدينة", "الدمام", "السعودية", "مصر", "الإمارات"]
        for place in places:
            if place in text:
                entities.append((place, "مكان"))
        
        return entities
    
    def _calculate_importance(self, message):
        """حساب درجة أهمية الرسالة"""
        content = message["content"]
        importance = 1.0  # القيمة الافتراضية
        
        # الرسائل الطويلة قد تكون أكثر أهمية
        importance += min(len(content) / 100, 2.0)
        
        # الرسائل التي تحتوي على كلمات مفتاحية مهمة
        important_keywords = ["مهم", "ضروري", "عاجل", "احتاج", "ساعدني", "كيف", "لماذا", "متى"]
        for keyword in important_keywords:
            if keyword in content.lower():
                importance += 0.5
        
        # الرسائل الأحدث أكثر أهمية
        recency_factor = 1.0  # أحدث رسالة
        
        # تخزين درجة الأهمية
        self.importance_scores[message["id"]] = importance * recency_factor
    
    def _prune_messages(self):
        """حذف الرسائل الأقل أهمية للحفاظ على الحد الأقصى"""
        # ترتيب الرسائل حسب الأهمية
        sorted_messages = sorted(
            range(len(self.messages)), 
            key=lambda i: self.importance_scores.get(i, 0),
            reverse=True
        )
        
        # الاحتفاظ بالرسائل المهمة فقط
        keep_indices = sorted_messages[:self.max_messages]
        keep_indices.sort()  # إعادة ترتيبها حسب التسلسل الزمني
        
        self.messages = [self.messages[i] for i in keep_indices]
        
        # تحديث المعرفات
        for i, message in enumerate(self.messages):
            message["id"] = i
            self.importance_scores[i] = self.importance_scores.pop(message["id"], 1.0)
    
    def get_relevant_context(self, query, max_messages=10):
        """الحصول على السياق الأكثر صلة بالاستعلام"""
        if not self.messages:
            return []
        
        # حساب درجة التشابه بين الاستعلام وكل رسالة
        similarities = {}
        query_words = set(query.lower().split())
        
        for message in self.messages:
            content = message["content"].lower()
            content_words = set(content.split())
            
            # حساب تشابه جاكارد البسيط
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))
            
            similarity = intersection / union if union > 0 else 0
            
            # تعزيز أهمية الرسائل الحديثة
            recency_boost = 1.0 - (0.05 * (len(self.messages) - 1 - message["id"]))
            recency_boost = max(0.5, recency_boost)  # لا تقل عن 0.5
            
            # الدرجة النهائية تجمع بين التشابه والحداثة والأهمية
            final_score = (
                similarity * 0.5 + 
                recency_boost * 0.3 + 
                self.importance_scores.get(message["id"], 1.0) * 0.2
            )
            
            similarities[message["id"]] = final_score
        
        # ترتيب الرسائل حسب الصلة
        sorted_messages = sorted(
            self.messages, 
            key=lambda msg: similarities.get(msg["id"], 0),
            reverse=True
        )
        
        # إرجاع الرسائل الأكثر صلة
        return sorted_messages[:max_messages]
    
    def get_active_topics(self, top_n=3):
        """الحصول على المواضيع النشطة في المحادثة"""
        sorted_topics = sorted(self.topics.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:top_n]]
    
    def get_recent_entities(self, entity_type=None):
        """الحصول على الكيانات الحديثة من نوع معين"""
        if entity_type:
            return self.entities.get(entity_type, [])
        return self.entities
    
    def clear(self):
        """مسح الذاكرة"""
        self.messages = []
        self.topics = {}
        self.entities = {}
        self.importance_scores = {}

# إنشاء كائن الذاكرة
conversation_memory = ConversationMemory(max_messages=30, max_topics=10)

def enhance_query_with_context(user_message, conversation_context):
    """تحسين استعلام المستخدم باستخدام سياق المحادثة"""
    # إذا كانت الرسالة قصيرة جدًا، قد تكون متابعة لسؤال سابق
    if len(user_message.split()) <= 3:
        # البحث عن الضمائر والإشارات
        pronouns = ["هو", "هي", "هم", "هذا", "هذه", "ذلك", "تلك", "هؤلاء", "أولئك"]
        contains_pronoun = any(pronoun in user_message.lower().split() for pronoun in pronouns)
        
        # إذا كانت تحتوي على ضمير، ابحث عن المرجع في المحادثة السابقة
        if contains_pronoun and conversation_context:
            # ابحث عن آخر رسالة من المستخدم
            for msg in reversed(conversation_context):
                if msg["role"] == "user" and msg["content"] != user_message:
                    # دمج السؤال السابق مع السؤال الحالي
                    return f"{msg['content']} - {user_message}"
    
    # التعامل مع الأسئلة المتعلقة بالمواضيع النشطة
    active_topics = conversation_memory.get_active_topics()
    for topic in active_topics:
        topic_keywords = {
            "تاريخ": ["تاريخ", "هجري", "ميلادي", "سنة", "شهر", "يوم"],
            "وقت": ["وقت", "ساعة", "دقيقة", "صباح", "مساء"],
            "طقس": ["طقس", "حرارة", "درجة", "مطر", "رياح", "جو"],
            # ... إلخ
        }
        
        # إذا كان السؤال يتعلق بموضوع نشط، أضف سياقًا إضافيًا
        if topic in topic_keywords:
            for keyword in topic_keywords[topic]:
                if keyword in user_message.lower():
                    # ابحث عن آخر رسالة متعلقة بهذا الموضوع
                    for msg in reversed(conversation_context):
                        if msg["role"] == "user" and any(kw in msg["content"].lower() for kw in topic_keywords[topic]):
                            if msg["content"] != user_message:
                                return f"{user_message} (بناءً على سؤالك السابق: {msg['content']})"
    
    # التعامل مع الأسئلة التي تحتوي على كلمات مثل "أيضًا" أو "كذلك"
    follow_up_indicators = ["أيضا", "أيضًا", "كذلك", "بالإضافة", "وماذا عن", "وماذا بخصوص"]
    if any(indicator in user_message.lower() for indicator in follow_up_indicators) and conversation_context:
        # ابحث عن آخر رسالة من المستخدم
        for msg in reversed(conversation_context):
            if msg["role"] == "user" and msg["content"] != user_message:
                # دمج السؤال السابق مع السؤال الحالي
                return f"{msg['content']} وأيضًا {user_message}"
    
    # التعامل مع الأسئلة التي تبدأ بـ "و" أو "ثم"
    if user_message.strip().startswith(("و", "ثم", "بعد ذلك")) and conversation_context:
        # ابحث عن آخر رسالة من المستخدم
        for msg in reversed(conversation_context):
            if msg["role"] == "user" and msg["content"] != user_message:
                return f"{msg['content']} {user_message}"
    
    # إذا لم يتم تحسين الاستعلام، أعد الرسالة الأصلية
    return user_message

def resolve_references(text, conversation_context):
    """حل الإشارات والضمائر في النص"""
    # قائمة بالضمائر والإشارات الشائعة في اللغة العربية
    pronouns = {
        "هو": {"gender": "male", "count": "singular"},
        "هي": {"gender": "female", "count": "singular"},
        "هم": {"gender": "male", "count": "plural"},
        "هن": {"gender": "female", "count": "plural"},
        "هذا": {"gender": "male", "count": "singular", "distance": "near"},
        "هذه": {"gender": "female", "count": "singular", "distance": "near"},
        "ذلك": {"gender": "male", "count": "singular", "distance": "far"},
        "تلك": {"gender": "female", "count": "singular", "distance": "far"},
        "هؤلاء": {"count": "plural", "distance": "near"},
        "أولئك": {"count": "plural", "distance": "far"}
    }
    
    # استخراج الكيانات من المحادثة السابقة
    entities = {}
    for msg in conversation_context:
        # تحليل بسيط للكيانات (يمكن استخدام مكتبات NLP متقدمة)
        content_words = msg["content"].split()
        for i, word in enumerate(content_words):
            # تخمين الكيانات بناءً على الأحرف الكبيرة (في اللغة الإنجليزية) أو الكلمات المعروفة
            if word in ["الرياض", "جدة", "مكة", "السعودية", "مصر"]:
                entities[word] = {"type": "location", "gender": "female"}
            # يمكن إضافة المزيد من القواعد هنا
    
    # استبدال الضمائر والإشارات بمراجعها
    words = text.split()
    for i, word in enumerate(words):
        if word in pronouns:
            pronoun_info = pronouns[word]
            # البحث عن المرجع المناسب
            for entity, entity_info in entities.items():
                if "gender" in pronoun_info and "gender" in entity_info:
                    if pronoun_info["gender"] == entity_info["gender"]:
                        words[i] = entity
                        break
    
    return " ".join(words)

def fallback_to_openai(query, conversation_context):
    """استخدام OpenAI كخطة بديلة إذا فشل GitHub API"""
    try:
        # استخدام OpenAI API
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            return "لم يتم تكوين مفتاح OpenAI API. يرجى تحديث ملف .env"
        
        # إنشاء بنية الطلب
        messages = [
            {
                "role": "system",
                "content": "أنت ذكاء نور الخارق. ساعد المستخدم بإجابات مختصرة ومفيدة. تذكر المحادثة السابقة وحافظ على سياق المحادثة."
            }
        ]
        
        # إضافة سياق المحادثة
        for msg in conversation_context:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # إضافة سؤال المستخدم
        messages.append({
            "role": "user",
            "content": query
        })
        
        headers = {
            'Authorization': f'Bearer {openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 800
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"خطأ في OpenAI API: {response.status_code} - {response.text}")
            return "عذراً، لم أتمكن من الحصول على إجابة. يرجى المحاولة مرة أخرى لاحقًا."
    
    except Exception as e:
        print(f"خطأ في OpenAI API: {str(e)}")
        return f"عذراً، حدث خطأ: {str(e)}"

@app.route('/')
def index():
    # إعادة تعيين الذاكرة عند بدء جلسة جديدة
    conversation_memory.clear()
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('كلمات المرور غير متطابقة')
            return render_template('register.html')
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل')
            return render_template('register.html')
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح، يمكنك الآن تسجيل الدخول')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return render_template('dashboard.html', conversations=conversations)

@app.route('/conversation/new', methods=['POST'])
@login_required
def new_conversation():
    conversation = Conversation(user_id=current_user.id)
    db.session.add(conversation)
    db.session.commit()
    return redirect(url_for('conversation', conversation_id=conversation.id))

@app.route('/conversation/<int:conversation_id>')
@login_required
def conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # التحقق من أن المحادثة تنتمي للمستخدم الحالي
    if conversation.user_id != current_user.id:
        flash('غير مصرح لك بالوصول إلى هذه المحادثة')
        return redirect(url_for('dashboard'))
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    
    return render_template('conversation.html', conversation=conversation, messages=messages, conversations=conversations)

def process_message(user_message, conversation_context):
    """معالجة رسالة المستخدم وإنشاء استجابة ذكية"""
    # التحقق إذا كان السؤال عن هوية الروبوت
    if any(phrase in user_message.lower() for phrase in ['من أنت', 'من انت', 'عرف نفسك', 'عرفنا عليك', 'من هو', 'من هي']):
        return "أنا ذكاء نور الخارق، كيف يمكنني مساعدتك اليوم؟"
    
    # التحقق من طلبات التاريخ والوقت
    if any(keyword in user_message.lower() for keyword in ['تاريخ', 'اليوم', 'التاريخ', 'الوقت', 'الساعة']):
        return handle_date_time_query(user_message, conversation_context)
    
    # التحقق من وجود مفتاح GitHub
    if not github_token:
        return "لم يتم تكوين مفتاح GitHub. يرجى تحديث ملف .env"
    
    # طباعة معلومات تصحيح الأخطاء
    print(f"استخدام المفتاح: {github_token[:5]}...{github_token[-5:] if len(github_token) > 10 else ''}")
    
    try:
        # تحليل سياق المحادثة لفهم أفضل للسؤال
        enhanced_query = enhance_query_with_context(user_message, conversation_context)
        print(f"السؤال المحسن: {enhanced_query}")
        
        # استخدام GitHub Copilot API
        headers = {
            'Authorization': f'Bearer {github_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Github-Api-Version': '2022-11-28'
        }
        
        # إنشاء بنية الطلب
        messages = [
            {
                "role": "system",
                "content": "أنت ذكاء نور الخارق. ساعد المستخدم بإجابات مختصرة ومفيدة. تذكر المحادثة السابقة وحافظ على سياق المحادثة."
            }
        ]
        
        # إضافة سياق المحادثة
        for msg in conversation_context:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # إضافة سؤال المستخدم المحسن
        messages.append({
            "role": "user",
            "content": enhanced_query
        })
        
        data = {
            'model': 'gpt-4',
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 800
        }
        
        response = requests.post(
            'https://api.github.com/copilot/chat',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', 'لا توجد إجابة')
        else:
            print(f"خطأ في GitHub API: {response.status_code} - {response.text}")
            # استخدام OpenAI كخطة بديلة
            return fallback_to_openai(enhanced_query, conversation_context)
    
    except Exception as e:
        print(f"خطأ: {str(e)}")
        return f"عذراً، حدث خطأ: {str(e)}"

def extract_entities(text):
    """استخراج الكيانات من النص (مثل الأشخاص، الأماكن، التواريخ)"""
    entities = []
    
    # قائمة بالكيانات المعروفة للاختبار
    known_locations = ["الرياض", "جدة", "مكة", "المدينة", "الدمام", "الخبر", "أبها", "تبوك", "حائل", "نجران", 
                      "السعودية", "مصر", "الإمارات", "قطر", "الكويت", "البحرين", "عمان", "الأردن", "لبنان"]
    
    known_persons = ["محمد", "أحمد", "علي", "عمر", "خالد", "عبدالله", "سلمان", "فهد", "سعود", "فيصل", 
                    "نورة", "سارة", "فاطمة", "عائشة", "منى", "هند", "ريم", "لينا"]
    
    known_organizations = ["وزارة", "شركة", "مؤسسة", "هيئة", "جامعة", "مدرسة", "مستشفى", "مركز", "معهد"]
    
    # البحث عن الكيانات في النص
    words = text.split()
    for word in words:
        # تنظيف الكلمة من علامات الترقيم
        clean_word = word.strip(".,!?؟،:")
        
        # التحقق من الأماكن
        for location in known_locations:
            if location in clean_word:
                entities.append({"type": "location", "value": location})
        
        # التحقق من الأشخاص
        for person in known_persons:
            if person in clean_word:
                entities.append({"type": "person", "value": person})
        
        # التحقق من المنظمات
        for org in known_organizations:
            if org in clean_word:
                entities.append({"type": "organization", "value": clean_word})
    
    # البحث عن التواريخ (تنفيذ بسيط)
    date_indicators = ["يوم", "شهر", "سنة", "تاريخ", "الأسبوع", "الماضي", "القادم", "الحالي"]
    for i, word in enumerate(words):
        if any(indicator in word for indicator in date_indicators):
            date_entity = " ".join(words[max(0, i-1):min(len(words), i+3)])
            entities.append({"type": "date", "value": date_entity})
    
    # إزالة التكرارات
    unique_entities = []
    seen = set()
    for entity in entities:
        key = f"{entity['type']}:{entity['value']}"
        if key not in seen:
            seen.add(key)
            unique_entities.append(entity)
    
    return unique_entities

def extract_topics(text):
    """استخراج المواضيع من النص"""
    topics = []
    
    # قائمة بالمواضيع المعروفة وكلماتها المفتاحية
    topic_keywords = {
        "تاريخ": ["تاريخ", "هجري", "ميلادي", "سنة", "شهر", "يوم"],
        "وقت": ["وقت", "ساعة", "دقيقة", "صباح", "مساء"],
        "طقس": ["طقس", "حرارة", "درجة", "مطر", "رياح", "جو"],
        "رياضة": ["كرة", "مباراة", "فريق", "لاعب", "بطولة", "دوري"],
        "تقنية": ["حاسوب", "هاتف", "تطبيق", "برنامج", "إنترنت", "تقنية", "ذكاء اصطناعي"],
        "صحة": ["صحة", "مرض", "علاج", "دواء", "طبيب"],
        "تعليم": ["تعليم", "مدرسة", "جامعة", "طالب", "معلم", "دراسة", "امتحان"],
        "اقتصاد": ["اقتصاد", "مال", "سوق", "شركة", "استثمار", "سهم", "عملة"],
        "سفر": ["سفر", "سياحة", "فندق", "رحلة", "مطار", "تذكرة", "وجهة"],
        "طعام": ["طعام", "أكل", "وصفة", "مطعم", "طبخ", "مكونات"]
    }
    
    # البحث عن المواضيع في النص
    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            if keyword in text.lower():
                topics.append(topic)
                break
    
    return topics

def handle_date_time_query(user_message, conversation_context):
    """معالجة استعلامات التاريخ والوقت"""
    from datetime import datetime
    import pytz
    from hijri_converter import Gregorian
    
    # تحديد المنطقة الزمنية للمملكة العربية السعودية
    saudi_tz = pytz.timezone('Asia/Riyadh')
    now = datetime.now(saudi_tz)
    
    # تحويل التاريخ الميلادي إلى هجري
    hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
    
    # تنسيق التاريخ والوقت
    gregorian_date_str = now.strftime("%Y-%m-%d")
    hijri_date_str = f"{hijri_date.year}-{hijri_date.month}-{hijri_date.day}"
    time_str = now.strftime("%H:%M:%S")
    
    # تحديد نوع الاستعلام
    if any(keyword in user_message.lower() for keyword in ['تاريخ', 'اليوم', 'التاريخ']):
        if 'هجري' in user_message.lower():
            return f"التاريخ الهجري اليوم هو: {hijri_date_str}"
        elif 'ميلادي' in user_message.lower():
            return f"التاريخ الميلادي اليوم هو: {gregorian_date_str}"
        else:
            return f"اليوم هو: {gregorian_date_str} ميلادي، الموافق {hijri_date_str} هجري"
    
    elif any(keyword in user_message.lower() for keyword in ['الوقت', 'الساعة']):
        return f"الوقت الآن هو: {time_str}"
    
    else:
        return f"اليوم هو: {gregorian_date_str} ميلادي، الموافق {hijri_date_str} هجري\nالوقت الآن هو: {time_str}"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # الحصول على بيانات الطلب
        data = request.get_json()
        user_message = data.get('message', '')
        
        # التحقق من وجود رسالة
        if not user_message:
            return jsonify({'error': 'الرسالة مطلوبة'}), 400
        
        # الحصول على سجل المحادثة من الجلسة أو إنشاء سجل جديد
        conversation_history = session.get('conversation_history', [])
        
        # إضافة رسالة المستخدم إلى سجل المحادثة
        conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # تحديث ذاكرة المحادثة
        conversation_memory.add_message("user", user_message)
        
        # استخراج الكيانات والمواضيع من رسالة المستخدم
        entities = extract_entities(user_message)
        topics = extract_topics(user_message)
        
        # تحديث الكيانات والمواضيع في ذاكرة المحادثة
        for entity in entities:
            conversation_memory.add_entity(entity)
        
        for topic in topics:
            conversation_memory.add_topic(topic)
        
        # الحصول على استجابة من نموذج الذكاء الاصطناعي
        ai_response = process_message(user_message, conversation_history)
        
        # إضافة استجابة النموذج إلى سجل المحادثة
        conversation_history.append({
            "role": "assistant",
            "content": ai_response
        })
        
        # تحديث ذاكرة المحادثة بالاستجابة
        conversation_memory.add_message("assistant", ai_response)
        
        # تحديث سجل المحادثة في الجلسة
        session['conversation_history'] = conversation_history
        
        # إرجاع الاستجابة
        return jsonify({
            'response': ai_response,
            'context': {
                'active_topics': conversation_memory.get_active_topics(),
                'recent_entities': conversation_memory.get_recent_entities(5)
            }
        })
    
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'حدث خطأ في معالجة طلبك'}), 500

@app.route('/api/conversation/<int:conversation_id>/messages', methods=['POST'])
@login_required
def add_message_to_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # التحقق من أن المحادثة تنتمي للمستخدم الحالي
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه المحادثة'}), 403
    
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'الرسالة مطلوبة'}), 400
    
    # إنشاء رسالة جديدة من المستخدم
    user_msg = Message(content=user_message, role='user', conversation_id=conversation_id)
    db.session.add(user_msg)
    
    # تحديث وقت آخر تعديل للمحادثة
    conversation.updated_at = datetime.utcnow()
    
    # الحصول على جميع رسائل المحادثة لبناء السياق
    conversation_history = []
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    
    for msg in messages:
        conversation_history.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # إضافة رسالة المستخدم الحالية إلى السياق
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # الحصول على استجابة من نموذج الذكاء الاصطناعي
    ai_response = process_message(user_message, conversation_history)
    
    # إنشاء رسالة جديدة من المساعد
    assistant_msg = Message(content=ai_response, role='assistant', conversation_id=conversation_id)
    db.session.add(assistant_msg)
    
    # تحديث عنوان المحادثة إذا كانت المحادثة جديدة (أول رسالة)
    if len(messages) == 0:
        # استخدام أول 30 حرف من رسالة المستخدم كعنوان للمحادثة
        title = user_message[:30] + ('...' if len(user_message) > 30 else '')
        conversation.title = title
    
    db.session.commit()
    
    return jsonify({
        'user_message': user_msg.to_dict(),
        'assistant_message': assistant_msg.to_dict()
    })

@app.route('/api/conversation/<int:conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # التحقق من أن المحادثة تنتمي للمستخدم الحالي
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه المحادثة'}), 403
    
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    return jsonify([msg.to_dict() for msg in messages])

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_user_conversations():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.updated_at.desc()).all()
    return jsonify([{
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at.isoformat(),
        'updated_at': conv.updated_at.isoformat()
    } for conv in conversations])

@app.route('/api/conversation/<int:conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # التحقق من أن المحادثة تنتمي للمستخدم الحالي
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه المحادثة'}), 403
    
    db.session.delete(conversation)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/conversation/<int:conversation_id>/title', methods=['PUT'])
@login_required
def update_conversation_title(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    
    # التحقق من أن المحادثة تنتمي للمستخدم الحالي
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'غير مصرح لك بالوصول إلى هذه المحادثة'}), 403
    
    data = request.get_json()
    new_title = data.get('title', '')
    
    if not new_title:
        return jsonify({'error': 'العنوان مطلوب'}), 400
    
    conversation.title = new_title
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # إنشاء قاعدة البيانات إذا لم تكن موجودة
    with app.app_context():
        db.create_all()
        
    parser = argparse.ArgumentParser(description='تشغيل تطبيق نور')
    parser.add_argument('--port', type=int, default=5010, help='رقم المنفذ للتشغيل')
    parser.add_argument('--debug', action='store_true', help='تشغيل في وضع التصحيح')
    args = parser.parse_args()
    
    app.run(debug=args.debug, port=args.port)
