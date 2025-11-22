from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.nome

class ContaPagar(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Em dia'),
        ('proximo_vencimento', 'Próximo do vencimento'),
        ('pago', 'Quitada'),
        ('vencida', 'Vencida'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    vencimento = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacao = models.TextField(blank=True, null=True)
    
    # Campo para informações do pagamento
    info_pagamento = models.TextField(blank=True, null=True, verbose_name='Informações do Pagamento')

    # Campos para parcelamento
    grupo_parcelamento = models.UUIDField(null=True, blank=True, editable=False)
    numero_parcela = models.PositiveIntegerField(default=1)
    total_parcelas = models.PositiveIntegerField(default=1)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.total_parcelas > 1:
            return f"{self.descricao} ({self.numero_parcela}/{self.total_parcelas})"
        return self.descricao

    def save(self, *args, **kwargs):
        hoje = timezone.now().date()
        if self.status != 'pago':
            if self.vencimento < hoje:
                self.status = 'vencida'
            elif (self.vencimento - hoje).days <= 3 and (self.vencimento - hoje).days >= 0:
                self.status = 'proximo_vencimento'
            else:
                self.status = 'pendente'
        super().save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=False)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
