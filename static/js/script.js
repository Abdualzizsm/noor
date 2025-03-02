document.addEventListener('DOMContentLoaded', function() {
    // تحديد العناصر
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const buttonText = document.querySelector('.button-text');
    
    // تحديث السنة الحالية في التذييل
    document.getElementById('current-year').textContent = new Date().getFullYear();
    
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
        
        // تقسيم المحتوى إلى فقرات
        const paragraphs = content.split('\n').filter(p => p.trim() !== '');
        
        paragraphs.forEach(paragraph => {
            const p = document.createElement('p');
            p.textContent = paragraph;
            messageContent.appendChild(p);
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
