/**
 * chat.js — Chat interface with Tailwind UI support.
 * Handles AJAX message sending, bubble rendering, typing animation.
 */

const chatBox = document.getElementById('chat-box');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const typingIndicator = document.getElementById('typing-indicator');
const sentimentBadge = document.getElementById('sentiment-badge');
const sendBtn = document.getElementById('send-btn');

// Auto-grow textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 112) + 'px';
});

// Enter to send, Shift+Enter for newline
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

/** Escape HTML to prevent XSS */
function esc(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** Scroll chat to bottom */
function scrollBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

/** Append a user bubble */
function appendUserBubble(text) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'flex gap-3 items-end justify-end bubble-in';
    div.innerHTML = `
        <div class="max-w-[78%]">
            <div class="bg-gradient-to-br from-calm-500 to-calm-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-relaxed">
                ${esc(text)}
            </div>
            <span class="text-xs text-slate-400 mt-1 block text-right mr-1">You · ${now}</span>
        </div>`;
    chatBox.appendChild(div);
    scrollBottom();
}

/** Append an AI bubble */
function appendAIBubble(text, isHtml = false) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'flex gap-3 items-start bubble-in';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-calm-500 to-lav-500 flex items-center justify-center flex-shrink-0 shadow-sm">
            <i class="bi bi-robot text-white text-xs"></i>
        </div>
        <div class="max-w-[78%]">
            <div class="bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-slate-700 leading-relaxed">
                ${isHtml ? text : esc(text)}
            </div>
            <span class="text-xs text-slate-400 mt-1 block ml-1">MindGuard AI · ${now}</span>
        </div>`;
    chatBox.appendChild(div);
    scrollBottom();
}

/** Show / hide typing indicator */
function showTyping(show) {
    typingIndicator.classList.toggle('hidden', !show);
    if (show) scrollBottom();
}

/** Update sentiment badge */
function updateSentimentBadge(sentiment, emotion) {
    if (!sentimentBadge) return;
    const classes = sentiment === 'POSITIVE'
        ? 'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-sage-100 text-sage-700'
        : 'inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-rose-100 text-rose-700';
    const icon = sentiment === 'POSITIVE' ? 'bi-emoji-smile-fill' : 'bi-emoji-frown-fill';
    sentimentBadge.className = classes;
    sentimentBadge.innerHTML = `<i class="bi ${icon}"></i> ${emotion || sentiment}`;
}

/** Show HIGH risk crisis banner */
function showCrisisBanner() {
    if (document.getElementById('crisis-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'crisis-banner';
    banner.className = 'flex items-start gap-3 bg-rose-100 border border-rose-300 rounded-2xl p-4 mt-4 bubble-in';
    banner.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill text-rose-500 text-lg flex-shrink-0 mt-0.5"></i>
        <div>
            <p class="font-semibold text-rose-700 text-sm">We're concerned about you</p>
            <p class="text-xs text-rose-600 mt-0.5">
                If you're in crisis, please reach out for immediate support.
                You deserve care and you are not alone. 💙
            </p>
        </div>`;
    chatBox.appendChild(banner);
    scrollBottom();
}

// ── Form submission ─────────────────────────────────────────────────────────
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    // Clear input
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Show user bubble immediately
    appendUserBubble(message);

    // Show typing
    showTyping(true);

    try {
        const res = await fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({ message }),
        });

        const data = await res.json();
        showTyping(false);

        if (data.error) {
            appendAIBubble('Sorry, something went wrong. Please try again.');
        } else {
            appendAIBubble(data.ai_response);
            updateSentimentBadge(data.sentiment || 'NEUTRAL', data.emotion);
            if (data.risk_level === 'RED') showCrisisBanner();
        }
    } catch {
        showTyping(false);
        appendAIBubble('Connection error. Please check your internet and try again.');
    }

    sendBtn.disabled = false;
    chatInput.focus();
});

// Scroll to bottom on load
scrollBottom();
