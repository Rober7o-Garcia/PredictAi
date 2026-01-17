// CHATBOT FUNCTIONALITY
const chatbotInput = document.getElementById('chatbotInput');
const chatbotSend = document.getElementById('chatbotSend');
const chatbotMessages = document.getElementById('chatbotMessages');

// Send message
function sendMessage() {
    const message = chatbotInput.value.trim();
    if (!message) return;

    // Mostrar mensaje del usuario
    addMessage(message, 'user');
    chatbotInput.value = '';

    // Mostrar "escribiendo..."
    showTypingIndicator();

    fetch('/gameplay/chatbot/api/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin',  // 🔥 ESTO ES LO IMPORTANTE
        body: JSON.stringify({
            mensaje: message
        })
    })

    .then(response => response.json())
    .then(data => {
    hideTypingIndicator();
    addMessage(data.respuesta || data.error || '⚠️ Respuesta inválida', 'bot');
    })
    .catch(error => {
        hideTypingIndicator();
        addMessage('❌ Error al comunicar con el servidor', 'bot');
        console.error(error);
    });
}


chatbotSend.addEventListener('click', sendMessage);
chatbotInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Suggestion chips
document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const message = chip.getAttribute('data-message');
        chatbotInput.value = message;
        sendMessage();
    });
});

// Add message to chat
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const now = new Date();
    const time = now.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${text}
            <div class="message-time">${time}</div>
        </div>
    `;
    
    chatbotMessages.appendChild(messageDiv);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

// Typing indicator
let typingIndicator = null;

function showTypingIndicator() {
    typingIndicator = document.createElement('div');
    typingIndicator.className = 'message bot';
    typingIndicator.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    chatbotMessages.appendChild(typingIndicator);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

function hideTypingIndicator() {
    if (typingIndicator) {
        typingIndicator.remove();
        typingIndicator = null;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
