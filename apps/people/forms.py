from django import forms
from django.contrib.auth import get_user_model
from .models import Docente, Pariente, Estudiante, Responsable, EstudianteClase, Estudio, Experiencia, FichaMedica
from apps.academic_core.models import PeriodoLectivo, Clase, Seccion

User = get_user_model()


class DocenteForm(forms.ModelForm):
    # Campos para vincular o crear el usuario de acceso
    username = forms.CharField(
        max_length=150, required=False, label="Nombre de usuario (Login)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: prof.gonzalez"})
    )
    first_name = forms.CharField(
        max_length=150, required=False, label="Nombres",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombres del docente"})
    )
    last_name = forms.CharField(
        max_length=150, required=False, label="Apellidos",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellidos del docente"})
    )
    email = forms.EmailField(
        required=False, label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "docente@institucion.edu"})
    )
    password = forms.CharField(
        required=False, label="Contraseña inicial",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Dejar en blanco si ya existe usuario"})
    )

    class Meta:
        model = Docente
        fields = ["codigo_empleado", "especialidad", "telefono", "direccion", "foto"]
        widgets = {
            "codigo_empleado": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: DOC-2026-001"}),
            "especialidad": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Matemáticas y Física"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: +505 8888-9999"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Dirección domiciliaria"}),
            "foto": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.usuario:
            self.fields["username"].initial = self.instance.usuario.username
            self.fields["first_name"].initial = self.instance.usuario.first_name
            self.fields["last_name"].initial = self.instance.usuario.last_name
            self.fields["email"].initial = self.instance.usuario.email


class ParienteForm(forms.ModelForm):
    class Meta:
        model = Pariente
        fields = [
            "primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido",
            "cedula_identidad", "parentesco", "telefono", "email",
            "profesion", "lugar_trabajo", "direccion"
        ]
        widgets = {
            "primer_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer nombre"}),
            "segundo_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo nombre"}),
            "primer_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer apellido"}),
            "segundo_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo apellido"}),
            "cedula_identidad": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: 001-010190-0000A"}),
            "parentesco": forms.Select(attrs={"class": "form-select"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: +505 8765-4321"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "tutor@correo.com"}),
            "profesion": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Ingeniero / Comerciante"}),
            "lugar_trabajo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Empresa o institución"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Dirección domiciliar"}),
        }


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = [
            "codigo_estudiante", "primer_nombre", "segundo_nombre",
            "primer_apellido", "segundo_apellido", "cedula_identidad",
            "fecha_nacimiento", "genero", "estado_civil", "religion",
            "escolaridad", "recorrido", "foto", "activo"
        ]
        widgets = {
            "codigo_estudiante": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: 2026-EST-001"}),
            "primer_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer nombre"}),
            "segundo_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo nombre"}),
            "primer_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer apellido"}),
            "segundo_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo apellido"}),
            "cedula_identidad": forms.TextInput(attrs={"class": "form-control", "placeholder": "Cédula o partida de nacimiento"}),
            "fecha_nacimiento": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "genero": forms.Select(attrs={"class": "form-select"}),
            "estado_civil": forms.Select(attrs={"class": "form-select"}),
            "religion": forms.Select(attrs={"class": "form-select"}),
            "escolaridad": forms.Select(attrs={"class": "form-select"}),
            "recorrido": forms.Select(attrs={"class": "form-select"}),
            "foto": forms.FileInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ResponsableForm(forms.ModelForm):
    class Meta:
        model = Responsable
        fields = ["pariente", "es_representante_legal", "es_responsable_financiero", "convive_con_estudiante"]
        widgets = {
            "pariente": forms.Select(attrs={"class": "form-select"}),
            "es_representante_legal": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "es_responsable_financiero": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "convive_con_estudiante": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MatriculaEstudianteForm(forms.ModelForm):
    class Meta:
        model = EstudianteClase
        fields = ["periodo", "clase", "seccion", "estado"]
        widgets = {
            "periodo": forms.Select(attrs={"class": "form-select"}),
            "clase": forms.Select(attrs={"class": "form-select"}),
            "seccion": forms.Select(attrs={"class": "form-select"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }


class EstudioDocenteForm(forms.ModelForm):
    class Meta:
        model = Estudio
        fields = ["titulo", "institucion", "fecha_obtencion"]
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Licenciatura en Pedagogía"}),
            "institucion": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Universidad Nacional"}),
            "fecha_obtencion": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class ExperienciaDocenteForm(forms.ModelForm):
    class Meta:
        model = Experiencia
        fields = ["cargo", "institucion", "fecha_inicio", "fecha_fin"]
        widgets = {
            "cargo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Docente de Secundaria"}),
            "institucion": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Colegio San José"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class FichaMedicaForm(forms.ModelForm):
    class Meta:
        model = FichaMedica
        fields = [
            "tipo_sangre", "alergias", "padecimientos_cronicos", "medicamentos_permanentes",
            "seguro_medico", "numero_poliza", "contacto_emergencia_nombre",
            "contacto_emergencia_telefono", "autoriza_traslado_hospital", "observaciones"
        ]
        widgets = {
            "tipo_sangre": forms.Select(attrs={"class": "form-select"}),
            "alergias": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Alergias a medicamentos, alimentos, picaduras..."}),
            "padecimientos_cronicos": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Asma, diabetes, epilepsia, afecciones cardíacas..."}),
            "medicamentos_permanentes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Nombre, dosis y horario de administración..."}),
            "seguro_medico": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Seguros América / Cruz Roja"}),
            "numero_poliza": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: POL-998877"}),
            "contacto_emergencia_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre completo del contacto"}),
            "contacto_emergencia_telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono 24/7"}),
            "autoriza_traslado_hospital": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Restricciones para educación física, deportes o dieta escolar..."}),
        }

