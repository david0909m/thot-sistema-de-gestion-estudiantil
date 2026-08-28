from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from apps.accounts.views import (
    login_view,
    logout_view,
    cambiar_password_view,
    dashboard_view,
    descargar_reporte_docentes_view,
    usuarios_list_view,
    usuario_create_view,
    usuario_edit_view,
    usuario_unlock_axes_view,
    roles_list_view,
    rol_create_view,
    rol_edit_view
)
from apps.academic_core.views import (
    configuracion_institucion_view,
    periodos_list_view,
    periodo_create_view,
    periodo_edit_view,
    clases_list_view,
    clase_create_view,
    clase_edit_view,
    seccion_create_view,
    seccion_edit_view,
    materia_detail_view,
    horarios_list_view,
    asignaturas_list_view,
    asignatura_create_view,
    asignatura_edit_view,
    niveles_list_view,
    nivel_create_view,
    nivel_edit_view,
    tipos_nota_list_view,
    tipo_nota_create_view,
    tipo_nota_edit_view,
    escalas_list_view,
    escala_create_view,
    escala_edit_view,
    catalogos_panel_view
)
from apps.people.views import (
    estudiantes_list_view,
    estudiante_detail_view,
    estudiante_create_view,
    estudiante_edit_view,
    matricular_estudiante_view,
    asignar_responsable_view,
    docentes_list_view,
    docente_detail_view,
    docente_create_view,
    docente_edit_view,
    docente_estudio_add_view,
    docente_experiencia_add_view,
    parientes_list_view,
    pariente_create_view,
    pariente_edit_view,
    ficha_medica_view
)
from apps.grading.views import (
    evaluaciones_list_view,
    evaluacion_create_view,
    evaluacion_edit_view,
    evaluacion_ingreso_notas_view,
    consolidacion_view,
    sabana_notas_view,
    boletin_web_view
)
from apps.support.views import (
    incidencias_list_view,
    incidencia_detail_view,
    mensajes_inbox_view,
    mensaje_detail_view
)
from apps.reporting.views import (
    reportes_index_view,
    descargar_boletin_view,
    descargar_listado_view,
    descargar_reporte_estadisticas_view
)
from apps.audit.views import auditoria_list_view

# Personalización institucional del encabezado de Django Admin
admin.site.site_header = "THOT — Sistema de Gestión Estudiantil"
admin.site.site_title = "THOT Admin"
admin.site.index_title = "Consola de Administración y Gestión Técnica"

urlpatterns = [
    path('', dashboard_view, name='root'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('accounts/cambiar-password/', cambiar_password_view, name='cambiar_password'),

    # Recuperación de contraseña por correo (tokens firmados de Django)
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'
    ),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name='password_reset_done'
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),
    path(
        'password-reset/completo/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name='password_reset_complete'
    ),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('configuracion/', configuracion_institucion_view, name='configuracion_institucion'),
    
    # Gestión de Usuarios, Cuentas y Roles
    path('usuarios/', usuarios_list_view, name='usuarios_list'),
    path('usuarios/nuevo/', usuario_create_view, name='usuario_create'),
    path('usuarios/<int:user_id>/editar/', usuario_edit_view, name='usuario_edit'),
    path('usuarios/unlock/<str:username>/', usuario_unlock_axes_view, name='usuario_unlock_axes'),
    path('usuarios/roles/', roles_list_view, name='roles_list'),
    path('usuarios/roles/nuevo/', rol_create_view, name='rol_create'),
    path('usuarios/roles/<int:rol_id>/editar/', rol_edit_view, name='rol_edit'),

    # Módulos Académicos
    path('periodos/', periodos_list_view, name='periodos_list'),
    path('periodos/nuevo/', periodo_create_view, name='periodo_create'),
    path('periodos/<int:periodo_id>/editar/', periodo_edit_view, name='periodo_edit'),
    path('clases/', clases_list_view, name='clases_list'),
    path('clases/nueva/', clase_create_view, name='clase_create'),
    path('clases/<int:clase_id>/editar/', clase_edit_view, name='clase_edit'),
    path('secciones/nueva/', seccion_create_view, name='seccion_create'),
    path('secciones/<int:seccion_id>/editar/', seccion_edit_view, name='seccion_edit'),
    path('materias/<int:materia_id>/', materia_detail_view, name='materia_detail'),
    path('academic/horarios/', horarios_list_view, name='horarios_list'),

    # Catálogos y Escalas
    path('catalogos/asignaturas/', asignaturas_list_view, name='asignaturas_list'),
    path('catalogos/asignaturas/nueva/', asignatura_create_view, name='asignatura_create'),
    path('catalogos/asignaturas/<int:asignatura_id>/editar/', asignatura_edit_view, name='asignatura_edit'),
    path('catalogos/niveles/', niveles_list_view, name='niveles_list'),
    path('catalogos/niveles/nuevo/', nivel_create_view, name='nivel_create'),
    path('catalogos/niveles/<int:nivel_id>/editar/', nivel_edit_view, name='nivel_edit'),
    path('grading/tipos-notas/', tipos_nota_list_view, name='tipos_nota_list'),
    path('grading/tipos-notas/nuevo/', tipo_nota_create_view, name='tipo_nota_create'),
    path('grading/tipos-notas/<int:tipo_id>/editar/', tipo_nota_edit_view, name='tipo_nota_edit'),
    path('grading/escalas/', escalas_list_view, name='escalas_list'),
    path('grading/escalas/nueva/', escala_create_view, name='escala_create'),
    path('grading/escalas/<int:escala_id>/editar/', escala_edit_view, name='escala_edit'),
    path('catalogos/', catalogos_panel_view, name='catalogos_panel'),

    # Módulo de Personas (Estudiantes, Docentes, Parientes, Matrículas y Salud)
    path('estudiantes/', estudiantes_list_view, name='estudiantes_list'),
    path('estudiantes/nuevo/', estudiante_create_view, name='estudiante_create'),
    path('estudiantes/<int:estudiante_id>/', estudiante_detail_view, name='estudiante_detail'),
    path('estudiantes/<int:estudiante_id>/editar/', estudiante_edit_view, name='estudiante_edit'),
    path('estudiantes/<int:estudiante_id>/salud/', ficha_medica_view, name='ficha_medica'),
    path('estudiantes/<int:estudiante_id>/matricular/', matricular_estudiante_view, name='matricular_estudiante'),
    path('estudiantes/<int:estudiante_id>/parientes/asignar/', asignar_responsable_view, name='asignar_responsable'),
    path('matriculas/nueva/', matricular_estudiante_view, name='matricula_create'),

    path('docentes/', docentes_list_view, name='docentes_list'),
    path('docentes/nuevo/', docente_create_view, name='docente_create'),
    path('docentes/<int:docente_id>/', docente_detail_view, name='docente_detail'),
    path('docentes/<int:docente_id>/editar/', docente_edit_view, name='docente_edit'),
    path('docentes/<int:docente_id>/estudios/add/', docente_estudio_add_view, name='docente_estudio_add'),
    path('docentes/<int:docente_id>/experiencias/add/', docente_experiencia_add_view, name='docente_experiencia_add'),

    path('parientes/', parientes_list_view, name='parientes_list'),
    path('parientes/nuevo/', pariente_create_view, name='pariente_create'),
    path('parientes/<int:pariente_id>/editar/', pariente_edit_view, name='pariente_edit'),

    # Módulos de Calificaciones y Evaluaciones
    path('evaluaciones/', evaluaciones_list_view, name='evaluaciones_list'),
    path('evaluaciones/nueva/', evaluacion_create_view, name='evaluacion_create'),
    path('evaluaciones/<int:evaluacion_id>/editar/', evaluacion_edit_view, name='evaluacion_edit'),
    path('evaluaciones/<int:evaluacion_id>/notas/', evaluacion_ingreso_notas_view, name='evaluacion_ingreso_notas'),
    path('consolidacion/', consolidacion_view, name='consolidacion'),
    path('calificaciones/sabana/', sabana_notas_view, name='sabana_notas'),
    path('calificaciones/boletin/<int:estudiante_id>/', boletin_web_view, name='boletin_web'),

    # Soporte e Incidencias
    path('support/incidencias/', incidencias_list_view, name='incidencias_list'),
    path('support/incidencias/<int:incidencia_id>/', incidencia_detail_view, name='incidencia_detail'),
    path('support/mensajes/', mensajes_inbox_view, name='mensajes_inbox'),
    path('support/mensajes/<int:mensaje_id>/', mensaje_detail_view, name='mensaje_detail'),
    
    # Reportes y Auditoría
    path('reportes/', reportes_index_view, name='reportes_index'),
    path('reportes/docentes/', descargar_reporte_docentes_view, name='descargar_reporte_docentes'),
    path('reportes/boletin/', descargar_boletin_view, name='descargar_boletin'),
    path('reportes/listado/', descargar_listado_view, name='descargar_listado'),
    path('reportes/estadisticas/', descargar_reporte_estadisticas_view, name='descargar_reporte_estadisticas'),
    path('auditoria/', auditoria_list_view, name='auditoria_list'),

    path('admin/', admin.site.urls),
]
