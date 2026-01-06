from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # API routes
    path("api/", include("apps.catalog.api.urls")),
    path("api/", include("apps.orders.api.urls")),
]
