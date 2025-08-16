from django.urls import path
from .views import StudentListView, StudentDetailView

app_name = "registry"

urlpatterns = [
    path("", StudentListView.as_view(), name="student-list"),
    path("alumno/<slug:slug>/", StudentDetailView.as_view(), name="student-detail"),
]
