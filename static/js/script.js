document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const clearChatButton = document.getElementById('clear-chat');
    const themeToggle = document.getElementById('theme-toggle');
    const webSearchToggle = document.getElementById('web-search-toggle');
    const webSearchLabel = document.getElementById('web-search-label');
    
    let isWebSearchEnabled = false;
    let isThemeDark = true; // افتراضي: الوضع الداكن
    
    // تحديث السنة الحالية في التذييل
    document.getElementById('current-year').textContent = new Date().getFullYear();
    
    // تحميل حالة الوضع من التخزين المحلي
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.remove('dark-theme');
        document.body.classList.add('light-theme');
        isThemeDark = false;
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
    });
    
    // تبديل البحث على الإنترنت
    webSearchToggle.addEventListener('click', function() {
        isWebSearchEnabled = !isWebSearchEnabled;
        
        // إضافة رسالة نظام لإعلام المستخدم بتغيير الإعداد
        const systemMessage = document.createElement('div');
        systemMessage.className = 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isWebSearchEnabled) {
            messageContent.textContent = 'تم تفعيل البحث على الإنترنت مع التفكير الذكي. سيقوم نور بالبحث عن معلومات محدثة.';
            webSearchLabel.textContent = 'البحث على الإنترنت مع التفكير الذكي: مفعل';
        } else {
            messageContent.textContent = 'تم تعطيل البحث على الإنترنت. سيعتمد نور على معرفته المضمنة فقط.';
            webSearchLabel.textContent = 'البحث على الإنترنت مع التفكير الذكي: معطل';
        }
        
        systemMessage.appendChild(messageContent);
        chatContainer.appendChild(systemMessage);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });
    
    // إرسال الرسالة عند تقديم النموذج
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });
    
    // إرسال الرسالة عند الضغط على Enter
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // مسح المحادثة
    clearButton.addEventListener('click', function() {
        userInput.value = '';
        userInput.focus();
    });
    
    // مسح المحادثة بالكامل
    clearChatButton.addEventListener('click', function() {
        // إضافة رسالة تأكيد
        if (confirm('هل أنت متأكد من رغبتك في مسح المحادثة؟')) {
            chatContainer.innerHTML = '';
            
            // إضافة رسالة ترحيب
            addMessageToChat('bot', 'مرحباً! أنا نور، كيف يمكنني مساعدتك اليوم؟');
        }
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
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                use_web_search: isWebSearchEnabled
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // إزالة مؤشر التحميل
            loadingIndicator.remove();
            
            if (data.error) {
                // إضافة رسالة الخطأ
                addMessageToChat('error', data.error);
            } else {
                // إذا كان البحث على الإنترنت مفعلاً، أضف المعلومات الخام والإجابة النهائية
                if (isWebSearchEnabled && data.raw_info) {
                    // إضافة المعلومات الخام
                    addRawInfoToChat(data.raw_info);
                    
                    // إضافة الإجابة النهائية
                    addMessageToChat('bot', data.response);
                } else {
                    // إضافة الرد العادي
                    addMessageToChat('bot', data.response);
                }
            }
            
            // التمرير إلى أسفل المحادثة
            chatContainer.scrollTop = chatContainer.scrollHeight;
        })
        .catch(error => {
            // إزالة مؤشر التحميل
            loadingIndicator.remove();
            
            // إضافة رسالة الخطأ
            addMessageToChat('error', 'حدث خطأ في الاتصال بالخادم. يرجى المحاولة مرة أخرى.');
            console.error('Error:', error);
        });
    }
    
    // وظيفة إضافة رسالة إلى المحادثة
    function addMessageToChat(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // تحويل الروابط إلى روابط قابلة للنقر وتنسيق النص
        messageContent.innerHTML = formatMessage(content);
        
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        // التمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // وظيفة إضافة المعلومات الخام إلى المحادثة
    function addRawInfoToChat(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message raw-info';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // إضافة عنوان للمعلومات الخام
        const titleElement = document.createElement('div');
        titleElement.className = 'raw-info-title';
        titleElement.textContent = 'معلومات من الإنترنت:';
        messageContent.appendChild(titleElement);
        
        // تحويل الروابط إلى روابط قابلة للنقر وتنسيق النص
        const contentElement = document.createElement('div');
        contentElement.className = 'raw-info-content';
        contentElement.innerHTML = formatMessage(content);
        messageContent.appendChild(contentElement);
        
        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        
        // التمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // وظيفة تنسيق الرسالة (تحويل الروابط وتنسيق النص)
    function formatMessage(text) {
        // تحويل الروابط إلى روابط قابلة للنقر
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // تحويل سطور النص الجديدة إلى علامات <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // وظيفة إضافة مؤشر التحميل
    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading';
        
        const loadingContent = document.createElement('div');
        loadingContent.className = 'message-content';
        
        const loadingDots = document.createElement('div');
        loadingDots.className = 'loading-dots';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'dot';
            loadingDots.appendChild(dot);
        }
        
        loadingContent.appendChild(loadingDots);
        loadingDiv.appendChild(loadingContent);
        chatContainer.appendChild(loadingDiv);
        
        // التمرير إلى أسفل المحادثة
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return loadingDiv;
    }
});
