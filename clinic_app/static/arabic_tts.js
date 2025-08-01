/**
 * مكتبة لتحويل الأرقام إلى كلمات عربية وإصدار صوت قراءة
 */
const ArabicTTS = {
    // مصفوفات الأرقام بالعربي
    ones: ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة'],
    tens: ['', 'عشرة', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون'],
    teens: ['عشرة', 'أحد عشر', 'اثنا عشر', 'ثلاثة عشر', 'أربعة عشر', 'خمسة عشر', 'ستة عشر', 'سبعة عشر', 'ثمانية عشر', 'تسعة عشر'],
    hundreds: ['', 'مائة', 'مئتان', 'ثلاثمائة', 'أربعمائة', 'خمسمائة', 'ستمائة', 'سبعمائة', 'ثمانمائة', 'تسعمائة'],

    // تحويل رقم إلى كلمات عربية
    convertToArabicWords: function(number) {
        if (number === 0) return 'صفر';
        if (number < 0) return 'ناقص ' + this.convertToArabicWords(Math.abs(number));

        let words = '';

        // للأرقام أكبر من 999
        if (number >= 1000) {
            words += this.convertToArabicWords(Math.floor(number / 1000)) + ' ألف ';
            number %= 1000;
        }

        // للأرقام من 100-999
        if (number >= 100) {
            words += this.hundreds[Math.floor(number / 100)] + ' ';
            number %= 100;
        }

        // للأرقام من 1-99
        if (number > 0) {
            if (words !== '') {
                words += 'و';
            }

            if (number < 10) {
                words += this.ones[number];
            } else if (number < 20) {
                words += this.teens[number - 10];
            } else {
                const ten = Math.floor(number / 10);
                const one = number % 10;

                if (one > 0) {
                    words += this.ones[one] + ' و' + this.tens[ten];
                } else {
                    words += this.tens[ten];
                }
            }
        }

        return words.trim();
    },

    // دمج الصوت مع رقم التذكرة
    speakTicketNumber: function(ticketNumber) {
        if (!ticketNumber) return;

        // إنشاء النص الذي سيتم قراءته
        const ticketText = this.convertToArabicWords(ticketNumber);
        const fullText = `التذكرة رقم ${ticketText}، يرجى الدخول للفحص`;

        // استخدام خاصية قراءة النص في المتصفح
        this.speak(fullText);

        return fullText;
    },

    // استخدام Web Speech API للقراءة
    speak: function(text) {
        // التأكد من دعم المتصفح لـ Web Speech API
        if ('speechSynthesis' in window) {
            // تشغيل صوت التنبيه أولاً
            this.playNotificationSound();

            // ثم قراءة النص
            setTimeout(() => {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ar';
                utterance.rate = 0.9;  // سرعة قراءة أبطأ قليلاً

                // تحديد صوت عربي إذا كان متوفراً
                const voices = speechSynthesis.getVoices();
                const arabicVoice = voices.find(voice => voice.lang.includes('ar'));
                if (arabicVoice) {
                    utterance.voice = arabicVoice;
                }

                speechSynthesis.speak(utterance);
            }, 1000); // تأخير بعد صوت التنبيه
        } else {
            console.log("المتصفح لا يدعم خاصية قراءة النص");
        }
    },

    // تشغيل صوت التنبيه
    playNotificationSound: function() {
        const notificationSound = new Audio('/static/sounds/notification.mp3');
        notificationSound.play().catch(e => console.log("خطأ في تشغيل الصوت:", e));
    }
};
