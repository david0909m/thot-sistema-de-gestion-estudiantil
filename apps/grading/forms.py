from django import forms
from .models import Evaluacion


class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ["materia", "tipo_nota", "nombre", "fecha", "porcentaje", "descripcion"]
        widgets = {
            "materia": forms.Select(attrs={"class": "form-select"}),
            "tipo_nota": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Examen Parcial 1 / Guía Práctica"}),
            "fecha": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "porcentaje": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "ej: 25.00"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Objetivos y criterios de evaluación"}),
        }
