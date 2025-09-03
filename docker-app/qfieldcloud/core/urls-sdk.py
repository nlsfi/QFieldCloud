from django.urls import include, path
from rest_framework.routers import DefaultRouter

from qfieldcloud.core.urls import router as original_router
from qfieldcloud.core.urls import urlpatterns as original_urls
from qfieldcloud.core.views import (
    projects_views,
)
from qfieldcloud.filestorage.views import FileCrudViewAdmin, FileListViewAdmin

router = DefaultRouter()
router.register(r"projects", projects_views.ProjectViewSetAdmin, basename="project")

# Copy everything from the old router except "projects"
for prefix, viewset, basename in original_router.registry:
    if prefix != "projects":
        router.register(prefix, viewset, basename=basename)

urlpatterns = [
    *[
        p
        for p in original_urls
        if not (p.pattern._route == "" or p.pattern._route.startswith("files/"))
    ],  # everything except old router (projects) and file urls
    path("", include(router.urls)),
    path(
        "files/<uuid:project_id>/",
        FileListViewAdmin.as_view(),
        name="filestorage_list_files",
    ),
    path(
        "files/<uuid:project_id>/<path:filename>/",
        FileCrudViewAdmin.as_view(),
        name="filestorage_crud_file",
    ),
]
