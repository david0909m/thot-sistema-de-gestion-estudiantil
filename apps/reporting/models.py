from django.db import models


class ConfiguracionInstitucion(models.Model):
    """
    Configuración de la institución educativa para marca blanca y encabezados de reportes XLSX.
    """
    nombre_institucion = models.CharField(
        max_length=150, default="Sistema de Gestión Estudiantil THOT", verbose_name="Nombre de la Institución"
    )
    lema = models.CharField(max_length=200, blank=True, verbose_name="Lema o Eslogan")
    logo = models.ImageField(upload_to="institucion/logos/", blank=True, null=True, verbose_name="Logo Institucional")
    direccion = models.TextField(blank=True, verbose_name="Dirección de la Institución")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono Institucional")
    correo = models.EmailField(blank=True, verbose_name="Correo Electrónico Oficial")
    pie_de_pagina_boletin = models.TextField(
        default="Documento Oficial de Calificaciones - Impreso desde el Sistema de Gestión Estudiantil.",
        verbose_name="Pie de página para Boletines y Reportes"
    )
 
    class Meta:
        verbose_name = "Configuración Institucional (Marca Blanca)"
        verbose_name_plural = "Configuraciones Institucionales"

    def __str__(self):
        return self.nombre_institucion

    @classmethod
    def get_solo(cls):
        instancia, _ = cls.objects.get_or_create(id=1)
        return instancia
