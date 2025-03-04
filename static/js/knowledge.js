// ملف إدارة قاعدة المعرفة
document.addEventListener('DOMContentLoaded', function() {
    // متغيرات عامة
    let concepts = [];
    let relations = [];
    let categories = [];
    
    // تبديل الوضع الداكن/الفاتح
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            document.body.classList.toggle('light-theme');
            
            // تحديث نص الزر
            const icon = this.querySelector('i');
            if (document.body.classList.contains('dark-theme')) {
                this.innerHTML = '<i class="fas fa-sun"></i> الوضع الفاتح';
            } else {
                this.innerHTML = '<i class="fas fa-moon"></i> الوضع الداكن';
            }
            
            // حفظ التفضيل في التخزين المحلي
            localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
        });
        
        // تطبيق الوضع المحفوظ
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            document.body.classList.remove('light-theme');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i> الوضع الفاتح';
        } else {
            document.body.classList.add('light-theme');
            document.body.classList.remove('dark-theme');
            themeToggle.innerHTML = '<i class="fas fa-moon"></i> الوضع الداكن';
        }
    }
    
    // تحميل البيانات الأولية
    function loadInitialData() {
        // تحميل المفاهيم
        fetch('/api/concepts')
            .then(response => response.json())
            .then(data => {
                concepts = data;
                renderConcepts();
                populateConceptSelects();
            })
            .catch(error => {
                console.error('خطأ في تحميل المفاهيم:', error);
                showAlert('فشل في تحميل المفاهيم', 'danger');
            });
        
        // تحميل العلاقات
        fetch('/api/relations')
            .then(response => response.json())
            .then(data => {
                relations = data;
                renderRelations();
            })
            .catch(error => {
                console.error('خطأ في تحميل العلاقات:', error);
                showAlert('فشل في تحميل العلاقات', 'danger');
            });
        
        // تحميل الفئات
        fetch('/api/categories')
            .then(response => response.json())
            .then(data => {
                categories = data;
                populateCategoryLists();
            })
            .catch(error => {
                console.error('خطأ في تحميل الفئات:', error);
            });
    }
    
    // عرض المفاهيم
    function renderConcepts() {
        const conceptsList = document.getElementById('concepts-list');
        if (!conceptsList) return;
        
        // فلترة المفاهيم حسب البحث والفئة
        const searchTerm = document.getElementById('concept-search')?.value.toLowerCase() || '';
        const categoryFilter = document.getElementById('category-filter')?.value || '';
        
        const filteredConcepts = concepts.filter(concept => {
            const matchesSearch = concept.name.toLowerCase().includes(searchTerm) || 
                                 concept.description.toLowerCase().includes(searchTerm);
            const matchesCategory = categoryFilter === '' || concept.category === categoryFilter;
            return matchesSearch && matchesCategory;
        });
        
        // إنشاء بطاقات المفاهيم
        conceptsList.innerHTML = '';
        
        if (filteredConcepts.length === 0) {
            conceptsList.innerHTML = '<div class="col-12"><p class="text-center">لا توجد مفاهيم مطابقة للبحث</p></div>';
            return;
        }
        
        filteredConcepts.forEach(concept => {
            const conceptCard = document.createElement('div');
            conceptCard.className = 'col-md-4 mb-3';
            conceptCard.innerHTML = `
                <div class="card concept-card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h5 class="card-title">${concept.name}</h5>
                            <span class="badge bg-info category-badge">${concept.category}</span>
                        </div>
                        <p class="card-text">${concept.description}</p>
                        <div class="concept-actions">
                            <button class="btn btn-sm btn-outline-primary edit-concept" data-id="${concept.id}">
                                <i class="fas fa-edit"></i> تعديل
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-concept" data-id="${concept.id}">
                                <i class="fas fa-trash"></i> حذف
                            </button>
                        </div>
                    </div>
                </div>
            `;
            conceptsList.appendChild(conceptCard);
        });
        
        // إضافة مستمعي الأحداث لأزرار التعديل والحذف
        document.querySelectorAll('.edit-concept').forEach(button => {
            button.addEventListener('click', function() {
                const conceptId = this.getAttribute('data-id');
                openEditConceptModal(conceptId);
            });
        });
        
        document.querySelectorAll('.delete-concept').forEach(button => {
            button.addEventListener('click', function() {
                const conceptId = this.getAttribute('data-id');
                if (confirm('هل أنت متأكد من حذف هذا المفهوم؟')) {
                    deleteConcept(conceptId);
                }
            });
        });
    }
    
    // عرض العلاقات
    function renderRelations() {
        const relationsList = document.getElementById('relations-list');
        if (!relationsList) return;
        
        relationsList.innerHTML = '';
        
        if (relations.length === 0) {
            relationsList.innerHTML = '<p class="text-center">لا توجد علاقات</p>';
            return;
        }
        
        relations.forEach(relation => {
            const relationItem = document.createElement('div');
            relationItem.className = 'relation-item';
            relationItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${relation.source_name}</strong>
                        <span class="badge bg-secondary mx-2">${relation.relation_type}</span>
                        <strong>${relation.target_name}</strong>
                    </div>
                    <button class="btn btn-sm btn-outline-danger delete-relation" data-source="${relation.source}" data-target="${relation.target}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
                <div class="mt-2">
                    <small class="text-muted">${relation.description || 'لا يوجد وصف'}</small>
                </div>
                <div class="mt-2">
                    <label>قوة العلاقة: ${(relation.strength * 100).toFixed(0)}%</label>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: ${relation.strength * 100}%" 
                             aria-valuenow="${relation.strength * 100}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </div>
            `;
            relationsList.appendChild(relationItem);
        });
        
        // إضافة مستمعي الأحداث لأزرار الحذف
        document.querySelectorAll('.delete-relation').forEach(button => {
            button.addEventListener('click', function() {
                const source = this.getAttribute('data-source');
                const target = this.getAttribute('data-target');
                if (confirm('هل أنت متأكد من حذف هذه العلاقة؟')) {
                    deleteRelation(source, target);
                }
            });
        });
    }

    // ملء قوائم المفاهيم في نماذج إضافة/تعديل العلاقات
    function populateConceptSelects() {
        const sourceSelect = document.getElementById('relation-source');
        const targetSelect = document.getElementById('relation-target');
        
        if (!sourceSelect || !targetSelect) return;
        
        // حفظ القيم المحددة حالياً إن وجدت
        const currentSource = sourceSelect.value;
        const currentTarget = targetSelect.value;
        
        // إفراغ القوائم
        sourceSelect.innerHTML = '<option value="">اختر مفهوماً</option>';
        targetSelect.innerHTML = '<option value="">اختر مفهوماً</option>';
        
        // ملء القوائم بالمفاهيم
        concepts.forEach(concept => {
            const sourceOption = document.createElement('option');
            sourceOption.value = concept.id;
            sourceOption.textContent = concept.name;
            
            const targetOption = document.createElement('option');
            targetOption.value = concept.id;
            targetOption.textContent = concept.name;
            
            sourceSelect.appendChild(sourceOption);
            targetSelect.appendChild(targetOption);
        });
        
        // استعادة القيم المحددة إن أمكن
        if (currentSource) sourceSelect.value = currentSource;
        if (currentTarget) targetSelect.value = currentTarget;
    }
    
    // ملء قوائم الفئات
    function populateCategoryLists() {
        const categoryFilter = document.getElementById('category-filter');
        const conceptCategory = document.getElementById('concept-category');
        
        if (categoryFilter) {
            categoryFilter.innerHTML = '<option value="">جميع الفئات</option>';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categoryFilter.appendChild(option);
            });
        }
        
        if (conceptCategory) {
            conceptCategory.innerHTML = '';
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                conceptCategory.appendChild(option);
            });
        }
    }
    
    // فتح نافذة إضافة مفهوم جديد
    function openAddConceptModal() {
        const modal = document.getElementById('concept-modal');
        const modalTitle = modal.querySelector('.modal-title');
        const form = document.getElementById('concept-form');
        
        modalTitle.textContent = 'إضافة مفهوم جديد';
        form.reset();
        form.setAttribute('data-mode', 'add');
        
        // إذا كان هناك حقل للفئة، تأكد من ملئه بالفئات المتاحة
        populateCategoryLists();
        
        // إظهار النافذة
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
    
    // فتح نافذة تعديل مفهوم
    function openEditConceptModal(conceptId) {
        const concept = concepts.find(c => c.id === conceptId);
        if (!concept) return;
        
        const modal = document.getElementById('concept-modal');
        const modalTitle = modal.querySelector('.modal-title');
        const form = document.getElementById('concept-form');
        
        modalTitle.textContent = 'تعديل المفهوم';
        form.setAttribute('data-mode', 'edit');
        form.setAttribute('data-id', conceptId);
        
        // ملء حقول النموذج بمعلومات المفهوم
        document.getElementById('concept-name').value = concept.name;
        document.getElementById('concept-description').value = concept.description;
        
        const categorySelect = document.getElementById('concept-category');
        if (categorySelect) {
            // التأكد من تحميل الفئات أولاً
            populateCategoryLists();
            categorySelect.value = concept.category;
        }
        
        // إظهار النافذة
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
    
    // حفظ المفهوم (إضافة أو تعديل)
    function saveConcept(event) {
        event.preventDefault();
        
        const form = document.getElementById('concept-form');
        const mode = form.getAttribute('data-mode');
        const conceptId = form.getAttribute('data-id');
        
        const name = document.getElementById('concept-name').value.trim();
        const description = document.getElementById('concept-description').value.trim();
        const category = document.getElementById('concept-category')?.value || 'عام';
        
        if (!name) {
            showAlert('يرجى إدخال اسم المفهوم', 'warning');
            return;
        }
        
        const conceptData = {
            name: name,
            description: description,
            category: category
        };
        
        let url = '/api/concepts';
        let method = 'POST';
        
        if (mode === 'edit' && conceptId) {
            url = `/api/concepts/${conceptId}`;
            method = 'PUT';
            conceptData.id = conceptId;
        }
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(conceptData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`فشل في ${mode === 'edit' ? 'تعديل' : 'إضافة'} المفهوم`);
            }
            return response.json();
        })
        .then(data => {
            // تحديث قائمة المفاهيم
            if (mode === 'edit') {
                const index = concepts.findIndex(c => c.id === conceptId);
                if (index !== -1) {
                    concepts[index] = data;
                }
            } else {
                concepts.push(data);
            }
            
            // إعادة عرض المفاهيم وتحديث قوائم المفاهيم
            renderConcepts();
            populateConceptSelects();
            
            // إغلاق النافذة
            const modal = document.getElementById('concept-modal');
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();
            
            // عرض رسالة نجاح
            showAlert(`تم ${mode === 'edit' ? 'تعديل' : 'إضافة'} المفهوم بنجاح`, 'success');
        })
        .catch(error => {
            console.error('خطأ:', error);
            showAlert(error.message, 'danger');
        });
    }
    
    // حذف مفهوم
    function deleteConcept(conceptId) {
        fetch(`/api/concepts/${conceptId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل في حذف المفهوم');
            }
            
            // حذف المفهوم من القائمة المحلية
            concepts = concepts.filter(c => c.id !== conceptId);
            
            // إعادة عرض المفاهيم وتحديث قوائم المفاهيم
            renderConcepts();
            populateConceptSelects();
            
            // تحديث الرسم البياني
            if (typeof updateGraph === 'function') {
                updateGraph();
            }
            
            // عرض رسالة نجاح
            showAlert('تم حذف المفهوم بنجاح', 'success');
        })
        .catch(error => {
            console.error('خطأ:', error);
            showAlert(error.message, 'danger');
        });
    }
    
    // إضافة علاقة جديدة
    function addRelation(event) {
        event.preventDefault();
        
        const sourceId = document.getElementById('relation-source').value;
        const targetId = document.getElementById('relation-target').value;
        const relationType = document.getElementById('relation-type').value;
        const description = document.getElementById('relation-description').value.trim();
        const strength = parseFloat(document.getElementById('relation-strength').value) / 100;
        
        if (!sourceId || !targetId || !relationType) {
            showAlert('يرجى ملء جميع الحقول المطلوبة', 'warning');
            return;
        }
        
        if (sourceId === targetId) {
            showAlert('لا يمكن إنشاء علاقة بين مفهوم ونفسه', 'warning');
            return;
        }
        
        const relationData = {
            source: sourceId,
            target: targetId,
            relation_type: relationType,
            description: description,
            strength: strength
        };
        
        fetch('/api/relations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(relationData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل في إضافة العلاقة');
            }
            return response.json();
        })
        .then(data => {
            // إضافة العلاقة إلى القائمة المحلية
            relations.push(data);
            
            // إعادة عرض العلاقات
            renderRelations();
            
            // تحديث الرسم البياني
            if (typeof updateGraph === 'function') {
                updateGraph();
            }
            
            // إعادة تعيين النموذج
            document.getElementById('relation-form').reset();
            
            // عرض رسالة نجاح
            showAlert('تم إضافة العلاقة بنجاح', 'success');
        })
        .catch(error => {
            console.error('خطأ:', error);
            showAlert(error.message, 'danger');
        });
    }

    // حذف علاقة
    function deleteRelation(sourceId, targetId) {
        fetch(`/api/relations/${sourceId}/${targetId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('فشل في حذف العلاقة');
            }
            
            // حذف العلاقة من القائمة المحلية
            relations = relations.filter(r => !(r.source === sourceId && r.target === targetId));
            
            // إعادة عرض العلاقات
            renderRelations();
            
            // تحديث الرسم البياني
            if (typeof updateGraph === 'function') {
                updateGraph();
            }
            
            // عرض رسالة نجاح
            showAlert('تم حذف العلاقة بنجاح', 'success');
        })
        .catch(error => {
            console.error('خطأ:', error);
            showAlert(error.message, 'danger');
        });
    }
    
    // تصدير قاعدة المعرفة
    function exportKnowledgeBase() {
        fetch('/api/export')
            .then(response => {
                if (!response.ok) {
                    throw new Error('فشل في تصدير قاعدة المعرفة');
                }
                return response.json();
            })
            .then(data => {
                // تحويل البيانات إلى نص JSON
                const jsonData = JSON.stringify(data, null, 2);
                
                // إنشاء رابط تنزيل
                const blob = new Blob([jsonData], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `knowledge_base_${new Date().toISOString().slice(0, 10)}.json`;
                document.body.appendChild(a);
                a.click();
                
                // تنظيف
                setTimeout(() => {
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }, 0);
                
                showAlert('تم تصدير قاعدة المعرفة بنجاح', 'success');
            })
            .catch(error => {
                console.error('خطأ:', error);
                showAlert(error.message, 'danger');
            });
    }
    
    // استيراد قاعدة المعرفة
    function importKnowledgeBase(event) {
        const fileInput = document.getElementById('import-file');
        const file = fileInput.files[0];
        
        if (!file) {
            showAlert('يرجى اختيار ملف للاستيراد', 'warning');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                
                // إرسال البيانات إلى الخادم
                fetch('/api/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('فشل في استيراد قاعدة المعرفة');
                    }
                    return response.json();
                })
                .then(result => {
                    // تحديث البيانات المحلية
                    concepts = result.concepts || [];
                    relations = result.relations || [];
                    categories = result.categories || [];
                    
                    // إعادة عرض البيانات
                    renderConcepts();
                    renderRelations();
                    populateConceptSelects();
                    populateCategoryLists();
                    
                    // تحديث الرسم البياني
                    if (typeof updateGraph === 'function') {
                        updateGraph();
                    }
                    
                    // إعادة تعيين حقل الملف
                    fileInput.value = '';
                    
                    // إغلاق النافذة
                    const modal = document.getElementById('import-modal');
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                    
                    showAlert('تم استيراد قاعدة المعرفة بنجاح', 'success');
                })
                .catch(error => {
                    console.error('خطأ:', error);
                    showAlert(error.message, 'danger');
                });
            } catch (error) {
                console.error('خطأ في تحليل ملف JSON:', error);
                showAlert('الملف المختار ليس بتنسيق JSON صالح', 'danger');
            }
        };
        
        reader.readAsText(file);
    }
    
    // تحديث الرسم البياني
    function updateGraph() {
        const graphContainer = document.getElementById('knowledge-graph');
        if (!graphContainer) return;
        
        // إنشاء بيانات الرسم البياني
        const nodes = concepts.map(concept => ({
            id: concept.id,
            label: concept.name,
            group: concept.category
        }));
        
        const edges = relations.map(relation => ({
            from: relation.source,
            to: relation.target,
            label: relation.relation_type,
            title: relation.description || '',
            width: relation.strength * 5,
            arrows: 'to'
        }));
        
        // إنشاء الرسم البياني باستخدام vis.js
        if (typeof vis !== 'undefined') {
            const data = {
                nodes: new vis.DataSet(nodes),
                edges: new vis.DataSet(edges)
            };
            
            const options = {
                nodes: {
                    shape: 'dot',
                    size: 16,
                    font: {
                        size: 14,
                        face: 'Tajawal, Arial'
                    }
                },
                edges: {
                    font: {
                        size: 12,
                        align: 'middle',
                        face: 'Tajawal, Arial'
                    },
                    smooth: {
                        type: 'continuous'
                    }
                },
                physics: {
                    stabilization: true,
                    barnesHut: {
                        gravitationalConstant: -80000,
                        springConstant: 0.001,
                        springLength: 200
                    }
                },
                interaction: {
                    navigationButtons: true,
                    keyboard: true
                }
            };
            
            // تنظيف الحاوية
            graphContainer.innerHTML = '';
            
            // إنشاء الرسم البياني
            const network = new vis.Network(graphContainer, data, options);
            
            // إضافة مستمع للنقر على العقد
            network.on('doubleClick', function(params) {
                if (params.nodes.length > 0) {
                    const conceptId = params.nodes[0];
                    openEditConceptModal(conceptId);
                }
            });
        } else {
            graphContainer.innerHTML = '<div class="alert alert-warning">مكتبة vis.js غير متوفرة. يرجى تضمينها لعرض الرسم البياني.</div>';
        }
    }
    
    // عرض تنبيه للمستخدم
    function showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) {
            // إنشاء حاوية التنبيهات إذا لم تكن موجودة
            const container = document.createElement('div');
            container.id = 'alerts-container';
            container.className = 'alerts-container';
            document.body.appendChild(container);
        }
        
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${type} alert-dismissible fade show`;
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="إغلاق"></button>
        `;
        
        document.getElementById('alerts-container').appendChild(alertElement);
        
        // إزالة التنبيه تلقائياً بعد 5 ثوانٍ
        setTimeout(() => {
            alertElement.classList.remove('show');
            setTimeout(() => {
                alertElement.remove();
            }, 150);
        }, 5000);
    }
    
    // إضافة مستمعي الأحداث
    function setupEventListeners() {
        // زر إضافة مفهوم جديد
        const addConceptBtn = document.getElementById('add-concept-btn');
        if (addConceptBtn) {
            addConceptBtn.addEventListener('click', openAddConceptModal);
        }
        
        // نموذج إضافة/تعديل مفهوم
        const conceptForm = document.getElementById('concept-form');
        if (conceptForm) {
            conceptForm.addEventListener('submit', saveConcept);
        }
        
        // نموذج إضافة علاقة
        const relationForm = document.getElementById('relation-form');
        if (relationForm) {
            relationForm.addEventListener('submit', addRelation);
        }
        
        // زر تصدير قاعدة المعرفة
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportKnowledgeBase);
        }
        
        // زر استيراد قاعدة المعرفة
        const importBtn = document.getElementById('import-btn');
        if (importBtn) {
            importBtn.addEventListener('click', function() {
                const modal = document.getElementById('import-modal');
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
            });
        }
        
        // نموذج استيراد قاعدة المعرفة
        const importForm = document.getElementById('import-form');
        if (importForm) {
            importForm.addEventListener('submit', function(event) {
                event.preventDefault();
                importKnowledgeBase();
            });
        }
        
        // البحث في المفاهيم
        const conceptSearch = document.getElementById('concept-search');
        if (conceptSearch) {
            conceptSearch.addEventListener('input', function() {
                renderConcepts();
            });
        }
        
        // تصفية المفاهيم حسب الفئة
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', function() {
                renderConcepts();
            });
        }
        
        // تبديل عرض الرسم البياني
        const graphTab = document.querySelector('a[href="#graph-tab"]');
        if (graphTab) {
            graphTab.addEventListener('shown.bs.tab', function() {
                updateGraph();
            });
        }
    }
    
    // تهيئة الصفحة
    function init() {
        loadInitialData();
        setupEventListeners();
        
        // إذا كان الرسم البياني مرئياً عند التحميل، قم بتحديثه
        if (document.querySelector('.tab-pane.active#graph-tab')) {
            setTimeout(updateGraph, 500);
        }
    }
    
    // بدء التهيئة
    init();
});
