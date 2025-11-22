from django.contrib import admin
from .models import ContaPagar, Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'vencimento', 'categoria', 'status', 'usuario')
    search_fields = ('descricao', 'categoria__nome', 'usuario__username')
    list_filter = ('status', 'categoria', 'vencimento', 'usuario')
