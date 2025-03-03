document.addEventListener('DOMContentLoaded', function() {
    // تحديد العناصر
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const buttonText = document.querySelector('.button-text');
    const clearChatButton = document.getElementById('clear-chat');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');
    const webSearchToggle = document.getElementById('web-search-toggle');
    
    // حالة البحث على الإنترنت
    let useWebSearch = false;
    
    // تحديث السنة الحالية في التذييل
    document.getElementById('current-year').textContent = new Date().getFullYear();
    
    // تفعيل الوضع المظلم افتراضيًا
    document.body.classList.add('dark-mode');
    themeIcon.classList.remove('fa-moon');
    themeIcon.classList.add('fa-sun');
    localStorage.setItem('darkMode', 'enabled');
    
    // إضافة مستمع الحدث لزر تبديل الوضع
    themeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            document.body.classList.remove('dark-mode');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            localStorage.setItem('darkMode', 'disabled');
        } else {
            document.body.classList.add('dark-mode');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            localStorage.setItem('darkMode', 'enabled');
        }
    });
    
    // إضافة مستمع الحدث لزر تبديل البحث على الإنترنت
    webSearchToggle.addEventListener('change', function() {
        useWebSearch = this.checked;
        
        // إظهار رسالة للمستخدم عند تفعيل/تعطيل البحث على الإنترنت
        const statusMessage = useWebSearch ? 
            "تم تفعيل البحث على الإنترنت. سأستخدم معلومات محدثة من الإنترنت للإجابة على أسئلتك." : 
            "تم تعطيل البحث على الإنترنت. سأستخدم معرفتي المخزنة للإجابة على أسئلتك.";
        
        // إضافة رسالة النظام إلى الدردشة
        const systemMessageDiv = document.createElement('div');
        systemMessageDiv.className = 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const paragraph = document.createElement('p');
        paragraph.textContent = statusMessage;
        
        messageContent.appendChild(paragraph);
        systemMessageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(systemMessageDiv);
        
        // التمرير إلى أسفل
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    // إضافة مستمع الحدث لزر مسح المحادثة
    clearChatButton.addEventListener('click', function() {
        // الاحتفاظ فقط برسالة الترحيب
        const welcomeMessage = chatMessages.firstElementChild;
        chatMessages.innerHTML = '';
        chatMessages.appendChild(welcomeMessage);
        
        // إضافة تأثير الرسوم المتحركة
        welcomeMessage.style.animation = 'none';
        setTimeout(() => {
            welcomeMessage.style.animation = 'fadeIn 0.3s ease-out';
        }, 10);
    });
    
    // إضافة مستمع الحدث لنموذج الدردشة
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const userMessage = userInput.value.trim();
        
        if (userMessage === '') {
            return;
        }
        
        // إضافة رسالة المستخدم إلى الدردشة
        addMessage('user', userMessage);
        
        // مسح حقل الإدخال
        userInput.value = '';
        
        // تعطيل الزر وإظهار مؤشر التحميل
        sendButton.disabled = true;
        loadingSpinner.style.display = 'block';
        buttonText.style.opacity = '0.5';
        
        // إرسال الرسالة إلى الخادم
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: userMessage,
                use_web_search: useWebSearch
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('حدث خطأ في الاتصال بالخادم');
            }
            return response.json();
        })
        .then(data => {
            // إذا كان البحث على الإنترنت مفعلاً، أضف المعلومات الخام والإجابة النهائية
            if (useWebSearch && data.raw_info) {
                // إضافة المعلومات الخام
                addRawInfoToChat(data.raw_info);
                
                // إضافة الإجابة النهائية
                addMessage('bot', data.response);
            } else {
                // إضافة الرد العادي
                addMessage('bot', data.response);
            }
        })
        .catch(error => {
            // إضافة رسالة الخطأ إلى الدردشة
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = error.message || 'حدث خطأ في الاتصال بالخادم';
            chatMessages.appendChild(errorDiv);
        })
        .finally(() => {
            // إعادة تمكين الزر وإخفاء مؤشر التحميل
            sendButton.disabled = false;
            loadingSpinner.style.display = 'none';
            buttonText.style.opacity = '1';
            
            // التركيز على حقل الإدخال
            userInput.focus();
        });
    });
    
    // دالة إضافة رسالة إلى الدردشة
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // تحويل الروابط إلى روابط قابلة للنقر
        message = message.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
        
        // تحويل النص المنسق
        message = formatMessage(message);
        
        messageContent.innerHTML = message;
        messageDiv.appendChild(messageContent);
        
        chatMessages.appendChild(messageDiv);
        
        // التمرير إلى أسفل
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // دالة إضافة معلومات خام إلى الدردشة
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
        chatMessages.appendChild(messageDiv);
        
        // التمرير إلى أسفل
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // دالة تنسيق الرسالة (تحويل النص العادي إلى HTML منسق)
    function formatMessage(text) {
        // تقسيم النص إلى فقرات
        const paragraphs = text.split('\n\n');
        
        // معالجة كل فقرة
        const formattedParagraphs = paragraphs.map(paragraph => {
            // إذا كانت الفقرة فارغة، تخطيها
            if (!paragraph.trim()) {
                return '';
            }
            
            // التعامل مع قوائم النقاط
            if (paragraph.includes('\n- ')) {
                const listItems = paragraph.split('\n- ');
                const listHeader = listItems.shift();
                
                return `<p>${listHeader}</p><ul>${listItems.map(item => `<li>${item}</li>`).join('')}</ul>`;
            }
            
            // التعامل مع القوائم المرقمة
            if (/\n\d+\.\s/.test(paragraph)) {
                const listItems = paragraph.split(/\n\d+\.\s/);
                const listHeader = listItems.shift();
                
                return `<p>${listHeader}</p><ol>${listItems.map(item => `<li>${item}</li>`).join('')}</ol>`;
            }
            
            // تنسيق النص العادي
            return `<p>${paragraph.replace(/\n/g, '<br>')}</p>`;
        });
        
        return formattedParagraphs.join('');
    }
    
    // التركيز على حقل الإدخال عند تحميل الصفحة
    userInput.focus();
    
    // إضافة مستمع الحدث للضغط على زر Enter
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });
});
