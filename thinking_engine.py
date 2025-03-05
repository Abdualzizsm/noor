import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ThinkingStep:
    name: str
    description: str
    result: str
    confidence: float
    timestamp: str

class ThinkingEngine:
    def __init__(self):
        self.thinking_steps = []
        self.context = {}
        self.memory_cache = {}  # إضافة ذاكرة مؤقتة لتخزين نتائج التفكير السابقة
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """تحليل السؤال وتحديد نوعه ومتطلباته"""
        # تحديد نوع السؤال (استفسار، مشكلة، طلب معلومات، إلخ)
        question_types = {
            'ما': 'information_query',
            'كيف': 'how_to',
            'لماذا': 'explanation',
            'متى': 'time_query',
            'أين': 'location_query',
            'هل': 'yes_no_query',
            'من': 'person_query'
        }
        
        question_type = 'general_query'
        for keyword, q_type in question_types.items():
            if question.startswith(keyword):
                question_type = q_type
                break
        
        # تحليل الكلمات المفتاحية
        keywords = [word for word in question.split() if len(word) > 3]
        
        # تحليل متقدم للسؤال - إضافة تحليل للتعقيد والسياق
        complexity_score = self._calculate_complexity(question)
        context_needed = self._determine_context_needed(question, question_type)
        
        return {
            'type': question_type,
            'keywords': keywords,
            'complexity': complexity_score,
            'context_needed': context_needed,
            'requires_web_search': any(word in question.lower() for word in ['احدث', 'جديد', 'اخر', 'الان'])
        }
    
    def _calculate_complexity(self, question: str) -> float:
        """حساب درجة تعقيد السؤال بناءً على عدة عوامل"""
        # عوامل التعقيد: طول السؤال، تنوع المفردات، وجود مصطلحات متخصصة، إلخ
        words = question.split()
        unique_words = set(words)
        
        # حساب نسبة الكلمات الفريدة (مؤشر على تنوع المفردات)
        vocabulary_diversity = len(unique_words) / len(words) if words else 0
        
        # حساب درجة التعقيد الإجمالية (1-10)
        complexity = min(10, (len(words) / 5) + (vocabulary_diversity * 5))
        
        return complexity
    
    def _determine_context_needed(self, question: str, question_type: str) -> List[str]:
        """تحديد أنواع السياق المطلوبة للإجابة على السؤال"""
        context_types = []
        
        # تحديد السياق بناءً على نوع السؤال
        if question_type == 'explanation':
            context_types.extend(['historical', 'causal'])
        elif question_type == 'how_to':
            context_types.extend(['procedural', 'requirements'])
        elif question_type == 'time_query':
            context_types.append('temporal')
        elif question_type == 'location_query':
            context_types.append('spatial')
        
        # إضافة سياقات إضافية بناءً على كلمات مفتاحية
        if any(word in question.lower() for word in ['مقارنة', 'أفضل', 'الفرق']):
            context_types.append('comparative')
        
        if any(word in question.lower() for word in ['تاريخ', 'قديم', 'تطور']):
            context_types.append('historical')
        
        return context_types
    
    def plan_solution(self, question_analysis: Dict[str, Any]) -> List[str]:
        """تخطيط خطوات الحل بناءً على تحليل السؤال"""
        steps = ['تحليل السؤال']
        
        # إضافة خطوات بناءً على تعقيد السؤال
        complexity = question_analysis['complexity']
        
        if complexity > 7:
            # للأسئلة المعقدة، نضيف خطوات تفكير إضافية
            steps.append('تقسيم المشكلة إلى أجزاء أصغر')
        
        if question_analysis['requires_web_search']:
            steps.append('البحث عن معلومات حديثة')
        
        # إضافة خطوات بناءً على السياق المطلوب
        for context_type in question_analysis.get('context_needed', []):
            if context_type == 'historical':
                steps.append('جمع المعلومات التاريخية')
            elif context_type == 'comparative':
                steps.append('إجراء تحليل مقارن')
            elif context_type == 'causal':
                steps.append('تحليل العلاقات السببية')
        
        # إضافة خطوات بناءً على نوع السؤال
        if question_analysis['type'] == 'how_to':
            steps.extend([
                'تحديد المتطلبات الأساسية',
                'تقسيم المهمة إلى خطوات',
                'شرح كل خطوة بالتفصيل',
                'تقديم أمثلة عملية'
            ])
        elif question_analysis['type'] == 'explanation':
            steps.extend([
                'جمع المعلومات الأساسية',
                'تحليل العلاقات السببية',
                'تقديم تفسير منطقي',
                'دعم التفسير بالأدلة'
            ])
        
        # إضافة خطوة للتقييم الذاتي
        steps.append('مراجعة وتقييم الإجابة')
        steps.append('صياغة الإجابة النهائية')
        
        return steps
    
    def execute_thinking_step(self, step: str, context: Dict[str, Any]) -> ThinkingStep:
        """تنفيذ خطوة تفكير محددة وتسجيل النتيجة"""
        # التحقق من وجود نتائج مخزنة مسبقاً في الذاكرة المؤقتة
        cache_key = f"{step}_{hash(json.dumps(context, sort_keys=True))}"
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]
        
        # تنفيذ الخطوة بناءً على نوعها
        result = ""
        confidence = 0.0
        
        if step == 'تحليل السؤال':
            result = f"تم تحليل السؤال: نوع السؤال {context.get('type', 'غير محدد')}, " \
                     f"الكلمات المفتاحية: {', '.join(context.get('keywords', []))}"
            confidence = 0.9
        elif step == 'تقسيم المشكلة إلى أجزاء أصغر':
            # تقسيم المشكلة إلى أجزاء أصغر
            sub_problems = self._break_down_problem(context)
            result = f"تم تقسيم المشكلة إلى {len(sub_problems)} أجزاء: {', '.join(sub_problems)}"
            confidence = 0.85
        elif step == 'البحث عن معلومات حديثة':
            result = "تم البحث عن معلومات حديثة (محاكاة)"
            confidence = 0.7
        elif step == 'مراجعة وتقييم الإجابة':
            result = "تم مراجعة الإجابة وتقييمها للتأكد من دقتها واكتمالها"
            confidence = 0.8
        else:
            # خطوات أخرى
            result = f"نتيجة تنفيذ خطوة: {step}"
            confidence = 0.75
        
        thinking_step = ThinkingStep(
            name=step,
            description=f"تنفيذ {step}",
            result=result,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
        
        # تخزين النتيجة في الذاكرة المؤقتة
        self.memory_cache[cache_key] = thinking_step
        
        # إضافة الخطوة إلى سجل التفكير
        self.thinking_steps.append(thinking_step)
        return thinking_step
    
    def _break_down_problem(self, context: Dict[str, Any]) -> List[str]:
        """تقسيم المشكلة المعقدة إلى مشاكل فرعية أبسط"""
        # هذه مجرد محاكاة، في التطبيق الفعلي يمكن استخدام خوارزميات أكثر تعقيداً
        sub_problems = []
        
        if 'keywords' in context:
            for keyword in context['keywords']:
                sub_problems.append(f"فهم {keyword}")
        
        if context.get('type') == 'how_to':
            sub_problems.extend(['تحديد المتطلبات', 'تحديد الخطوات', 'تحديد الموارد'])
        elif context.get('type') == 'explanation':
            sub_problems.extend(['تحديد المفاهيم الأساسية', 'تحديد العلاقات', 'تحديد الأمثلة'])
        
        return sub_problems
    
    def evaluate_solution(self) -> Dict[str, Any]:
        """تقييم الحل النهائي وحساب درجة الثقة الإجمالية"""
        if not self.thinking_steps:
            return {
                'confidence': 0.0,
                'complete': False,
                'missing_steps': ['لم يتم تنفيذ أي خطوات']
            }
        
        # حساب متوسط درجة الثقة (مع إعطاء وزن أكبر للخطوات الأخيرة)
        total_confidence = 0
        total_weight = 0
        
        for i, step in enumerate(self.thinking_steps):
            # إعطاء وزن أكبر للخطوات الأخيرة
            weight = 1 + (i / len(self.thinking_steps))
            total_confidence += step.confidence * weight
            total_weight += weight
        
        avg_confidence = total_confidence / total_weight if total_weight > 0 else 0
        
        # تحديد الخطوات المفقودة أو غير المكتملة
        expected_steps = {'تحليل السؤال', 'صياغة الإجابة النهائية', 'مراجعة وتقييم الإجابة'}
        completed_steps = {step.name for step in self.thinking_steps}
        missing_steps = expected_steps - completed_steps
        
        # تقييم جودة الحل
        quality_score = self._evaluate_solution_quality()
        
        return {
            'confidence': avg_confidence,
            'complete': len(missing_steps) == 0,
            'missing_steps': list(missing_steps),
            'steps_count': len(self.thinking_steps),
            'quality_score': quality_score
        }
    
    def _evaluate_solution_quality(self) -> float:
        """تقييم جودة الحل بناءً على عدة معايير"""
        # هذه مجرد محاكاة، في التطبيق الفعلي يمكن استخدام معايير أكثر تعقيداً
        
        # عدد الخطوات (المزيد من الخطوات يشير إلى تفكير أكثر شمولاً)
        steps_score = min(1.0, len(self.thinking_steps) / 10)
        
        # تنوع الخطوات
        unique_steps = len(set(step.name for step in self.thinking_steps))
        diversity_score = min(1.0, unique_steps / 5)
        
        # متوسط الثقة
        confidence_score = sum(step.confidence for step in self.thinking_steps) / len(self.thinking_steps) if self.thinking_steps else 0
        
        # الحساب النهائي (مع أوزان مختلفة)
        quality_score = (steps_score * 0.3) + (diversity_score * 0.3) + (confidence_score * 0.4)
        
        return quality_score
    
    def format_thinking_process(self) -> str:
        """تنسيق عملية التفكير بشكل مفهوم للعرض"""
        if not self.thinking_steps:
            return "لم يتم تنفيذ أي خطوات تفكير بعد."
        
        formatted_output = "خطوات التفكير:\n\n"
        for i, step in enumerate(self.thinking_steps, 1):
            formatted_output += f"{i}. {step.name}\n"
            formatted_output += f"   - {step.description}\n"
            formatted_output += f"   - النتيجة: {step.result}\n"
            formatted_output += f"   - درجة الثقة: {step.confidence:.2%}\n\n"
        
        evaluation = self.evaluate_solution()
        formatted_output += f"\nالتقييم النهائي:\n"
        formatted_output += f"- درجة الثقة الإجمالية: {evaluation['confidence']:.2%}\n"
        formatted_output += f"- جودة الحل: {evaluation.get('quality_score', 0):.2%}\n"
        formatted_output += f"- اكتمال الحل: {'نعم' if evaluation['complete'] else 'لا'}\n"
        
        if evaluation['missing_steps']:
            formatted_output += "- الخطوات المفقودة:\n"
            for step in evaluation['missing_steps']:
                formatted_output += f"  * {step}\n"
        
        return formatted_output
    
    def process_large_data(self, data: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """معالجة البيانات الكبيرة على دفعات لتجنب مشاكل الذاكرة"""
        results = []
        
        # معالجة البيانات على دفعات
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            batch_results = self._process_data_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _process_data_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """معالجة دفعة من البيانات"""
        results = []
        
        for item in batch:
            # معالجة كل عنصر في الدفعة
            processed_item = self._process_single_item(item)
            results.append(processed_item)
        
        return results
    
    def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة عنصر واحد من البيانات"""
        # هذه مجرد محاكاة، في التطبيق الفعلي يمكن تنفيذ منطق معالجة أكثر تعقيداً
        processed_item = item.copy()
        
        # إضافة بعض المعلومات المستخلصة
        if 'text' in item:
            processed_item['analysis'] = self.analyze_question(item['text'])
        
        return processed_item
    
    def clear_memory_cache(self):
        """مسح الذاكرة المؤقتة لتحرير الموارد"""
        self.memory_cache.clear()
