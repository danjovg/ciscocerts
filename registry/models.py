from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Student(models.Model):
    first_name = models.CharField("Nombres", max_length=80)
    last_name  = models.CharField("Apellidos", max_length=80)

    # Lo mantenemos para compatibilidad, se rellena siempre en save()
    full_name  = models.CharField("Nombre completo", max_length=120, editable=False)

    email = models.EmailField("Email", unique=True)
    slug  = models.SlugField("Slug", unique=True, blank=True, help_text="Identificador público (ej. jvasquez)")
    cohort = models.CharField("Promocion/Seccion", max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"

    def __str__(self) -> str:
        return self.full_name

    def save(self, *args, **kwargs):
        # mantener full_name sincronizado
        self.full_name = f"{self.first_name} {self.last_name}".strip()

        # autogenerar slug si está vacío
        if not self.slug:
            base = slugify(self.full_name) or slugify(self.email.split("@")[0])
            slug = base or "alumno"
            unique = slug
            i = 1
            # asegurar unicidad
            while Student.objects.exclude(pk=self.pk).filter(slug=unique).exists():
                i += 1
                unique = f"{slug}-{i}"
            self.slug = unique

        super().save(*args, **kwargs)


class Curso(models.Model):
    nombre = models.CharField(max_length=150)
    codigo = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='cursos/%Y/%m/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.nombre}-{self.codigo}" if self.codigo else self.nombre
            self.slug = slugify(base)[:160]
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Certification(models.Model):
    # ⚠️ Cambio clave: ahora seleccionas el curso
    course = models.ForeignKey(
        Curso, verbose_name="Curso", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="certificaciones"
    )

    # Compatibilidad con tu flujo anterior (opcional):
    # Puedes borrar este campo si empiezas desde cero.
    cert_type = models.CharField(
        "Tipo de certificacion", max_length=160, blank=True,
        help_text="Obsoleto: usar 'Curso' arriba."
    )

    student = models.ForeignKey(Student, related_name="certifications", on_delete=models.CASCADE)
    credly_url = models.URLField("URL de Credly", blank=True)
    issued_at = models.DateField("Fecha de emision", null=True, blank=True)
    badge_image = models.ImageField("Insignia (archivo)", upload_to="badges/", blank=True)
    badge_image_url = models.URLField("Imagen de insignia (URL opcional)", blank=True)

    class Meta:
        unique_together = (("student", "course"),)  # único por alumno+curso
        verbose_name = "Certificacion"
        verbose_name_plural = "Certificaciones"

    def __str__(self) -> str:
        label = self.course.codigo if self.course else (self.cert_type or "—")
        return f"{self.student.full_name} - {label}"

    @property
    def is_required(self) -> bool:
        code = self.course.codigo if self.course else self.cert_type
        return code in getattr(settings, "REQUIRED_CERTS", [])

    @property
    def badge_src(self) -> str:
        if self.badge_image:
            return self.badge_image.url
        return self.badge_image_url or ""
