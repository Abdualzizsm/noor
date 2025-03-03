// بمجرد تحميل المستند، قم بتنفيذ الكود التالي
document.addEventListener('DOMContentLoaded', function() {
    // المتغيرات العامة
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const loadingSpinner = document.getElementById('loading-spinner');
    const clearChatButton = document.getElementById('clear-chat');
    const themeToggle = document.getElementById('theme-toggle');
    const currentYearSpan = document.getElementById('current-year');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    // تعيين السنة الحالية في تذييل الصفحة
    currentYearSpan.textContent = new Date().getFullYear();
    
    // تعيين التركيز على حقل الإدخال عند تحميل الصفحة
    userInput.focus();
    
    // تعديل العرض بناءً على حجم الشاشة
    adjustForScreenSize();
    
    // الاستجابة للتغييرات في حجم النافذة
    window.addEventListener('resize', function() {
        adjustForScreenSize();
    });
    
    // معالج إرسال النموذج
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // الحصول على قيمة المدخلات وتنظيفها
        const userMessage = userInput.value.trim();
        
        // التحقق من أن الرسالة ليست فارغة
        if (!userMessage) {
            showError('لا يمكن إرسال رسالة فارغة.');
            return;
        }
        
        // إضافة رسالة المستخدم إلى المحادثة
        addMessage('user', userMessage);
        
        // مسح المدخلات وإعادة التركيز
        userInput.value = '';
        userInput.focus();
        
        // تمكين وضع التحميل
        toggleLoading(true);
        
        try {
            // إرسال الرسالة إلى الخادم
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: userMessage })
            });
            
            // التحقق من نجاح الاستجابة
            if (!response.ok) {
                throw new Error(`خطأ في استجابة الخادم: ${response.status}`);
            }
            
            // تحويل الاستجابة إلى JSON
            const data = await response.json();
            
            // إضافة رد الروبوت إلى المحادثة
            addMessage('bot', data.response);
            
        } catch (error) {
            console.error('خطأ في إرسال الرسالة:', error);
            showError('حدث خطأ أثناء محاولة التواصل مع الخادم. يرجى المحاولة مرة أخرى لاحقًا.');
        } finally {
            // تعطيل وضع التحميل
            toggleLoading(false);
        }
    });
    
    // ضبط الحد الأقصى لارتفاع الإدخال وتكييفه مع المحتوى
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        const maxHeight = 120; // الحد الأقصى للارتفاع بالبكسل
        this.style.height = Math.min(this.scrollHeight, maxHeight) + 'px';
    });
    
    // دعم الإرسال بمفتاح الإدخال (مع مراعاة Shift+Enter لإضافة سطر جديد)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });
    
    // مسح المحادثة
    clearChatButton.addEventListener('click', function() {
        // إزالة جميع الرسائل باستثناء رسالة الترحيب
        const messages = chatMessages.querySelectorAll('.message');
        for (let i = 1; i < messages.length; i++) {
            messages[i].remove();
        }
        
        // إعادة التركيز إلى حقل الإدخال
        userInput.focus();
        
        // إغلاق القائمة الجانبية على الجوال بعد مسح المحادثة
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    });
    
    // تبديل السمة (المظلمة / الفاتحة) - وضع الظلام فقط حاليًا
    themeToggle.addEventListener('click', function() {
        // في المستقبل - تنفيذ تبديل السمة هنا
        this.classList.toggle('active');
    });
    
    // تبديل القائمة للأجهزة المحمولة
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
        
        // إغلاق القائمة الجانبية عند النقر خارجها على الأجهزة المحمولة
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                e.target !== mobileMenuToggle) {
                sidebar.classList.remove('active');
            }
        });
    }
    
    // تحسين الاستجابة للمس على الأجهزة المحمولة
    function enhanceTouchInteractions() {
        // إضافة الفئة 'clickable' للعناصر القابلة للنقر
        const clickableElements = document.querySelectorAll('.send-button, .mobile-menu-toggle, .theme-toggle, .message-bubble, button');
        clickableElements.forEach(el => {
            el.classList.add('clickable');
        });
        
        // تحسين تجربة النقر على الأزرار
        const allButtons = document.querySelectorAll('button, .button');
        allButtons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.classList.add('button-active');
            }, { passive: true });
            
            button.addEventListener('touchend', function() {
                this.classList.remove('button-active');
            }, { passive: true });
        });
        
        // منع التكبير عند النقر المزدوج على العناصر
        document.addEventListener('dblclick', function(e) {
            e.preventDefault();
        }, { passive: false });
        
        // تحسين التمرير
        const scrollContainers = document.querySelectorAll('.messages-container');
        scrollContainers.forEach(container => {
            container.style.webkitOverflowScrolling = 'touch';
        });
    }

    // معالجة مشكلة الترجيع السريع أثناء النقر على الأزرار
    function preventFastClicks() {
        let lastClickTime = 0;
        const clickableItems = document.querySelectorAll('.clickable, button, a');
        
        clickableItems.forEach(item => {
            item.addEventListener('click', function(e) {
                const currentTime = new Date().getTime();
                const timeDiff = currentTime - lastClickTime;
                
                if (timeDiff < 300) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
                
                lastClickTime = currentTime;
            });
        });
    }

    // دالة تعديل الواجهة بناءً على حجم الشاشة
    function adjustForScreenSize() {
        // تحديد نوع الجهاز
        const isMobile = window.innerWidth <= 768;
        const isSmallScreen = window.innerWidth <= 480;
        const isTinyScreen = window.innerWidth <= 360;
        const isLargePhone = window.innerWidth <= 480 && window.innerHeight >= 800;
        
        // ضبط ارتفاع منطقة الدردشة ليناسب الشاشة
        const chatContainer = document.querySelector('.chat-container');
        const headerHeight = document.querySelector('.chat-header').offsetHeight;
        const inputAreaHeight = document.querySelector('.input-area').offsetHeight;
        
        if (chatContainer) {
            const viewportHeight = window.innerHeight;
            chatContainer.style.height = `${viewportHeight}px`;
            chatContainer.style.maxHeight = `${viewportHeight}px`;
        }
        
        // تعديل عناصر واجهة المستخدم بناءً على حجم الشاشة
        if (isMobile) {
            // إغلاق الشريط الجانبي
            sidebar.classList.remove('active');
            
            // تعديل حجم حقل الإدخال
            userInput.placeholder = isSmallScreen ? "اكتب رسالتك..." : "اكتب رسالتك هنا...";
            
            // ضبط عرض فقاعات الرسائل
            adjustMessageBubbleWidth(isSmallScreen ? 95 : 92);
        } else {
            // تعديل حجم فقاعات الرسائل للشاشات الكبيرة
            adjustMessageBubbleWidth(88);
        }
        
        // تعديلات إضافية للشاشات الصغيرة جدًا
        if (isTinyScreen) {
            adjustMessageBubbleWidth(98);
        }
        
        // تعديلات خاصة بالهواتف ذات الشاشات الكبيرة (مثل iPhone Pro Max)
        if (isLargePhone) {
            document.body.classList.add('large-phone');
        } else {
            document.body.classList.remove('large-phone');
        }
        
        // التمرير إلى آخر رسالة
        scrollToBottom();
    }
    
    // تعديل عرض فقاعات الرسائل
    function adjustMessageBubbleWidth(widthPercentage) {
        document.querySelectorAll('.message').forEach(message => {
            message.style.maxWidth = `${widthPercentage}%`;
        });
    }
    
    // دالة إضافة رسالة إلى الدردشة
    function addMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // إنشاء الصورة الرمزية للرسالة
        const messageAvatar = document.createElement('div');
        messageAvatar.className = 'message-avatar';
        
        if (sender === 'bot') {
            messageAvatar.innerHTML = '<i class="fas fa-robot"></i>';
        } else {
            messageAvatar.innerHTML = '<i class="fas fa-user"></i>';
        }
        
        // إنشاء فقاعة الرسالة
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        
        // إنشاء نص الرسالة
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // تقسيم الرسالة إلى فقرات
        const paragraphs = message.split('\n');
        paragraphs.forEach(paragraph => {
            if (paragraph.trim()) {
                const p = document.createElement('p');
                p.textContent = paragraph;
                messageText.appendChild(p);
            }
        });
        
        // إضافة العناصر إلى هيكل الرسالة
        messageBubble.appendChild(messageText);
        messageContent.appendChild(messageAvatar);
        messageContent.appendChild(messageBubble);
        messageDiv.appendChild(messageContent);
        
        // إضافة الرسالة إلى المحادثة
        chatMessages.appendChild(messageDiv);
        
        // تعديل عرض الرسالة بناءً على حجم الشاشة
        adjustForScreenSize();
        
        // التمرير التلقائي إلى أسفل
        scrollToBottom();
    }
    
    // دالة التمرير لأسفل المحادثة
    function scrollToBottom() {
        // التأكد من أن التمرير يحدث بعد إضافة عنصر جديد
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 100);
    }
    
    // إظهار رسالة الخطأ
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message system error';
        
        const errorContent = document.createElement('div');
        errorContent.className = 'message-content';
        
        const errorBubble = document.createElement('div');
        errorBubble.className = 'message-bubble error-bubble';
        
        const errorText = document.createElement('div');
        errorText.className = 'message-text';
        errorText.innerHTML = `<p><i class="fas fa-exclamation-circle"></i> ${message}</p>`;
        
        errorBubble.appendChild(errorText);
        errorContent.appendChild(errorBubble);
        errorDiv.appendChild(errorContent);
        
        chatMessages.appendChild(errorDiv);
        
        // إزالة رسالة الخطأ بعد 5 ثوان
        setTimeout(() => {
            errorDiv.classList.add('fade-out');
            setTimeout(() => {
                errorDiv.remove();
            }, 300);
        }, 5000);
        
        // التمرير التلقائي إلى أسفل
        scrollToBottom();
    }
    
    // تبديل حالة التحميل
    function toggleLoading(isLoading) {
        if (isLoading) {
            loadingSpinner.style.display = 'block';
            sendButton.disabled = true;
            sendButton.querySelector('i').style.display = 'none';
        } else {
            loadingSpinner.style.display = 'none';
            sendButton.disabled = false;
            sendButton.querySelector('i').style.display = 'block';
        }
    }
    
    // الكشف عن نوع الجهاز
    function detectDevice() {
        const userAgent = navigator.userAgent.toLowerCase();
        const isIOS = /iphone|ipad|ipod/.test(userAgent);
        const isAndroid = /android/.test(userAgent);
        const isMobile = isIOS || isAndroid || window.innerWidth <= 768;
        
        // التحقق من نوع جهاز الآيفون
        let iphoneModel = "";
        if (isIOS && /iphone/.test(userAgent)) {
            const height = window.screen.height;
            const width = window.screen.width;
            const screenSize = Math.max(height, width);
            
            // تقريبي للموديلات
            if (screenSize >= 926) {
                iphoneModel = "iphone-large"; // iPhone Pro Max models (12/13/14/15)
                document.body.classList.add('iphone-pro-max');
            } else if (screenSize >= 844) {
                iphoneModel = "iphone-medium"; // iPhone Pro models
                document.body.classList.add('iphone-pro');
            } else {
                iphoneModel = "iphone-small"; // Regular & Mini models
                document.body.classList.add('iphone-regular');
            }
        }
        
        // إضافة فئات CSS للجسم بناءً على نوع الجهاز
        if (isIOS) document.body.classList.add('ios-device');
        if (isAndroid) document.body.classList.add('android-device');
        if (isMobile) document.body.classList.add('mobile-device');
        
        return { isIOS, isAndroid, isMobile, iphoneModel };
    }
    
    // دالة التأكد من ظهور شريط الإدخال وتحديث ارتفاعات العناصر بشكل ديناميكي
    function ensureInputAreaVisible() {
        // حساب ارتفاع منطقة الرسائل
        const windowHeight = window.innerHeight;
        const headerHeight = document.querySelector('.chat-header').offsetHeight;
        const inputAreaHeight = document.querySelector('.input-area').offsetHeight;
        
        // تحديث ارتفاع حاوية الدردشة
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.style.paddingBottom = `${inputAreaHeight}px`;
        }
        
        // تحديث هوامش منطقة الرسائل
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            messagesContainer.style.marginBottom = `${inputAreaHeight/2}px`;
        }
        
        // التمرير إلى آخر رسالة
        scrollToBottom();
    }
    
    // إضافة مستمعي الأحداث
    window.addEventListener('load', ensureInputAreaVisible);
    window.addEventListener('resize', ensureInputAreaVisible);
    
    // تنفيذ الكشف عن الجهاز عند التحميل
    detectDevice();
    
    // تنفيذ الدوال عند تحميل الصفحة
    window.addEventListener('load', function() {
        detectDevice();
        adjustForScreenSize();
        ensureInputAreaVisible();
        enhanceTouchInteractions();
        preventFastClicks();
    });
    
    // تحديث العناصر عند تغيير حجم النافذة
    window.addEventListener('resize', function() {
        adjustForScreenSize();
        ensureInputAreaVisible();
    });
    
    // تنفيذ عند تغيير اتجاه الشاشة
    window.addEventListener('orientationchange', function() {
        setTimeout(function() {
            adjustForScreenSize();
            ensureInputAreaVisible();
        }, 200);
    });
});
