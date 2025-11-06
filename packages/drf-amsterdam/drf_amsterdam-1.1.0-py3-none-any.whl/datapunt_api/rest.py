from typing import TYPE_CHECKING, Any, Generic, TypeVar

from django.db.models import Model, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import renderers, viewsets
from rest_framework.pagination import BasePagination
from rest_framework.renderers import BaseRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework_xml.renderers import XMLRenderer

from .pagination import HALPagination
from .renderers import PaginatedCSVRenderer
from .serializers import (DisplayField, HALSerializer,  # noqa: F401
                          LinksField, RelatedSummaryField,
                          SelfLinkSerializerMixin, get_links)

_MT = TypeVar("_MT", bound=Model)
_MT_co = TypeVar("_MT_co", bound=Model, covariant=True)


DEFAULT_RENDERERS: list[type[BaseRenderer]] = [
    renderers.JSONRenderer,
    PaginatedCSVRenderer,
    renderers.BrowsableAPIRenderer,
    XMLRenderer,
]


if api_settings.DEFAULT_RENDERER_CLASSES:
    # The APISettings class automagically converts the strings to classes
    DEFAULT_RENDERERS = api_settings.DEFAULT_RENDERER_CLASSES  # type: ignore


class _DisabledHTMLFilterBackend(DjangoFilterBackend):
    """See https://github.com/tomchristie/django-rest-framework/issues/3766.

    This prevents DRF from generating the filter dropdowns (which can be HUGE
    in our case)
    """

    def to_html(self, request: Request, queryset: QuerySet[_MT], view: APIView) -> str:
        return ""


def _is_detailed_request(detailed_keyword: str, request: Request) -> bool:
    value = request.GET.get(detailed_keyword, False)
    if value and value in [1, '1', True, 'True', 'yes']:
        return True

    return False


if TYPE_CHECKING:
    class ReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet[_MT_co]):
        pass

    class BaseDetailSerializerMixin(DetailSerializerMixin[_MT_co]):
        pass
else:
    class ReadOnlyModelViewSet(Generic[_MT_co], viewsets.ReadOnlyModelViewSet):
        pass

    class BaseDetailSerializerMixin(Generic[_MT_co], DetailSerializerMixin):
        pass


class DatapuntViewSet(BaseDetailSerializerMixin[_MT_co], ReadOnlyModelViewSet[_MT_co]):
    """ViewSet subclass for use in Datapunt APIs.

    Note:
    - this uses HAL JSON style pagination.
    """

    renderer_classes: list[type[BaseRenderer]] = DEFAULT_RENDERERS
    pagination_class: type[BasePagination] = HALPagination
    filter_backends = [_DisabledHTMLFilterBackend]
    # TO restore filter box in your view!
    # filter_backends = [DjangoFilterBackend]
    detailed_keyword: str = 'detailed'

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Checking if a detailed response is required
        if _is_detailed_request(self.detailed_keyword, request):
            self.serializer_class = self.serializer_detail_class
        return super().list(request, *args, **kwargs)

    def get_renderer_context(self) -> dict[str, Any]:
        # make CSV select fields to render.
        context = super().get_renderer_context()
        context['header'] = (
            self.request.GET['fields'].split(',')
            if 'fields' in self.request.GET else None)
        return context


if TYPE_CHECKING:
    class ModelViewSet(viewsets.ModelViewSet[_MT_co]):
        pass
else:
    class ModelViewSet(Generic[_MT_co], viewsets.ModelViewSet):
        pass


class DatapuntViewSetWritable(BaseDetailSerializerMixin[_MT_co], ModelViewSet[_MT_co]):
    """ViewSet subclass for use in Datapunt APIs.

    Note:
    - this uses HAL JSON style pagination.
    """

    renderer_classes: list[type[BaseRenderer]] = DEFAULT_RENDERERS
    pagination_class: type[BasePagination] = HALPagination
    filter_backends = [_DisabledHTMLFilterBackend]

    detailed_keyword: str = 'detailed'

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # Checking if a detailed response is required
        if _is_detailed_request(self.detailed_keyword, request):
            self.serializer_class = self.serializer_detail_class
        return super().list(request, *args, **kwargs)
