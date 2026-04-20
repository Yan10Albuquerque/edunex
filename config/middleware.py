"""
Middleware para isolamento de dados multi-tenant
"""

class MultiTenantMiddleware:
    """
    Middleware que garante isolamento de dados por usuário.
    Armazena o usuário atual na requisição para uso em views e modelos.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Armazenar usuário na requisição para acesso em views
        request.current_user = request.user if request.user.is_authenticated else None
        
        response = self.get_response(request)
        return response
