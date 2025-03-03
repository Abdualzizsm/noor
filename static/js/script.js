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
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('حدث خطأ في الاتصال بالخادم');
            }
            return response.json();
        })
        .then(data => {
            // إضافة رد البوت إلى الدردشة
            addMessage('bot', data.response);
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
        
        if (sender === 'bot') {
            const botIcon = document.createElement('div');
            botIcon.className = 'bot-icon';
            // إزالة حرف النون واستبداله بأيقونة
            botIcon.innerHTML = '<i class="fas fa-robot"></i>';
            messageContent.appendChild(botIcon);
        }
        
        const messageText = document.createElement('p');
        messageText.textContent = message;
        messageContent.appendChild(messageText);
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // تمرير إلى أسفل
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // التركيز على حقل الإدخال عند تحميل الصفحة
    userInput.focus();
    
    // إضافة مستمع الحدث للضغط على زر Enter
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled && userInput.value.trim() !== '') {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });
});
