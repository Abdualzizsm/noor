import json
import os
from typing import Dict, List, Any, Optional
from reasoning_engine import KnowledgeGraph, Concept, Relation

class KnowledgeManager:
    """مدير قاعدة المعرفة - يتيح تحميل وحفظ وتحديث قاعدة المعرفة"""
    
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None, storage_path: str = "knowledge_base.json"):
        """تهيئة مدير قاعدة المعرفة"""
        self.knowledge_graph = knowledge_graph or KnowledgeGraph()
        self.storage_path = storage_path
        
    def save_knowledge_base(self) -> bool:
        """حفظ قاعدة المعرفة إلى ملف JSON"""
        try:
            # تحويل قاعدة المعرفة إلى تمثيل JSON
            data = {
                "concepts": [],
                "relations": []
            }
            
            # حفظ المفاهيم
            for concept_id, concept in self.knowledge_graph.concepts.items():
                concept_data = {
                    "id": concept.id,
                    "name": concept.name,
                    "description": concept.description,
                    "category": concept.category,
                    "related_concepts": concept.related_concepts,
                    "attributes": concept.attributes
                }
                data["concepts"].append(concept_data)
            
            # حفظ العلاقات
            for source, target in self.knowledge_graph.graph.edges():
                edge_data = self.knowledge_graph.graph.get_edge_data(source, target)
                relation_data = {
                    "source": source,
                    "target": target,
                    "relation_type": edge_data.get("relation_type", "related_to"),
                    "strength": edge_data.get("strength", 0.5),
                    "description": edge_data.get("description", ""),
                    "bidirectional": False  # نفترض أن العلاقة أحادية الاتجاه ما لم يتم تحديد خلاف ذلك
                }
                
                # التحقق مما إذا كانت العلاقة ثنائية الاتجاه
                if (self.knowledge_graph.graph.has_edge(target, source) and 
                    self.knowledge_graph.graph.get_edge_data(target, source).get("relation_type") == edge_data.get("relation_type")):
                    relation_data["bidirectional"] = True
                
                data["relations"].append(relation_data)
            
            # حفظ البيانات إلى ملف
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"خطأ في حفظ قاعدة المعرفة: {e}")
            return False
    
    def load_knowledge_base(self) -> bool:
        """تحميل قاعدة المعرفة من ملف JSON"""
        if not os.path.exists(self.storage_path):
            print(f"ملف قاعدة المعرفة غير موجود: {self.storage_path}")
            return False
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # إنشاء قاعدة معرفة جديدة
            self.knowledge_graph = KnowledgeGraph()
            
            # إضافة المفاهيم
            for concept_data in data.get("concepts", []):
                concept = Concept(
                    id=concept_data["id"],
                    name=concept_data["name"],
                    description=concept_data["description"],
                    category=concept_data["category"],
                    related_concepts=concept_data.get("related_concepts", []),
                    attributes=concept_data.get("attributes", {})
                )
                self.knowledge_graph.add_concept(concept)
            
            # إضافة العلاقات
            for relation_data in data.get("relations", []):
                relation = Relation(
                    source=relation_data["source"],
                    target=relation_data["target"],
                    relation_type=relation_data["relation_type"],
                    strength=relation_data["strength"],
                    description=relation_data.get("description", ""),
                    bidirectional=relation_data.get("bidirectional", False)
                )
                self.knowledge_graph.add_relation(relation)
            
            return True
        
        except Exception as e:
            print(f"خطأ في تحميل قاعدة المعرفة: {e}")
            return False
    
    def add_concept(self, name: str, description: str, category: str, 
                   related_concepts: List[str] = None, attributes: Dict[str, Any] = None) -> str:
        """إضافة مفهوم جديد إلى قاعدة المعرفة"""
        # إنشاء معرف فريد للمفهوم
        concept_id = f"c{len(self.knowledge_graph.concepts) + 1}"
        
        # التحقق من عدم وجود مفهوم بنفس الاسم
        for existing_concept in self.knowledge_graph.concepts.values():
            if existing_concept.name.lower() == name.lower():
                return ""  # المفهوم موجود بالفعل
        
        # إنشاء المفهوم الجديد
        concept = Concept(
            id=concept_id,
            name=name,
            description=description,
            category=category,
            related_concepts=related_concepts or [],
            attributes=attributes or {}
        )
        
        # إضافة المفهوم إلى قاعدة المعرفة
        if self.knowledge_graph.add_concept(concept):
            # حفظ التغييرات
            self.save_knowledge_base()
            return concept_id
        
        return ""
    
    def add_relation(self, source_name: str, target_name: str, relation_type: str, 
                    strength: float = 0.5, description: str = "", bidirectional: bool = False) -> bool:
        """إضافة علاقة بين مفهومين باستخدام أسمائهما"""
        # البحث عن المفاهيم بالاسم
        source_id = ""
        target_id = ""
        
        for concept_id, concept in self.knowledge_graph.concepts.items():
            if concept.name.lower() == source_name.lower():
                source_id = concept_id
            elif concept.name.lower() == target_name.lower():
                target_id = concept_id
        
        # التحقق من وجود المفاهيم
        if not source_id or not target_id:
            return False
        
        # إنشاء العلاقة
        relation = Relation(
            source=source_id,
            target=target_id,
            relation_type=relation_type,
            strength=strength,
            description=description,
            bidirectional=bidirectional
        )
        
        # إضافة العلاقة إلى قاعدة المعرفة
        if self.knowledge_graph.add_relation(relation):
            # حفظ التغييرات
            self.save_knowledge_base()
            return True
        
        return False
    
    def get_concept_by_name(self, name: str) -> Optional[Concept]:
        """البحث عن مفهوم بالاسم"""
        for concept in self.knowledge_graph.concepts.values():
            if concept.name.lower() == name.lower():
                return concept
        return None
    
    def update_concept(self, concept_id: str, name: str = None, description: str = None, 
                      category: str = None, related_concepts: List[str] = None, 
                      attributes: Dict[str, Any] = None) -> bool:
        """تحديث مفهوم موجود"""
        if concept_id not in self.knowledge_graph.concepts:
            return False
        
        concept = self.knowledge_graph.concepts[concept_id]
        
        # تحديث البيانات المقدمة فقط
        if name is not None:
            concept.name = name
        if description is not None:
            concept.description = description
        if category is not None:
            concept.category = category
        if related_concepts is not None:
            concept.related_concepts = related_concepts
        if attributes is not None:
            concept.attributes = attributes
        
        # تحديث العقدة في الرسم البياني
        self.knowledge_graph.graph.nodes[concept_id].update({
            'name': concept.name,
            'category': concept.category,
            'description': concept.description
        })
        
        # حفظ التغييرات
        self.save_knowledge_base()
        return True
    
    def delete_concept(self, concept_id: str) -> bool:
        """حذف مفهوم من قاعدة المعرفة"""
        if concept_id not in self.knowledge_graph.concepts:
            return False
        
        # حذف المفهوم من القاموس
        del self.knowledge_graph.concepts[concept_id]
        
        # حذف العقدة والحواف المرتبطة بها من الرسم البياني
        self.knowledge_graph.graph.remove_node(concept_id)
        
        # حفظ التغييرات
        self.save_knowledge_base()
        return True
    
    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """الحصول على المفاهيم حسب الفئة"""
        return [concept for concept in self.knowledge_graph.concepts.values() 
                if concept.category.lower() == category.lower()]
    
    def search_concepts(self, query: str) -> List[Concept]:
        """البحث عن المفاهيم باستخدام استعلام نصي"""
        query = query.lower()
        results = []
        
        for concept in self.knowledge_graph.concepts.values():
            # البحث في الاسم والوصف
            if query in concept.name.lower() or query in concept.description.lower():
                results.append(concept)
        
        return results
    
    def export_knowledge_base(self, format_type: str = "json") -> str:
        """تصدير قاعدة المعرفة بتنسيق محدد"""
        if format_type.lower() == "json":
            # تحويل قاعدة المعرفة إلى تمثيل JSON
            data = {
                "concepts": [],
                "relations": []
            }
            
            # تصدير المفاهيم
            for concept_id, concept in self.knowledge_graph.concepts.items():
                concept_data = {
                    "id": concept.id,
                    "name": concept.name,
                    "description": concept.description,
                    "category": concept.category,
                    "related_concepts": concept.related_concepts,
                    "attributes": concept.attributes
                }
                data["concepts"].append(concept_data)
            
            # تصدير العلاقات
            for source, target in self.knowledge_graph.graph.edges():
                edge_data = self.knowledge_graph.graph.get_edge_data(source, target)
                relation_data = {
                    "source": source,
                    "target": target,
                    "relation_type": edge_data.get("relation_type", "related_to"),
                    "strength": edge_data.get("strength", 0.5),
                    "description": edge_data.get("description", "")
                }
                data["relations"].append(relation_data)
            
            return json.dumps(data, ensure_ascii=False, indent=2)
        
        return ""
    
    def import_knowledge_base(self, data_str: str, format_type: str = "json") -> bool:
        """استيراد قاعدة معرفة من تمثيل نصي"""
        if format_type.lower() == "json":
            try:
                data = json.loads(data_str)
                
                # إنشاء قاعدة معرفة جديدة
                new_kg = KnowledgeGraph()
                
                # استيراد المفاهيم
                for concept_data in data.get("concepts", []):
                    concept = Concept(
                        id=concept_data["id"],
                        name=concept_data["name"],
                        description=concept_data["description"],
                        category=concept_data["category"],
                        related_concepts=concept_data.get("related_concepts", []),
                        attributes=concept_data.get("attributes", {})
                    )
                    new_kg.add_concept(concept)
                
                # استيراد العلاقات
                for relation_data in data.get("relations", []):
                    relation = Relation(
                        source=relation_data["source"],
                        target=relation_data["target"],
                        relation_type=relation_data["relation_type"],
                        strength=relation_data["strength"],
                        description=relation_data.get("description", ""),
                        bidirectional=relation_data.get("bidirectional", False)
                    )
                    new_kg.add_relation(relation)
                
                # استبدال قاعدة المعرفة الحالية
                self.knowledge_graph = new_kg
                
                # حفظ التغييرات
                self.save_knowledge_base()
                
                return True
            
            except Exception as e:
                print(f"خطأ في استيراد قاعدة المعرفة: {e}")
                return False
        
        return False
