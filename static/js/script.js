document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearButton = document.getElementById('clear-button');
    const webSearchToggle = document.getElementById('web-search-toggle');
    const webSearchLabel = document.getElementById('web-search-label');

    let isWebSearchEnabled = false;
    let isWaitingForResponse = false;

    // تحديث السنة الحالية في التذييل
    document.getElementById('current-year').textContent = new Date().getFullYear();

    // Event Listeners
    chatForm.addEventListener('submit', handleSubmit);
    clearButton.addEventListener('click', clearInput);
    webSearchToggle.addEventListener('click', toggleWebSearch);

    // منع الإرسال التلقائي عند الضغط على Enter مع Shift
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.shiftKey) {
            e.preventDefault();
            const start = this.selectionStart;
            const end = this.selectionEnd;
            const value = this.value;
            this.value = value.substring(0, start) + '\n' + value.substring(end);
            this.selectionStart = this.selectionEnd = start + 1;
        }
    });

    // Functions
    function handleSubmit(e) {
        e.preventDefault();
        sendMessage();
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '' || isWaitingForResponse) return;

        // عرض رسالة المستخدم
        addMessageToChat('user', message);

        // مسح حقل الإدخال
        userInput.value = '';

        // تعطيل الإدخال أثناء انتظار الرد
        isWaitingForResponse = true;

        // إضافة مؤشر التحميل
        const loadingMessage = addLoadingIndicator();

        // إرسال الطلب إلى الخادم
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
            loadingMessage.remove();

            // عرض رد البوت
            addMessageToChat('bot', data.response);

            // إذا كان هناك معلومات من الإنترنت
            if (data.web_info && data.web_info.length > 0) {
                data.web_info.forEach(info => {
                    addRawInfoToChat(info.title, info.content);
                });
            }

            // تمكين الإدخال مرة أخرى
            isWaitingForResponse = false;

            // تركيز حقل الإدخال
            userInput.focus();
        })
        .catch(error => {
            console.error('Error:', error);

            // إزالة مؤشر التحميل
            loadingMessage.remove();

            // عرض رسالة خطأ
            addMessageToChat('system', 'حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى.');

            // تمكين الإدخال مرة أخرى
            isWaitingForResponse = false;

            // تركيز حقل الإدخال
            userInput.focus();
        });
    }

    function addMessageToChat(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        // تحويل الروابط إلى عناصر قابلة للنقر
        const formattedContent = formatMessage(content);
        messageContent.innerHTML = formattedContent;

        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);

        // تمرير إلى أسفل
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function formatMessage(text) {
        // تحويل الروابط إلى عناصر قابلة للنقر
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return text.replace(urlRegex, url => `<a href="${url}" target="_blank">${url}</a>`)
                   .replace(/\n/g, '<br>');
    }

    function addRawInfoToChat(title, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'raw-info');

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        const titleElement = document.createElement('div');
        titleElement.classList.add('raw-info-title');
        titleElement.textContent = title;

        const contentElement = document.createElement('div');
        contentElement.classList.add('raw-info-content');
        contentElement.innerHTML = content.replace(/\n/g, '<br>');

        messageContent.appendChild(titleElement);
        messageContent.appendChild(contentElement);

        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);

        // تمرير إلى أسفل
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function addLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot');

        const loadingContent = document.createElement('div');
        loadingContent.classList.add('message-content');

        const loadingDots = document.createElement('div');
        loadingDots.classList.add('loading-dots');

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.classList.add('dot');
            loadingDots.appendChild(dot);
        }

        loadingContent.appendChild(loadingDots);
        loadingDiv.appendChild(loadingContent);
        chatContainer.appendChild(loadingDiv);

        // تمرير إلى أسفل
        chatContainer.scrollTop = chatContainer.scrollHeight;

        return loadingDiv;
    }

    function clearInput() {
        userInput.value = '';
        userInput.focus();
    }

    function toggleWebSearch() {
        isWebSearchEnabled = !isWebSearchEnabled;

        // تحديث نص حالة البحث
        if (isWebSearchEnabled) {
            webSearchLabel.textContent = 'البحث على الإنترنت مع التفكير الذكي: مفعل';
            webSearchToggle.classList.add('active');
        } else {
            webSearchLabel.textContent = 'البحث على الإنترنت مع التفكير الذكي: معطل';
            webSearchToggle.classList.remove('active');
        }
    }
});
