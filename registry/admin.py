from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Certification, Curso

# ---------- Curso ----------
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "activo", "preview")
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}
    readonly_fields = ("preview", "creado", "modificado")

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:120px;border-radius:8px"/>', obj.imagen.url)
        return "—"
    preview.short_description = "Vista previa"


# ---------- Inline de Certificación en Student ----------
class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1
    autocomplete_fields = ("course",)
    fields = ("course", "credly_url", "issued_at", "badge_image", "badge_image_url")


# Acción para rellenar slugs vacíos (usa save())
@admin.action(description="Regenerar slug desde el nombre")
def regenerate_slug(modeladmin, request, queryset):
    count = 0
    for s in queryset:
        if not s.slug:
            s.save()
            count += 1
    modeladmin.message_user(request, f"Slugs generados: {count}")

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "email", "cohort", "slug")
    search_fields = ("last_name", "first_name", "email", "slug")
    # Puedes dejarlo comentado si prefieres que SOLO el save() maneje el slug
    # prepopulated_fields = {"slug": ("first_name", "last_name")}
    readonly_fields = ("slug", "full_name")
    inlines = [CertificationInline]
    actions = [regenerate_slug]


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "issued_at")
    search_fields = ("student__first_name", "student__last_name", "course__nombre", "course__codigo")
    autocomplete_fields = ("student", "course")
    list_filter = ("issued_at",)
