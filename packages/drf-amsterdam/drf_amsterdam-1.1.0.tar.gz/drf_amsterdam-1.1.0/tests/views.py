"""Test views."""
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet,
                                           filters)
from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ReadOnlyModelViewSet

from datapunt_api import bbox
from datapunt_api.rest import (DatapuntViewSet, DatapuntViewSetWritable,
                               _DisabledHTMLFilterBackend)
from tests.models import (Person, SimpleModel, TemperatureRecord, Thing,
                          WeatherStation)
from tests.serializers import (DetailedPersonSerializer, PersonSerializer,
                               SelfLinksSerializer,
                               TemperatureRecordSerializer, ThingSerializer,
                               WeatherDetailStationSerializer,
                               WeatherStationSerializer)


class WeatherFilter(FilterSet):
    """Weather station fitler.

    test geo location filtering
    """

    location = filters.CharFilter(
        method="locatie_filter", label='x,y,r')

    location_rd = filters.CharFilter(
        method="locatie_filter_rd", label='x,y,r')

    def locatie_filter(self, qs, name, value):  # noqa
        point, radius = bbox.parse_xyr(value)
        return qs.filter(
            centroid__geometrie__dwithin=(point, radius))

    def locatie_filter_rd(self, qs, name, value):  # noqa
        point, radius = bbox.parse_xyr(value, srid=28992)
        return qs.filter(
            centroid_rd__dwithin=(point, radius))

    class Meta(object): # noqa
        model = WeatherStation

        fields = (
            "location",
            "location_rd",
        )


class WeatherStationViewSet(DatapuntViewSet):  # noqa
    serializer_class = WeatherStationSerializer
    serializer_detail_class = WeatherDetailStationSerializer
    queryset = WeatherStation.objects.all().order_by('id')

    filter_class = WeatherFilter

    filter_backends = (
        _DisabledHTMLFilterBackend,
        DjangoFilterBackend,
        OrderingFilter
    )

    ordering_fields = '__all__'


class TemperatureRecordViewSet(DatapuntViewSet): # noqa
    serializer_class = TemperatureRecordSerializer
    serializer_detail_class = TemperatureRecordSerializer
    queryset = TemperatureRecord.objects.all().order_by('date')

    # test custom inheritance.
    def list(self, request, *args, **kwargs):  # noqa
        return super().list(self, request, *args, **kwargs)


class SimpleViewSet(ReadOnlyModelViewSet):
    queryset = SimpleModel.objects.all().order_by('id')
    serializer_class = SelfLinksSerializer


class ThingViewSet(ReadOnlyModelViewSet):
    queryset = Thing.objects.all().order_by('id')
    serializer_class = ThingSerializer


class PersonViewSet(DatapuntViewSetWritable):
    queryset = Person.objects.all().order_by('id')
    serializer_class = PersonSerializer
    serializer_detail_class = DetailedPersonSerializer
