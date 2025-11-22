from django.core.management.base import BaseCommand
from django.utils import timezone
from contas.models import ContaPagar

class Command(BaseCommand):
    help = 'Atualiza o status de contas pendentes para vencidas se a data de vencimento já passou.'

    def handle(self, *args, **kwargs):
        hoje = timezone.now().date()
        contas_para_atualizar = ContaPagar.objects.exclude(status='pago')
        contas_atualizadas = 0
        for conta in contas_para_atualizar:
            conta.save()  # O método save já atualiza o status conforme a lógica do modelo
            contas_atualizadas += 1
        self.stdout.write(self.style.SUCCESS(f'{contas_atualizadas} contas tiveram o status atualizado.')) 