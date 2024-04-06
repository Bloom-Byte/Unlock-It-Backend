"""UnlockIt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/

Examples:
Function views

- 1. Add an import:  from my_app import views
- 2. Add a URL to urlpatterns:  path('', views.home, name='home')

Class-based views

- 1. Add an import:  from other_app.views import Home
- 2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')

Including another URLconf

- 1. Import the include() function: from django.urls import include, path
- 2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

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
