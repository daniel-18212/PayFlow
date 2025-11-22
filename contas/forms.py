from django import forms
from .models import ContaPagar
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.models import User

class ContaPagarForm(forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = ['descricao', 'valor', 'vencimento', 'categoria', 'status', 'observacao']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Salvar'))

class QuitarContaForm(forms.Form):
    info_pagamento = forms.CharField(
        label='Informações do Pagamento',
        widget=forms.Textarea(attrs={
            'rows': 4, 
            'cols': 40,
            'placeholder': 'Ex: Pago via PIX\nForma de pagamento: Cartão de crédito\nObservações: Pagamento antecipado'
        }),
        required=False,
        help_text='Adicione informações sobre o pagamento (forma de pagamento, observações, etc.)'
    )
    valor_atualizado = forms.DecimalField(
        label='Valor Atualizado (com juros)',
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text='Informe o valor atualizado com juros e multa, se aplicável'
    )

    def __init__(self, *args, **kwargs):
        conta_vencida = kwargs.pop('conta_vencida', False)
        valor_original = kwargs.pop('valor_original', None)
        super().__init__(*args, **kwargs)
        
        # Se a conta estiver vencida, tornar o campo obrigatório e pré-preencher com o valor original
        if conta_vencida:
            self.fields['valor_atualizado'].required = True
            if valor_original:
                self.fields['valor_atualizado'].initial = valor_original
            self.fields['valor_atualizado'].help_text = 'Informe o valor atualizado com juros e multa (obrigatório para contas vencidas)'
            self.fields['valor_atualizado'].widget.attrs.update({
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            })
        else:
            # Para contas não vencidas, o campo é opcional
            self.fields['valor_atualizado'].help_text = 'Opcional: informe um valor diferente do original, se necessário'
            self.fields['valor_atualizado'].widget.attrs.update({
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            })
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Quitar Conta', css_class='btn-success'))
    
    def clean_valor_atualizado(self):
        valor_atualizado = self.cleaned_data.get('valor_atualizado')
        if valor_atualizado is not None and valor_atualizado <= 0:
            raise forms.ValidationError("O valor atualizado deve ser maior que zero.")
        return valor_atualizado

class NovaContaForm(forms.ModelForm):
    TIPO_PAGAMENTO_CHOICES = [
        ('avista', 'À Vista'),
        ('parcelado', 'Parcelado'),
    ]
    tipo_pagamento = forms.ChoiceField(choices=TIPO_PAGAMENTO_CHOICES, widget=forms.RadioSelect)
    numero_parcelas = forms.IntegerField(min_value=2, max_value=36, required=False, label="Número de Parcelas")

    class Meta:
        model = ContaPagar
        fields = ['descricao', 'valor', 'vencimento', 'categoria', 'observacao', 'tipo_pagamento', 'numero_parcelas']
        widgets = {
            'vencimento': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Salvar'))

    def clean_valor(self):
        valor = self.cleaned_data.get('valor')
        if valor is not None and valor <= 0:
            raise forms.ValidationError("O valor da conta deve ser maior que zero.")
        return valor

    def clean_numero_parcelas(self):
        tipo_pagamento = self.cleaned_data.get('tipo_pagamento')
        numero_parcelas = self.cleaned_data.get('numero_parcelas')
        if tipo_pagamento == 'parcelado':
            if numero_parcelas is None or numero_parcelas <= 1:
                raise forms.ValidationError("Para pagamento parcelado, o número de parcelas deve ser maior que 1.")
        return numero_parcelas

class CriarUsuarioForm(forms.ModelForm):
    senha1 = forms.CharField(label='Senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    senha2 = forms.CharField(label='Confirme a senha', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_senha1(self):
        senha1 = self.cleaned_data.get('senha1')
        if len(senha1) < 6:
            raise forms.ValidationError('A senha deve ter pelo menos 6 caracteres.')
        return senha1

    def clean(self):
        cleaned_data = super().clean()
        senha1 = cleaned_data.get('senha1')
        senha2 = cleaned_data.get('senha2')
        if senha1 and senha2 and senha1 != senha2:
            raise forms.ValidationError('As senhas não coincidem.')
        return cleaned_data

class RecuperarSenhaForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail não está cadastrado no sistema.')
        return email 