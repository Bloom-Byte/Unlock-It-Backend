from django.contrib import admin
from django.urls import path, include
from django.conf import settings


from .docs_generator import core_schema_view


urlpatterns = [
    path("lskjdflksdjflksfsf/", admin.site.urls),
    path("api/v1/", include("app.urls")),
]


if settings.SHOW_DOCS:
    urlpatterns += [  # documentation paths
        path(
            "docs/",
            core_schema_view.with_ui("swagger", cache_timeout=0),
            name="core-swagger-ui",
        )
    ]


handler404 = "app.views.handler404"
