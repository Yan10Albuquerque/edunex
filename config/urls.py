
from django.contrib import admin
from django.urls import path, include
from financeiro.views import dashboard
from accounts.views import vendas

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', dashboard, name='home'),
    path('accounts/', include('accounts.urls')),
    path('alunos/', include('core.urls')),
    path('financeiro/', include('financeiro.urls')),
    path('vendas/', vendas, name='vendas'),
]
