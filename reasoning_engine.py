import json
import re
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
import networkx as nx
import numpy as np
from datetime import datetime

@dataclass
class Concept:
    """تمثيل المفاهيم في قاعدة المعرفة"""
    id: str
    name: str
    description: str
    category: str
    related_concepts: List[str] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.related_concepts is None:
            self.related_concepts = []
        if self.attributes is None:
            self.attributes = {}


@dataclass
class Relation:
    """تمثيل العلاقات بين المفاهيم"""
    source: str
    target: str
    relation_type: str
    strength: float
    description: str = ""
    bidirectional: bool = False


@dataclass
class Inference:
    """تمثيل الاستنتاجات المنطقية"""
    premises: List[str]
    conclusion: str
    confidence: float
    reasoning_path: List[Tuple[str, str, str]]
    timestamp: str


class KnowledgeGraph:
    """قاعدة المعرفة المنظمة كشبكة معرفية"""
    
    def __init__(self):
        self.concepts = {}  # id -> Concept
        self.graph = nx.DiGraph()
        
    def add_concept(self, concept: Concept) -> bool:
        """إضافة مفهوم جديد إلى قاعدة المعرفة"""
        if concept.id in self.concepts:
            return False
        
        self.concepts[concept.id] = concept
        self.graph.add_node(concept.id, 
                           name=concept.name, 
                           category=concept.category,
                           description=concept.description)
        return True
    
    def add_relation(self, relation: Relation) -> bool:
        """إضافة علاقة بين مفهومين"""
        if relation.source not in self.concepts or relation.target not in self.concepts:
            return False
        
        self.graph.add_edge(relation.source, relation.target, 
                           relation_type=relation.relation_type,
                           strength=relation.strength,
                           description=relation.description)
        
        if relation.bidirectional:
            self.graph.add_edge(relation.target, relation.source, 
                               relation_type=relation.relation_type,
                               strength=relation.strength,
                               description=relation.description)
        
        return True
    
    def get_related_concepts(self, concept_id: str, max_depth: int = 2) -> Dict[str, float]:
        """الحصول على المفاهيم المرتبطة بمفهوم معين حتى عمق محدد"""
        if concept_id not in self.concepts:
            return {}
        
        related = {}
        visited = {concept_id}
        queue = [(concept_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            for neighbor in self.graph.neighbors(current_id):
                if neighbor not in visited:
                    edge_data = self.graph.get_edge_data(current_id, neighbor)
                    strength = edge_data.get('strength', 0.5)
                    decay = 0.8 ** depth  # تقليل القوة مع زيادة العمق
                    
                    related[neighbor] = strength * decay
                    visited.add(neighbor)
                    
                    if depth < max_depth:
                        queue.append((neighbor, depth + 1))
        
        return related
    
    def find_paths(self, source: str, target: str, max_depth: int = 3) -> List[List[Tuple[str, str, str]]]:
        """البحث عن المسارات بين مفهومين"""
        if source not in self.concepts or target not in self.concepts:
            return []
        
        paths = []
        for path in nx.all_simple_paths(self.graph, source, target, cutoff=max_depth):
            path_with_relations = []
            for i in range(len(path) - 1):
                edge_data = self.graph.get_edge_data(path[i], path[i+1])
                relation_type = edge_data.get('relation_type', 'related_to')
                path_with_relations.append((path[i], relation_type, path[i+1]))
            paths.append(path_with_relations)
        
        return paths


class ReasoningEngine:
    """محرك الاستدلال المنطقي"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.inferences = []
        
    def extract_concepts_from_text(self, text: str) -> List[str]:
        """استخراج المفاهيم من النص"""
        # هذه نسخة مبسطة، يمكن استخدام تقنيات NLP أكثر تقدماً
        # مثل استخراج الكيانات المسماة أو التحليل الدلالي
        
        # استخراج الكلمات المهمة (أكثر من 3 أحرف)
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        # البحث عن تطابقات مع المفاهيم الموجودة
        matched_concepts = []
        
        for word in words:
            for concept_id, concept in self.knowledge_graph.concepts.items():
                if word in concept.name.lower() or word in concept.description.lower():
                    matched_concepts.append(concept_id)
        
        return list(set(matched_concepts))
    
    def identify_relations(self, concept_ids: List[str]) -> List[Relation]:
        """تحديد العلاقات بين المفاهيم المستخرجة"""
        relations = []
        
        for i, source_id in enumerate(concept_ids):
            for target_id in concept_ids[i+1:]:
                # البحث عن علاقات مباشرة
                if self.knowledge_graph.graph.has_edge(source_id, target_id):
                    edge_data = self.knowledge_graph.graph.get_edge_data(source_id, target_id)
                    relation = Relation(
                        source=source_id,
                        target=target_id,
                        relation_type=edge_data.get('relation_type', 'related_to'),
                        strength=edge_data.get('strength', 0.5),
                        description=edge_data.get('description', '')
                    )
                    relations.append(relation)
                
                # البحث عن علاقات في الاتجاه المعاكس
                elif self.knowledge_graph.graph.has_edge(target_id, source_id):
                    edge_data = self.knowledge_graph.graph.get_edge_data(target_id, source_id)
                    relation = Relation(
                        source=target_id,
                        target=source_id,
                        relation_type=edge_data.get('relation_type', 'related_to'),
                        strength=edge_data.get('strength', 0.5),
                        description=edge_data.get('description', '')
                    )
                    relations.append(relation)
        
        return relations
    
    def generate_inferences(self, concept_ids: List[str], question: str) -> List[Inference]:
        """توليد استنتاجات منطقية بناءً على المفاهيم والعلاقات"""
        inferences = []
        
        # استخراج العلاقات بين المفاهيم
        relations = self.identify_relations(concept_ids)
        
        # البحث عن مسارات بين المفاهيم
        for i, source_id in enumerate(concept_ids):
            for target_id in concept_ids[i+1:]:
                paths = self.knowledge_graph.find_paths(source_id, target_id)
                
                for path in paths:
                    if path:
                        # بناء الاستنتاج
                        premises = []
                        for src, rel, tgt in path:
                            src_concept = self.knowledge_graph.concepts[src]
                            tgt_concept = self.knowledge_graph.concepts[tgt]
                            premise = f"{src_concept.name} {rel} {tgt_concept.name}"
                            premises.append(premise)
                        
                        # حساب درجة الثقة بناءً على قوة العلاقات
                        confidence = np.mean([self.knowledge_graph.graph.get_edge_data(src, tgt).get('strength', 0.5) 
                                             for src, _, tgt in path])
                        
                        # صياغة الاستنتاج
                        source_concept = self.knowledge_graph.concepts[source_id]
                        target_concept = self.knowledge_graph.concepts[target_id]
                        conclusion = f"هناك علاقة بين {source_concept.name} و {target_concept.name}"
                        
                        inference = Inference(
                            premises=premises,
                            conclusion=conclusion,
                            confidence=confidence,
                            reasoning_path=path,
                            timestamp=datetime.now().isoformat()
                        )
                        
                        inferences.append(inference)
        
        return inferences
    
    def reason(self, question: str) -> Dict[str, Any]:
        """تنفيذ عملية الاستدلال المنطقي على سؤال"""
        # استخراج المفاهيم من السؤال
        concept_ids = self.extract_concepts_from_text(question)
        
        # إذا لم يتم العثور على مفاهيم، نعيد نتيجة فارغة
        if not concept_ids:
            return {
                "concepts": [],
                "relations": [],
                "inferences": [],
                "confidence": 0.0
            }
        
        # توسيع المفاهيم لتشمل المفاهيم المرتبطة
        expanded_concepts = set(concept_ids)
        for concept_id in concept_ids:
            related = self.knowledge_graph.get_related_concepts(concept_id)
            # إضافة المفاهيم المرتبطة بقوة كافية
            for related_id, strength in related.items():
                if strength > 0.3:  # عتبة للتضمين
                    expanded_concepts.add(related_id)
        
        # توليد الاستنتاجات
        inferences = self.generate_inferences(list(expanded_concepts), question)
        
        # حساب درجة الثقة الإجمالية
        overall_confidence = 0.0
        if inferences:
            overall_confidence = np.mean([inf.confidence for inf in inferences])
        
        # تجميع النتائج
        result = {
            "concepts": [self.knowledge_graph.concepts[cid] for cid in expanded_concepts],
            "relations": self.identify_relations(list(expanded_concepts)),
            "inferences": inferences,
            "confidence": overall_confidence
        }
        
        return result
    
    def format_reasoning_result(self, result: Dict[str, Any]) -> str:
        """تنسيق نتائج الاستدلال المنطقي بشكل مفهوم"""
        if not result["concepts"]:
            return "لم أتمكن من تحديد مفاهيم كافية لإجراء استدلال منطقي."
        
        formatted_output = "نتائج التفكير الاستنتاجي:\n\n"
        
        # المفاهيم المحددة
        formatted_output += "المفاهيم المحددة:\n"
        for i, concept in enumerate(result["concepts"], 1):
            formatted_output += f"{i}. {concept.name}: {concept.description[:100]}...\n"
        
        formatted_output += "\n"
        
        # العلاقات
        if result["relations"]:
            formatted_output += "العلاقات المكتشفة:\n"
            for i, relation in enumerate(result["relations"], 1):
                source = self.knowledge_graph.concepts[relation.source].name
                target = self.knowledge_graph.concepts[relation.target].name
                formatted_output += f"{i}. {source} {relation.relation_type} {target} (الثقة: {relation.strength:.2%})\n"
        else:
            formatted_output += "لم يتم اكتشاف علاقات مباشرة بين المفاهيم.\n"
        
        formatted_output += "\n"
        
        # الاستنتاجات
        if result["inferences"]:
            formatted_output += "الاستنتاجات المنطقية:\n"
            for i, inference in enumerate(result["inferences"], 1):
                formatted_output += f"{i}. {inference.conclusion} (الثقة: {inference.confidence:.2%})\n"
                formatted_output += "   بناءً على:\n"
                for premise in inference.premises:
                    formatted_output += f"   - {premise}\n"
                formatted_output += "\n"
        else:
            formatted_output += "لم يتم التوصل إلى استنتاجات منطقية.\n"
        
        # التقييم العام
        formatted_output += f"\nالتقييم العام: درجة الثقة {result['confidence']:.2%}\n"
        
        return formatted_output


# إنشاء قاعدة معرفية أولية للاختبار
def create_initial_knowledge_base() -> KnowledgeGraph:
    """إنشاء قاعدة معرفية أولية للاختبار"""
    kg = KnowledgeGraph()
    
    # إضافة بعض المفاهيم الأساسية
    concepts = [
        Concept(id="c1", name="الذكاء الاصطناعي", description="تقنية تمكن الآلات من محاكاة الذكاء البشري", category="تقنية"),
        Concept(id="c2", name="تعلم الآلة", description="فرع من الذكاء الاصطناعي يركز على تطوير خوارزميات تتعلم من البيانات", category="تقنية"),
        Concept(id="c3", name="التعلم العميق", description="نوع متقدم من تعلم الآلة يستخدم شبكات عصبية متعددة الطبقات", category="تقنية"),
        Concept(id="c4", name="معالجة اللغة الطبيعية", description="مجال يركز على تفاعل الحواسيب مع اللغات البشرية", category="تقنية"),
        Concept(id="c5", name="الشبكات العصبية", description="نماذج حسابية مستوحاة من الدماغ البشري", category="تقنية"),
        Concept(id="c6", name="البيانات الضخمة", description="مجموعات بيانات كبيرة جدًا يصعب معالجتها بالطرق التقليدية", category="تقنية"),
        Concept(id="c7", name="الخصوصية", description="حماية المعلومات الشخصية من الوصول غير المصرح به", category="أمان"),
        Concept(id="c8", name="الأخلاقيات", description="مبادئ تحدد السلوك الصحيح والخاطئ", category="فلسفة"),
        Concept(id="c9", name="التحيز", description="ميل غير عادل تجاه أو ضد شخص أو مجموعة", category="اجتماعي"),
        Concept(id="c10", name="الأتمتة", description="استخدام التقنية لأداء المهام بتدخل بشري محدود", category="تقنية"),
    ]
    
    for concept in concepts:
        kg.add_concept(concept)
    
    # إضافة العلاقات بين المفاهيم
    relations = [
        Relation(source="c1", target="c2", relation_type="يشمل", strength=0.9, bidirectional=False),
        Relation(source="c2", target="c3", relation_type="يشمل", strength=0.8, bidirectional=False),
        Relation(source="c3", target="c5", relation_type="يستخدم", strength=0.9, bidirectional=False),
        Relation(source="c4", target="c1", relation_type="جزء من", strength=0.7, bidirectional=False),
        Relation(source="c6", target="c2", relation_type="يدعم", strength=0.8, bidirectional=False),
        Relation(source="c1", target="c7", relation_type="يؤثر على", strength=0.6, bidirectional=False),
        Relation(source="c1", target="c8", relation_type="يثير قضايا", strength=0.7, bidirectional=False),
        Relation(source="c2", target="c9", relation_type="قد يسبب", strength=0.5, bidirectional=False),
        Relation(source="c1", target="c10", relation_type="يمكّن", strength=0.8, bidirectional=False),
        Relation(source="c10", target="c7", relation_type="يهدد", strength=0.4, bidirectional=False),
    ]
    
    for relation in relations:
        kg.add_relation(relation)
    
    return kg
