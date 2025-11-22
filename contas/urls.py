from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

urlpatterns = [
    path('', views.lista_contas, name='lista_contas'),
    path('historico/', views.historico_contas_quitadas, name='historico_quitadas'),
    path('exportar-pdf/', views.exportar_pdf_contas, name='exportar_pdf_contas'),
    path('exportar-pdf-historico/', views.exportar_pdf_historico, name='exportar_pdf_historico'),
    path('nova/', views.nova_conta, name='nova_conta'),
    path('editar/<int:pk>/', views.editar_conta, name='editar_conta'),
    path('deletar/<int:conta_id>/', views.deletar_conta, name='deletar_conta'),
    path('reabrir/<int:pk>/', views.reabrir_conta, name='reabrir_conta'),
    path('quitar/<int:conta_id>/', views.quitar_conta, name='quitar_conta'),
    path('editar_inline/', views.editar_inline, name='editar_inline'),
    path('criar-usuario/', views.criar_usuario, name='criar_usuario'),
    path('recuperar-senha/', views.recuperar_senha, name='recuperar_senha'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('trocar-senha-obrigatorio/', views.trocar_senha_obrigatorio, name='trocar_senha_obrigatorio'),
] 