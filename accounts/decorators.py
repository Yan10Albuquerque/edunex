from django.contrib.auth.decorators import login_required
from functools import wraps
from django.shortcuts import redirect


def plano_profissional_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.plano == 'profissional':
            return view_func(request, *args, **kwargs)
        return redirect('pagina_upgrade')
    return _wrapped_view