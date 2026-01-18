// CHATBOT FUNCTIONALITY
const chatbotInput = document.getElementById('chatbotInput');
const chatbotSend = document.getElementById('chatbotSend');
const chatbotMessages = document.getElementById('chatbotMessages');

// Send message
// Send message
function sendMessage() {
    const message = chatbotInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    chatbotInput.value = '';

    showTypingIndicator();

    fetch('/gameplay/chat/api/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            mensaje: message,
            conversacion_id: CONVERSACION_ID
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();
        addMessage(data.respuesta || data.error || '⚠️ Respuesta inválida', 'bot');
        
        // ✅ ACTUALIZAR TÍTULO SI ES EL PRIMER MENSAJE
        if (data.es_primer_mensaje && data.nuevo_titulo) {
            actualizarTitulo(data.nuevo_titulo);
            actualizarTituloSidebar(CONVERSACION_ID, data.nuevo_titulo);
        }
    })
    .catch(error => {
        hideTypingIndicator();
        addMessage('❌ Error al comunicar con el servidor', 'bot');
        console.error(error);
    });
}

// ✅ TOGGLE SIDEBAR
function toggleSidebar() {
    const sidebar = document.getElementById('chatSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const toggleIcon = document.getElementById('toggleIcon');
    
    sidebar.classList.toggle('hidden');
    overlay.classList.toggle('active');
    
    // Cambiar ícono
    if (sidebar.classList.contains('hidden')) {
        // Ícono de menú hamburguesa (mostrar sidebar)
        toggleIcon.innerHTML = '<path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>';
    } else {
        // Ícono de X (cerrar sidebar)
        toggleIcon.innerHTML = '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>';
    }
    
    // Guardar estado en localStorage
    localStorage.setItem('sidebarHidden', sidebar.classList.contains('hidden'));
}

// ✅ RESTAURAR ESTADO DEL SIDEBAR AL CARGAR
document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatbotMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Restaurar estado del sidebar
    const sidebarHidden = localStorage.getItem('sidebarHidden') === 'true';
    if (sidebarHidden) {
        const sidebar = document.getElementById('chatSidebar');
        const toggleIcon = document.getElementById('toggleIcon');
        sidebar.classList.add('hidden');
        toggleIcon.innerHTML = '<path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>';
    }
});

// ✅ NUEVA FUNCIÓN: Actualizar título del header con animación
function actualizarTitulo(nuevoTitulo) {
    const titleElement = document.querySelector('.chatbot-title');
    
    // Agregar clase de animación
    titleElement.classList.add('typing-title');
    
    // Simular escritura
    titleElement.textContent = '';
    let i = 0;
    
    const typingInterval = setInterval(() => {
        if (i < nuevoTitulo.length) {
            titleElement.textContent += nuevoTitulo.charAt(i);
            i++;
        } else {
            clearInterval(typingInterval);
            titleElement.classList.remove('typing-title');
        }
    }, 50); // 50ms por carácter
}

// ✅ NUEVA FUNCIÓN: Actualizar título en el sidebar
function actualizarTituloSidebar(conversacionId, nuevoTitulo) {
    const conversacionItems = document.querySelectorAll('.conversacion-item');
    
    conversacionItems.forEach(item => {
        const link = item.getAttribute('href');
        if (link && link.includes(`/${conversacionId}/`)) {
            const tituloElement = item.querySelector('.conv-titulo');
            if (tituloElement) {
                // Animación de fade
                tituloElement.style.opacity = '0';
                setTimeout(() => {
                    tituloElement.textContent = nuevoTitulo;
                    tituloElement.style.opacity = '1';
                }, 200);
            }
        }
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

// ==========================================
// VOICE RECOGNITION IMPLEMENTATION
// ==========================================

const micBtn = document.getElementById('chatbotMic');

// Verificar soporte del navegador
if ('webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    
    recognition.continuous = false; // Se detiene al dejar de hablar
    recognition.lang = 'es-ES';     // Idioma Español
    recognition.interimResults = false;

    // Click en el micrófono
    micBtn.addEventListener('click', function() {
        if (micBtn.classList.contains('listening')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    // Inicio de la escucha
    recognition.onstart = function() {
        micBtn.classList.add('listening');
        chatbotInput.placeholder = "Escuchando...";
        micBtn.title = "Escuchando... clic para detener";
    };

    // Fin de la escucha (por silencio o manual)
    recognition.onend = function() {
        micBtn.classList.remove('listening');
        chatbotInput.placeholder = "Escribe tu mensaje...";
        micBtn.title = "Hablar";
        chatbotInput.focus();
    };

    // Resultado obtenido
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        
        // 1. Insertamos el texto en el input
        chatbotInput.value = transcript;
        
        // 2. Opcional: Auto-envío (actualmente desactivado para que el usuario verifique)
        // sendMessage(); 
    };

    recognition.onerror = function(event) {
        console.error("Error de reconocimiento de voz:", event.error);
        micBtn.classList.remove('listening');
        chatbotInput.placeholder = "Error al escuchar. Intenta escribir.";
    };

} else {
    // Si el navegador no soporta la API (ej. Firefox desktop sin flags), ocultamos el botón
    console.warn("Web Speech API no soportada en este navegador.");
    micBtn.style.display = 'none';
}
