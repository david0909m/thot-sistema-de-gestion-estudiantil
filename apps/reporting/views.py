from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .services import (
    generar_boletin_xlsx,
    generar_listado_estudiantes_xlsx,
    generar_resumen_docentes_xlsx,
    generar_estadisticas_bloque_xlsx
)
from apps.academic_core.models import PeriodoLectivo, Clase, Seccion
from apps.people.models import Estudiante
from apps.accounts.decorators import requiere_permiso
from apps.accounts.services_permissions import (
    puede,
    es_usuario_global,
    estudiantes_visibles,
    secciones_visibles,
)


@login_required(login_url="login")
@requiere_permiso("reporting.ver_reportes")
def reportes_index_view(request):
    """
    Centro unificado de descarga de reportes oficiales XLSX en marca blanca.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    estudiantes = estudiantes_visibles(request.user).filter(activo=True)[:50]
    clases = Clase.objects.filter(periodo=periodo) if periodo else []
    secciones = secciones_visibles(
        request.user,
        Seccion.objects.filter(clase__periodo=periodo)
    ) if periodo else []

    return render(
        request,
        "reporting/index.html",
        {
            "periodo": periodo,
            "estudiantes": estudiantes,
            "clases": clases,
            "secciones": secciones,
        }
    )


@login_required(login_url="login")
@requiere_permiso("reporting.descargar_boletin")
def descargar_boletin_view(request):
    """
    Descarga del Boletín Oficial de Calificaciones en XLSX.
    """
    estudiante_id = request.GET.get("estudiante_id")
    if not estudiante_id:
        messages.error(request, "Debe seleccionar un estudiante para generar el boletín.")
        return redirect("reportes_index")

    estudiante = get_object_or_404(Estudiante, pk=estudiante_id)
    if not puede(request.user, "reporting.descargar_boletin", objeto=estudiante):
        messages.error(request, "No tiene permisos para generar el boletín de este estudiante.")
        return redirect("reportes_index")

    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()

    buffer = generar_boletin_xlsx(estudiante, periodo)
    filename = f"Boletin_{estudiante.codigo_estudiante}_{periodo.nombre}.xlsx"

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url="login")
@requiere_permiso("reporting.descargar_listado")
def descargar_listado_view(request):
    """
    Descarga del Listado Oficial de Estudiantes por Clase/Sección en XLSX.
    """
    clase_id = request.GET.get("clase_id")
    seccion_id = request.GET.get("seccion_id")

    if not clase_id:
        messages.error(request, "Debe seleccionar una clase para generar el listado.")
        return redirect("reportes_index")

    clase = get_object_or_404(Clase, pk=clase_id)
    seccion = get_object_or_404(Seccion, pk=seccion_id) if seccion_id else None

    if not es_usuario_global(request.user):
        if seccion is None or not puede(request.user, "reporting.descargar_listado", objeto=seccion):
            messages.error(request, "Sólo puede generar listados de sus propias secciones.")
            return redirect("reportes_index")

    buffer = generar_listado_estudiantes_xlsx(clase, seccion)
    sec_tag = f"_{seccion.nombre}" if seccion else ""
    filename = f"Listado_{clase.nombre}{sec_tag}.xlsx".replace(" ", "_")

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required(login_url="login")
@requiere_permiso("reporting.descargar_estadisticas")
def descargar_reporte_estadisticas_view(request):
    """
    Descarga del Reporte Estadístico de Aprobación por Grado en XLSX.
    """
    periodo = PeriodoLectivo.objects.filter(activo=True).first() or PeriodoLectivo.objects.first()
    if not periodo:
        messages.error(request, "No existe un período lectivo activo para generar estadísticas.")
        return redirect("reportes_index")

    if not es_usuario_global(request.user):
        messages.error(request, "El reporte estadístico es de alcance institucional.")
        return redirect("reportes_index")

    buffer = generar_estadisticas_bloque_xlsx(periodo)
    filename = f"Estadisticas_Aprobacion_{periodo.nombre}.xlsx".replace(" ", "_")

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
