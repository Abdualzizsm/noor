document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const themeToggle = document.getElementById('theme-toggle');
    const webSearchToggle = document.getElementById('web-search-toggle');
    const webSearchLabel = document.getElementById('web-search-label');
    const clearChatButton = document.getElementById('clear-chat');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const closeSidebar = document.getElementById('close-sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const mobileSidebar = document.getElementById('mobile-sidebar');
    
    let isWebSearchEnabled = false;
    let isThemeDark = true; // افتراضي: الوضع الداكن
    
    // تحديث السنة الحالية في التذييل
    const currentYearElements = document.querySelectorAll('#current-year');
    currentYearElements.forEach(element => {
        element.textContent = new Date().getFullYear();
    });
    
    // تحميل حالة الوضع من التخزين المحلي
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        isThemeDark = false;
        updateThemeIcon();
    }
    
    // تبديل الوضع (داكن/فاتح)
    themeToggle.addEventListener('click', function() {
        if (isThemeDark) {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        }
        isThemeDark = !isThemeDark;
        updateThemeIcon();
    });
    
    // تحديث أيقونة الوضع
    function updateThemeIcon() {
        const themeIcons = document.querySelectorAll('#theme-toggle i');
        themeIcons.forEach(icon => {
            if (isThemeDark) {
                icon.className = 'fas fa-moon';
            } else {
                icon.className = 'fas fa-sun';
            }
        });
    }
    
    // تبديل البحث على الإنترنت
    webSearchToggle.addEventListener('click', function() {
        isWebSearchEnabled = !isWebSearchEnabled;
        
        // تحديث زر البحث
        if (isWebSearchEnabled) {
            webSearchToggle.classList.remove('btn-outline-success');
            webSearchToggle.classList.add('btn-success');
            webSearchLabel.textContent = 'البحث: مفعل';
        } else {
            webSearchToggle.classList.remove('btn-success');
            webSearchToggle.classList.add('btn-outline-success');
            webSearchLabel.textContent = 'البحث: معطل';
        }
        
        // إضافة رسالة نظام لإعلام المستخدم بتغيير الإعداد
        const systemMessage = document.createElement('div');
        systemMessage.className = 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isWebSearchEnabled) {
            messageContent.textContent = 'تم تفعيل البحث على الإنترنت. سيقوم نور بالبحث عن معلومات محدثة.';
        } else {
            messageContent.textContent = 'تم تعطيل البحث على الإنترنت. سيعتمد نور على معرفته المخزنة فقط.';
        }
        
        systemMessage.appendChild(messageContent);
        chatContainer.appendChild(systemMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });
    
    // تفعيل الشريط الجانبي للجوال
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            mobileSidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
        });
    }
    
    if (closeSidebar) {
        closeSidebar.addEventListener('click', function() {
            mobileSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }
    
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            mobileSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
        });
    }
    
    // مسح المحادثة بالكامل
    if (clearChatButton) {
        clearChatButton.addEventListener('click', function() {
            if (confirm('هل أنت متأكد من رغبتك في مسح المحادثة بالكامل؟')) {
                // إزالة جميع الرسائل باستثناء رسالة الترحيب
                while (chatContainer.childNodes.length > 1) {
                    chatContainer.removeChild(chatContainer.lastChild);
                }
            }
        });
    }
    
    // مسح حقل الإدخال
    clearButton.addEventListener('click', function() {
        userInput.value = '';
        userInput.focus();
    });
    
    // إرسال الرسالة
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });
    
    // وظيفة إرسال الرسالة
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // إضافة رسالة المستخدم إلى المحادثة
        addMessageToChat('user', message);
        
        // مسح حقل الإدخال
        userInput.value = '';
        
        // إضافة مؤشر التحميل
        const loadingIndicator = addLoadingIndicator();
        
        // إرسال الرسالة إلى الخادم
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                web_search: isWebSearchEnabled
            }),
        })
        .then(response => response.json())
        .then(data => {
            // إزالة مؤشر التحميل
            if (loadingIndicator) {
                chatContainer.removeChild(loadingIndicator);
            }
            
            // إذا كانت هناك معلومات خام من البحث، أضفها أولاً
            if (data.raw_info && data.raw_info.trim() !== '') {
                addRawInfoToChat(data.raw_info);
            }
            
            // إضافة رد نور
            addMessageToChat('bot', data.response);
            
            // تمرير إلى أسفل المحادثة
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            
            // إزالة مؤشر التحميل
            if (loadingIndicator) {
                chatContainer.removeChild(loadingIndicator);
            }
            
            // إضافة رسالة خطأ
            const errorMessage = 'عذراً، حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى.';
            addMessageToChat('bot', errorMessage);
            
            // تمرير إلى أسفل المحادثة
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }
    
    // وظيفة إضافة رسالة إلى المحادثة
    function addMessageToChat(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // تنسيق المحتوى (تحويل الروابط وتنسيق النص)
        messageContent.innerHTML = formatMessage(content);
        
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        // تمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // وظيفة إضافة المعلومات الخام إلى المحادثة
    function addRawInfoToChat(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message raw-info';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // إنشاء رأس المعلومات الخام
        const rawInfoHeader = document.createElement('div');
        rawInfoHeader.className = 'raw-info-header';
        
        const rawInfoTitle = document.createElement('div');
        rawInfoTitle.className = 'raw-info-title';
        rawInfoTitle.textContent = 'معلومات من الإنترنت';
        
        const toggleButton = document.createElement('button');
        toggleButton.className = 'toggle-raw-info';
        toggleButton.textContent = 'عرض المزيد من المعلومات';
        
        rawInfoHeader.appendChild(rawInfoTitle);
        rawInfoHeader.appendChild(toggleButton);
        
        // إنشاء محتوى المعلومات الخام
        const rawInfoContent = document.createElement('div');
        rawInfoContent.className = 'raw-info-content';
        rawInfoContent.innerHTML = formatRawInfo(content);
        
        // إضافة العناصر إلى الرسالة
        messageContent.appendChild(rawInfoHeader);
        messageContent.appendChild(rawInfoContent);
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        // تفعيل زر التوسيع/التقليص
        toggleButton.addEventListener('click', function() {
            if (rawInfoContent.classList.contains('expanded')) {
                rawInfoContent.classList.remove('expanded');
                toggleButton.textContent = 'عرض المزيد من المعلومات';
            } else {
                rawInfoContent.classList.add('expanded');
                toggleButton.textContent = 'عرض معلومات أقل';
            }
        });
        
        // تمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // وظيفة تنسيق المعلومات الخام
    function formatRawInfo(text) {
        // تحويل الروابط إلى روابط قابلة للنقر
        text = text.replace(/https?:\/\/[^\s)]+/g, function(url) {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
        
        // تنسيق المصادر
        text = text.replace(/المصدر: (.*?)(?=\n|$)/g, '<div class="raw-info-source">المصدر: $1</div>');
        
        // تنسيق العناوين الفرعية
        text = text.replace(/^(.*?):\s*$/gm, '<strong>$1:</strong>');
        
        // تحويل سطور جديدة إلى عناصر <p>
        text = text.split('\n\n').map(paragraph => {
            if (paragraph.trim() !== '') {
                return `<p>${paragraph}</p>`;
            }
            return '';
        }).join('');
        
        return text;
    }
    
    // وظيفة تنسيق الرسالة (تحويل الروابط وتنسيق النص)
    function formatMessage(text) {
        // تحويل الروابط إلى روابط قابلة للنقر
        text = text.replace(/https?:\/\/[^\s)]+/g, function(url) {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
        
        // تحويل سطور جديدة إلى <br>
        text = text.replace(/\n/g, '<br>');
        
        // تنسيق النص الغامق
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        return text;
    }
    
    // وظيفة إضافة مؤشر التحميل
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'loading-dot';
            loadingIndicator.appendChild(dot);
        }
        
        messageContent.appendChild(loadingIndicator);
        loadingDiv.appendChild(messageContent);
        chatContainer.appendChild(loadingDiv);
        
        // تمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return loadingDiv;
    }
});
