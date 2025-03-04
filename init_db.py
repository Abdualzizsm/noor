#!/usr/bin/env python
"""
سكريبت لإنشاء قاعدة البيانات وتهيئة النظام
"""

from app import app, db, User
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    """إنشاء قاعدة البيانات وإضافة مستخدم افتراضي"""
    with app.app_context():
        # إنشاء الجداول
        db.create_all()
        
        # التحقق مما إذا كان هناك مستخدم بالفعل
        if User.query.count() == 0:
            # إنشاء مستخدم افتراضي
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=generate_password_hash("adminpassword"),
                created_at=datetime.utcnow()
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("تم إنشاء المستخدم الافتراضي:")
            print("اسم المستخدم: admin")
            print("كلمة المرور: adminpassword")
            print("يرجى تغيير هذه المعلومات في أقرب وقت ممكن!")
        else:
            print("قاعدة البيانات موجودة بالفعل وتحتوي على مستخدمين.")

if __name__ == "__main__":
    init_db()
