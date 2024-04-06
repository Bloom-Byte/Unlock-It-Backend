"""UnlockIt Swagger API Documentation Generator


"""

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator

from rest_framework import permissions


class CoreAPISchemeGenerator(OpenAPISchemaGenerator):
    """
    This Generator class is in charge of generating the OpenAPI schema for the UnlockIt API.
    It exposes the HTTP and HTTPS schemes for the API.
    The HTTP is to be used when developing locally, which the HTTPS is to be used when viewing the API documentation in production.
    """

    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.base_path = "/api/v1/"
        schema.schemes = ["http", "https"]

        return schema


core_schema_view = get_schema_view(
    openapi.Info(
        title="UnlockIt API Documentation",
        default_version="v1",
        description="API documentation",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    urlconf="app.urls",
    generator_class=CoreAPISchemeGenerator,
)
