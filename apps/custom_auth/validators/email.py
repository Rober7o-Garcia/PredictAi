from django.core.exceptions import ValidationError
import re
from cachetools import TTLCache
import dns.resolver
import dns.exception

# Cache para almacenar los resultados de la validación DNS (TTL = 3600 segundos = 1 hora)
cache = TTLCache(maxsize=1000, ttl=3600)

def check_dns(email_domain): 
    if email_domain in cache:
        result = cache[email_domain]
        if result is not True:  # Si hay un error guardado en caché
            raise ValidationError(result)  # Lanzar el error guardado
        return True
    
    try: 
        dns.resolver.resolve(email_domain, 'MX')
        cache[email_domain] = True
        return True
    except dns.resolver.NoAnswer:
        error = "El dominio no puede manejar correos sin registros MX"
        cache[email_domain] = error
        raise ValidationError(error)
    except dns.resolver.NXDOMAIN:
        error = "El dominio no existe"
        cache[email_domain] = error
        raise ValidationError(error)
    except dns.resolver.Timeout:
        error = "Timeout al consultar el dominio"
        cache[email_domain] = error
        raise ValidationError(error)
    except dns.exception.DNSException:
        error = "Error al consultar el dominio"
        cache[email_domain] = error
        raise ValidationError(error)
        
    
def validar_email(email): 
    email = email.strip().lower()
    # Primera validación básica de formato
    expresion_regular = r"^(?![0-9])(?=.{6,254}$)([a-zA-Z][a-zA-Z0-9._%+-]{0,63})@([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$"
    if not re.fullmatch(expresion_regular, email):
        raise ValidationError("El formato del correo no es válido. La longitud del mismo debe estar entre los 6 y 254 caracteres")
    
    # Obtener el dominio del correo
    email_domain = email.split("@")[-1] 
    
    # Asegurarse de que el correo tiene un dominio válido
    if '.' not in email_domain:
        raise ValidationError("El dominio del correo no es válido")
    
    # Lista de dominios prohibidos
    banned_domains = [
        "example.com", "example.org", "example.net",  
        "tempmail.com", "tempmail.net", "tempmail.org",
        "10minutemail.com", "10minutemail.net",
        "mailinator.com", "mailinator.net", "mailinator.org",
        "guerrillamail.com", "guerrillamail.net",
        "dispostable.com", "getnada.com", "nada.email",
        "trashmail.com", "trashmail.de", "moakt.com",
        "yopmail.com", "yopmail.fr",
        "fakeinbox.com", "fakemail.net",
        "throwawaymail.com", "temp-mail.org", "temp-mail.io",
        "maildrop.cc", "mytemp.email", "emailondeck.com",
        "sharklasers.com", "spamgourmet.com", "mintemail.com",
        "mailcatch.com", "emailtemporario.com.br"
    ]
    
    if email_domain in banned_domains:
        raise ValidationError("El dominio del correo está prohibido")
    
    # Lista de subdominios prohibidos
    banned_subdomains = [
        "mailinator", "tempmail", "10minutemail", "guerrillamail", 
        "trashmail", "yopmail", "fakeinbox", "dispostable", 
        "throwawaymail", "moakt", "maildrop", "getnada", "spamgourmet"
    ]
    
    # Verifica subdominios prohibidos
    for banned_sub in banned_subdomains:
        if banned_sub in email_domain:
            raise ValidationError("El subdominio del correo está prohibido")
    
    # Finalmente, realizar la verificación DNS
    check_dns(email_domain)
    
    return True  