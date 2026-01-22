# gameplay/services/sql_executor.py
from django.db import connection
import re


class SafeSQLExecutor:
    """
    Ejecutor seguro de queries SQL generadas por LLM
    """
    
    ALLOWED_OPERATIONS = ['SELECT']
    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC',
        'EXECUTE', 'PRAGMA'
    ]
    
    @classmethod
    def is_safe_query(cls, sql):
        """
        Validar que la query sea segura (solo SELECT)
        """
        sql_upper = sql.upper().strip()
        
        # Debe empezar con SELECT
        if not sql_upper.startswith('SELECT'):
            return False, "Solo se permiten consultas SELECT"
        
        # No debe contener operaciones peligrosas
        for keyword in cls.FORBIDDEN_KEYWORDS:
            # Buscar el keyword como palabra completa
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_upper):
                return False, f"Operación prohibida: {keyword}"
        
        # No debe tener múltiples statements
        semicolons = sql.count(';')
        if semicolons > 1 or (semicolons == 1 and not sql.rstrip().endswith(';')):
            return False, "Solo se permite una consulta a la vez"
        
        return True, "Query segura"
    
    @classmethod
    def execute_query(cls, sql):
        """
        Ejecutar query de forma segura y retornar resultados
        """
        # Validar seguridad
        is_safe, message = cls.is_safe_query(sql)
        
        if not is_safe:
            return {
                "success": False,
                "error": message,
                "data": None
            }
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                
                # Obtener nombres de columnas
                columns = [col[0] for col in cursor.description]
                
                # Obtener filas
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                results = [
                    dict(zip(columns, row))
                    for row in rows
                ]
                
                return {
                    "success": True,
                    "error": None,
                    "data": results,
                    "row_count": len(results),
                    "columns": columns
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }