# gameplay/services/text_formatter.py
import markdown
import re


def formatear_respuesta_chatbot(texto):
    """
    Convierte markdown a HTML y aplica formato personalizado para el chatbot
    """
    if not texto:
        print("⚠️ TEXTO VACÍO O NONE")
        return texto
    
    print("📝 TEXTO ORIGINAL:", texto[:200])
    print("📏 LONGITUD:", len(texto))
    
    try:
        
        # 1. Proteger bloques LaTeX ANTES de convertir markdown
        # Detectar fórmulas en [ ... ] o \[ ... \]
        texto = re.sub(
            r'\\\[(.*?)\\\]',
            r'<span class="math-block">\[\1\]</span>',
            texto,
            flags=re.DOTALL
        )
        
        # Detectar fórmulas inline en $...$ o \(...\)
        texto = re.sub(
            r'\$\$([^\$]+)\$\$',
            r'<span class="math-block">\[\1\]</span>',
            texto
        )
        
        texto = re.sub(
            r'\$([^\$]+)\$',
            r'<span class="math-inline">\(\1\)</span>',
            texto
        )
        
        # 1. Convertir markdown básico a HTML
        html = markdown.markdown(
            texto,
            extensions=[
                'nl2br',  # Convierte saltos de línea a <br>
                'tables',  # Soporte para tablas
                'fenced_code'  # Soporte para bloques de código
            ]
        )
        
        print("🔄 HTML CONVERTIDO:", html[:200])
        print("📏 LONGITUD HTML:", len(html))
        
        # 2. Aplicar estilos personalizados
        
        # Hacer las listas más bonitas
        html = html.replace('<ul>', '<ul class="chatbot-list">')
        html = html.replace('<ol>', '<ol class="chatbot-list chatbot-list-numbered">')
        
        # Hacer las tablas responsivas
        html = re.sub(
            r'<table>',
            '<div class="table-wrapper"><table class="chatbot-table">',
            html
        )
        html = re.sub(r'</table>', '</table></div>', html)
        
        # Truncar celdas muy largas (opcional)
        html = re.sub(
            r'<td>([^<]{100,})</td>',
            lambda m: f'<td title="{m.group(1)}">{m.group(1)[:80]}...</td>',
            html
        )
        
        # Resaltar código inline
        html = re.sub(
            r'<code>([^<]+)</code>',
            r'<code class="inline-code">\1</code>',
            html
        )
        
        # Bloques de código
        html = re.sub(
            r'<pre><code>',
            '<pre class="code-block"><code>',
            html
        )
        
        # 3. Emojis de énfasis (opcional, para hacerlo más visual)
        # Detectar encabezados importantes y agregar emojis
        html = re.sub(
            r'<h3>Recomendaciones',
            '<h3>💡 Recomendaciones',
            html,
            flags=re.IGNORECASE
        )
        html = re.sub(
            r'<h3>Análisis',
            '<h3>📊 Análisis',
            html,
            flags=re.IGNORECASE
        )
        html = re.sub(
            r'<h3>Estrategia',
            '<h3>🎯 Estrategia',
            html,
            flags=re.IGNORECASE
        )
        
        print("✅ HTML FINAL:", html[:200])
        print("📏 LONGITUD FINAL:", len(html))
        print("=" * 80)
        
        return html
        
    except Exception as e:
        print("=" * 80)
        print("❌ ERROR AL FORMATEAR RESPUESTA:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print(f"   Texto original (primeros 500 chars): {texto[:500]}")
        print("=" * 80)
        # Retornar texto original si falla
        return texto