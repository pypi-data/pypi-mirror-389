from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from datapunt_api.rest import HALSerializer
from datapunt_api.serializers import (DataSetSerializerMixin, DisplayField,
                                      MultipleGeometryField,
                                      RelatedSummaryField,
                                      SelfLinkSerializerMixin)
from tests import models


class WeatherStationSerializer(HALSerializer):
    class Meta:
        model = models.WeatherStation
        fields = '__all__'


class DatasetSerializer(DataSetSerializerMixin, ModelSerializer):
    dataset = 'test_dataset'

    class Meta:
        model = models.SimpleModel
        fields = '__all__'


class SelfLinksSerializer(SelfLinkSerializerMixin, ModelSerializer):
    _links = serializers.SerializerMethodField()

    class Meta:
        model = models.SimpleModel
        fields = '__all__'


class WeatherDetailStationSerializer(HALSerializer):

    detailed = serializers.SerializerMethodField()

    class Meta:
        model = models.WeatherStation
        fields = [
            '_links',
            'number',
            'detailed'
        ]

    def get_detailed(self, obj):
        return 'I am detailed'


class TemperatureRecordSerializer(HALSerializer):
    class Meta:
        model = models.TemperatureRecord
        fields = '__all__'


class DisplayFieldSerializer(ModelSerializer):
    _display = DisplayField()

    class Meta:  # noqa
        model = models.WeatherStation
        fields = '__all__'


class ThingSerializer(ModelSerializer):
    class Meta:
        model = models.Thing
        fields = '__all__'


class PersonSerializer(ModelSerializer):
    things = RelatedSummaryField()

    class Meta:
        model = models.Person
        fields = '__all__'


class LocationSerializer(ModelSerializer):
    geometrie = MultipleGeometryField()

    class Meta:
        model = models.Location
        fields = '__all__'


class DetailedPersonSerializer(ModelSerializer):
    things = RelatedSummaryField()
    detailed = serializers.SerializerMethodField()

    class Meta:
        model = models.Person
        fields = '__all__'

    def get_detailed(self, obj: models.Person) -> str:
        return "Yes, detailed isn't it?"
