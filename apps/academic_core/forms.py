from django import forms
from .models import PeriodoLectivo, Nivel, Clase, Seccion, Asignatura, Escala, TipoNota
from apps.reporting.models import ConfiguracionInstitucion


class ConfiguracionInstitucionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionInstitucion
        fields = ["nombre_institucion", "lema", "logo", "direccion", "telefono", "correo", "pie_de_pagina_boletin"]
        widgets = {
            "nombre_institucion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del Centro Educativo"}),
            "lema": forms.TextInput(attrs={"class": "form-control", "placeholder": "Lema o eslogan institucional"}),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Dirección física"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: +505 2222-3333"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "contacto@colegio.edu"}),
            "pie_de_pagina_boletin": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class PeriodoLectivoForm(forms.ModelForm):
    class Meta:
        model = PeriodoLectivo
        fields = ["nombre", "fecha_inicio", "fecha_fin", "activo", "abierto", "visible"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Año Lectivo 2026"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "abierto": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class NivelForm(forms.ModelForm):
    class Meta:
        model = Nivel
        fields = ["nombre", "codigo", "orden", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Educación Secundaria"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: SEC"}),
            "orden": forms.NumberInput(attrs={"class": "form-control", "placeholder": "ej: 1"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ["periodo", "nivel", "nombre"]
        widgets = {
            "periodo": forms.Select(attrs={"class": "form-select"}),
            "nivel": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Séptimo Grado"}),
        }


class SeccionForm(forms.ModelForm):
    class Meta:
        model = Seccion
        fields = ["clase", "nombre", "codigo", "capacidad_maxima"]
        widgets = {
            "clase": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Sección A"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: SEC-7A-2026"}),
            "capacidad_maxima": forms.NumberInput(attrs={"class": "form-control", "placeholder": "ej: 35"}),
        }


class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ["nombre", "codigo", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Matemáticas"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: MAT-101"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción curricular"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class EscalaForm(forms.ModelForm):
    class Meta:
        model = Escala
        fields = ["nombre", "codigo", "nota_minima_aprobatoria", "nota_maxima"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Escala 0-100 Estándar"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: ESC-0-100"}),
            "nota_minima_aprobatoria": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "nota_maxima": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class TipoNotaForm(forms.ModelForm):
    class Meta:
        model = TipoNota
        fields = ["periodo", "padre", "nombre", "es_consolidado", "orden", "peso", "porcentaje"]
        widgets = {
            "periodo": forms.Select(attrs={"class": "form-select"}),
            "padre": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Primer Bloque / Parcial 1"}),
            "es_consolidado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "orden": forms.NumberInput(attrs={"class": "form-control"}),
            "peso": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "porcentaje": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
