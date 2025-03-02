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
    
    // تحديث السنة الحالية في التذييل
    document.getElementById('current-year').textContent = new Date().getFullYear();
    
    // التحقق من وجود تفضيل للوضع المظلم في التخزين المحلي
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
    }
    
    // إضافة مستمع الحدث لزر تبديل الوضع
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // تحديث الأيقونة
        if (document.body.classList.contains('dark-mode')) {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            localStorage.setItem('darkMode', 'disabled');
        }
    });
    
    // إضافة مستمع الحدث لزر مسح المحادثة
    clearChatButton.addEventListener('click', function() {
        // الاحتفاظ برسالة الترحيب فقط
        const welcomeMessage = chatMessages.querySelector('.message.bot');
        chatMessages.innerHTML = '';
        chatMessages.appendChild(welcomeMessage);
        
        // التمرير إلى أعلى المحادثة
        chatMessages.scrollTop = 0;
    });
    
    // إضافة مستمع الحدث لنموذج الدردشة
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // الحصول على رسالة المستخدم
        const message = userInput.value.trim();
        
        // التحقق من أن الرسالة ليست فارغة
        if (!message) return;
        
        // إضافة رسالة المستخدم إلى الدردشة
        addMessage(message, 'user');
        
        // مسح حقل الإدخال
        userInput.value = '';
        
        // تعطيل زر الإرسال وإظهار مؤشر التحميل
        sendButton.disabled = true;
        loadingSpinner.style.display = 'block';
        buttonText.textContent = 'جارٍ...';
        
        try {
            // إرسال الرسالة إلى الخادم
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            // التحقق من وجود خطأ
            if (data.error) {
                throw new Error(data.error);
            }
            
            // إضافة رد البوت إلى الدردشة
            addMessage(data.response, 'bot');
            
        } catch (error) {
            console.error('Error:', error);
            
            // إضافة رسالة خطأ إلى الدردشة
            const errorMessage = document.createElement('div');
            errorMessage.className = 'error-message';
            errorMessage.textContent = `حدث خطأ: ${error.message}`;
            chatMessages.appendChild(errorMessage);
        } finally {
            // إعادة تمكين زر الإرسال وإخفاء مؤشر التحميل
            sendButton.disabled = false;
            loadingSpinner.style.display = 'none';
            buttonText.textContent = 'إرسال';
            
            // التمرير إلى أسفل الدردشة
            scrollToBottom();
        }
    });
    
    // وظيفة لإضافة رسالة إلى الدردشة
    function addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // إضافة أيقونة للروبوت إذا كانت الرسالة من البوت
        if (sender === 'bot') {
            const botIcon = document.createElement('div');
            botIcon.className = 'bot-icon';
            botIcon.textContent = 'ن';
            messageContent.appendChild(botIcon);
        }
        
        // تقسيم المحتوى إلى فقرات
        const paragraphs = content.split('\n');
        paragraphs.forEach(paragraph => {
            if (paragraph.trim() !== '') {
                const p = document.createElement('p');
                p.textContent = paragraph;
                messageContent.appendChild(p);
            }
        });
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // التمرير إلى أسفل الدردشة
        scrollToBottom();
    }
    
    // وظيفة للتمرير إلى أسفل الدردشة
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // التركيز على حقل الإدخال عند تحميل الصفحة
    userInput.focus();
});
