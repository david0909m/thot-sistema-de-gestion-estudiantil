from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Perfil, AsignacionUsuario, Permiso

User = get_user_model()


class LoginForm(forms.Form):
    """
    Formulario de autenticación con estilos y widgets de Bootstrap 5.
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Ej: soporteadmin",
                "autofocus": True,
                "required": True,
            }
        ),
        label="Usuario",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "••••••••",
                "required": True,
            }
        ),
        label="Contraseña",
    )


class CambiarPasswordForm(forms.Form):
    """
    Formulario para cambio obligatorio de contraseña (PassController de Rails).
    """
    current_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña actual", "required": True}
        ),
        label="Contraseña Actual",
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Nueva contraseña", "required": True}
        ),
        label="Nueva Contraseña",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirmar nueva contraseña", "required": True}
        ),
        label="Confirmación de Contraseña",
    )

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("La confirmación de la nueva contraseña no coincide.")

        if current_password and new_password and current_password == new_password:
            raise forms.ValidationError("La nueva contraseña debe ser diferente a la contraseña actual.")

        if new_password:
            try:
                validate_password(new_password)
            except forms.ValidationError as errores:
                self.add_error("new_password", errores.messages)

        return cleaned_data


class UserAccountForm(forms.ModelForm):
    """
    Formulario de gestión completa de cuentas de usuario.
    """
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Dejar en blanco para no cambiarla"}),
        label="Establecer Nueva Contraseña"
    )

    class Meta:
        model = User
        fields = [
            "username", "first_name", "segundo_nombre", "last_name", "segundo_apellido",
            "email", "cedula_identidad", "is_staff", "is_superuser", "habilitado", "requiere_cambio_password"
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de usuario único"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer nombre"}),
            "segundo_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo nombre"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Primer apellido"}),
            "segundo_apellido": forms.TextInput(attrs={"class": "form-control", "placeholder": "Segundo apellido"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
            "cedula_identidad": forms.TextInput(attrs={"class": "form-control", "placeholder": "001-000000-0000A"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "habilitado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "requiere_cambio_password": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        new_pwd = self.cleaned_data.get("new_password")
        if new_pwd:
            validate_password(new_pwd, user=user)
            user.set_password(new_pwd)
            user.fecha_vencimiento_password = None
            user.requiere_cambio_password = False
        if commit:
            user.save()
        return user


class PerfilForm(forms.ModelForm):
    """
    Formulario para creación y edición de roles / perfiles de usuario.
    """
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label="Permisos del Perfil"
    )

    class Meta:
        model = Perfil
        fields = ["nombre", "codigo", "descripcion", "activo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: Coordinador Académico"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "ej: COORD_ACAD"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción de responsabilidades y alcance del rol"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
