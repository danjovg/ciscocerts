from datetime import date
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q
from .models import Student, Certification, Curso

# Config desde settings
REQUIRED = list(getattr(settings, "REQUIRED_CERTS", []))          # p.ej. ["IC", "CBHC"]
REQUIRED_BADGES = dict(getattr(settings, "REQUIRED_BADGES", {}))  # opcional (fallbacks)
ALIASES = dict(getattr(settings, "REQUIRED_CERT_ALIASES", {}))    # opcional (alias de códigos)

def _norm(code: str | None) -> str | None:
    """Normaliza un código usando los alias (si existen)."""
    if not code:
        return None
    return ALIASES.get(code, code)


# ------------------------------
# Listado de alumnos
# ------------------------------
class StudentListView(ListView):
    model = Student
    template_name = "registry/student_list.html"
    context_object_name = "students"

    def get_queryset(self):
        q = self.request.GET.get("q", "")
        sort = self.request.GET.get("sort", "apellido")  # "apellido" | "nombre"
        order = ["last_name", "first_name"] if sort == "apellido" else ["first_name", "last_name"]

        qs = (
            Student.objects
                   .all()
                   .prefetch_related("certifications__course")
                   .order_by(*order)
        )
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["sort"] = self.request.GET.get("sort", "apellido")

        # Nombres legibles de los cursos requeridos para el pie del listado
        courses = Curso.objects.filter(codigo__in=REQUIRED)
        code_to_name = {c.codigo: c.nombre for c in courses}
        ctx["required"] = REQUIRED
        ctx["required_names"] = [code_to_name.get(code, code) for code in REQUIRED]
        return ctx


# ------------------------------
# Ficha del alumno
# ------------------------------
class StudentDetailView(DetailView):
    model = Student
    template_name = "registry/student_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "student"

    def get_queryset(self):
        # Trae certificaciones y cursos asociados de una vez
        return Student.objects.prefetch_related("certifications__course")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student: Student = ctx["student"]

        # Todas las certificaciones del alumno
        certs = list(Certification.objects.select_related("course").filter(student=student))

        # Índice por código normalizado del curso requerido (toma la más reciente)
        by_norm: dict[str, Certification] = {}
        extras: list[Certification] = []

        for c in certs:
            # Soporta registros antiguos con cert_type y los nuevos con relación a Curso
            code = c.course.codigo if c.course else (c.cert_type or None)
            ncode = _norm(code)

            if ncode in REQUIRED:
                cur = by_norm.get(ncode)
                # Conserva la más reciente por issued_at
                if not cur or (c.issued_at or date.min) > (cur.issued_at or date.min):
                    by_norm[ncode] = c
            else:
                extras.append(c)

        # Mapa de cursos requeridos: código -> objeto (para nombre e imagen)
        courses = {c.codigo: c for c in Curso.objects.filter(codigo__in=REQUIRED)}

        # Estructura para el template (tarjetas requeridas)
        required_rows = []
        for code in REQUIRED:
            course = courses.get(code)

            # Imagen del curso (fallback si no hay badge en la certificación)
            course_img = ""
            if course and getattr(course, "imagen", None):
                try:
                    course_img = course.imagen.url
                except Exception:
                    course_img = ""

            required_rows.append({
                "code": code,
                "name": course.nombre if course else code,   # nombre bonito o código
                "cert": by_norm.get(code),                   # Certification o None
                "course_img": course_img,                    # imagen del curso (fallback)
                "fallback": REQUIRED_BADGES.get(code, ""),   # imagen estática opcional
            })

        ctx.update({
            "required_rows": required_rows,
            "extras": extras,
            "required": REQUIRED,
            "has_all": all(code in by_norm for code in REQUIRED),
        })
        return ctx
