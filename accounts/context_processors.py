from .demo import is_visitante


def modo_visitante(request):
    user = getattr(request, 'user', None)
    return {'modo_visitante': bool(user) and is_visitante(user)}
