import json
from typing import List, Dict, Any
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
        
        return {
            'type': question_type,
            'keywords': keywords,
            'complexity': len(question.split()),
            'requires_web_search': any(word in question.lower() for word in ['احدث', 'جديد', 'اخر', 'الان'])
        }
    
    def plan_solution(self, question_analysis: Dict[str, Any]) -> List[str]:
        """تخطيط خطوات الحل بناءً على تحليل السؤال"""
        steps = ['تحليل السؤال']
        
        if question_analysis['requires_web_search']:
            steps.append('البحث عن معلومات حديثة')
        
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
        
        steps.append('صياغة الإجابة النهائية')
        return steps
    
    def execute_thinking_step(self, step: str, context: Dict[str, Any]) -> ThinkingStep:
        """تنفيذ خطوة تفكير محددة وتسجيل النتيجة"""
        # هنا سيتم تنفيذ المنطق الخاص بكل خطوة
        # حالياً نقوم بتنفيذ نموذج بسيط
        
        result = f"نتيجة تنفيذ خطوة: {step}"
        confidence = 0.8  # سيتم حساب هذه القيمة بناءً على عوامل مختلفة
        
        thinking_step = ThinkingStep(
            name=step,
            description=f"تنفيذ {step}",
            result=result,
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )
        
        self.thinking_steps.append(thinking_step)
        return thinking_step
    
    def evaluate_solution(self) -> Dict[str, Any]:
        """تقييم الحل النهائي وحساب درجة الثقة الإجمالية"""
        if not self.thinking_steps:
            return {
                'confidence': 0.0,
                'complete': False,
                'missing_steps': ['لم يتم تنفيذ أي خطوات']
            }
        
        # حساب متوسط درجة الثقة
        avg_confidence = sum(step.confidence for step in self.thinking_steps) / len(self.thinking_steps)
        
        # تحديد الخطوات المفقودة أو غير المكتملة
        expected_steps = {'تحليل السؤال', 'صياغة الإجابة النهائية'}
        completed_steps = {step.name for step in self.thinking_steps}
        missing_steps = expected_steps - completed_steps
        
        return {
            'confidence': avg_confidence,
            'complete': len(missing_steps) == 0,
            'missing_steps': list(missing_steps),
            'steps_count': len(self.thinking_steps)
        }
    
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
        formatted_output += f"- اكتمال الحل: {'نعم' if evaluation['complete'] else 'لا'}\n"
        
        if evaluation['missing_steps']:
            formatted_output += "- الخطوات المفقودة:\n"
            for step in evaluation['missing_steps']:
                formatted_output += f"  * {step}\n"
        
        return formatted_output
