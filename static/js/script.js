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
    
    // تفعيل الوضع المظلم افتراضيًا إذا لم يكن هناك تفضيل محفوظ
    if (localStorage.getItem('darkMode') === null || localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        localStorage.setItem('darkMode', 'enabled');
    }
    
    // إضافة مستمع الحدث لزر تبديل الوضع
    themeToggle.addEventListener('click', function() {
        if (document.body.classList.contains('dark-mode')) {
            // تبديل إلى الوضع النهاري
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            localStorage.setItem('darkMode', 'disabled');
        } else {
            // تبديل إلى الوضع الليلي
            document.body.classList.remove('light-mode');
            document.body.classList.add('dark-mode');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            localStorage.setItem('darkMode', 'enabled');
        }
    });
    
    // إضافة مستمع الحدث لزر مسح المحادثة
    clearChatButton.addEventListener('click', function() {
        // الاحتفاظ فقط برسالة الترحيب
        const welcomeMessage = chatMessages.firstElementChild;
        chatMessages.innerHTML = '';
        chatMessages.appendChild(welcomeMessage);
        
        // إظهار رسالة تأكيد
        showNotification('تم مسح المحادثة');
    });
    
    // إضافة مستمع الحدث لنموذج الدردشة
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = userInput.value.trim();
        
        if (message) {
            // إضافة رسالة المستخدم
            addMessage(message, 'user');
            
            // مسح حقل الإدخال
            userInput.value = '';
            
            // تعطيل زر الإرسال وإظهار مؤشر التحميل
            sendButton.disabled = true;
            buttonText.style.display = 'none';
            loadingSpinner.style.display = 'block';
            
            // إضافة مؤشر الكتابة
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'message bot';
            typingIndicator.innerHTML = `
                <div class="message-content">
                    <div class="bot-icon">ن</div>
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // إرسال الرسالة إلى الخادم
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('حدث خطأ في الاتصال بالخادم');
                }
                return response.json();
            })
            .then(data => {
                // إزالة مؤشر الكتابة
                chatMessages.removeChild(typingIndicator);
                
                // إضافة رد البوت
                addMessage(data.response, 'bot');
            })
            .catch(error => {
                // إزالة مؤشر الكتابة
                if (typingIndicator.parentNode) {
                    chatMessages.removeChild(typingIndicator);
                }
                
                // إظهار رسالة الخطأ
                showError(error.message);
            })
            .finally(() => {
                // إعادة تفعيل زر الإرسال وإخفاء مؤشر التحميل
                sendButton.disabled = false;
                buttonText.style.display = 'block';
                loadingSpinner.style.display = 'none';
            });
        }
    });
    
    // دالة لإضافة رسالة إلى المحادثة
    function addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        let messageContent = '';
        if (sender === 'bot') {
            messageContent = `
                <div class="message-content">
                    <div class="bot-icon">ن</div>
                    <p>${content}</p>
                </div>
            `;
        } else {
            messageContent = `
                <div class="message-content">
                    <p>${content}</p>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageContent;
        chatMessages.appendChild(messageDiv);
        
        // التمرير إلى أسفل المحادثة
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // دالة لإظهار رسالة خطأ
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        chatMessages.appendChild(errorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // إزالة رسالة الخطأ بعد 5 ثوانٍ
        setTimeout(() => {
            if (errorDiv.parentNode) {
                chatMessages.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    // دالة لإظهار إشعار
    function showNotification(message) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'message bot';
        notificationDiv.innerHTML = `
            <div class="message-content">
                <div class="bot-icon">ن</div>
                <p>${message}</p>
            </div>
        `;
        
        chatMessages.appendChild(notificationDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // إزالة الإشعار بعد 3 ثوانٍ
        setTimeout(() => {
            if (notificationDiv.parentNode) {
                chatMessages.removeChild(notificationDiv);
            }
        }, 3000);
    }
    
    // التركيز على حقل الإدخال عند تحميل الصفحة
    userInput.focus();
});
