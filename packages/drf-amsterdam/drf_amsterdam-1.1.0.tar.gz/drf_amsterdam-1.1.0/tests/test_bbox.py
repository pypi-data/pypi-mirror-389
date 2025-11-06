from unittest.mock import Mock

from django.contrib.gis.geos import Point
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from datapunt_api.bbox import (BBOX, determine_bbox, dist_to_deg, parse_xyr,
                               valid_bbox)


class ValidBboxTestCase(TestCase):
    def test_valid_bbox(self):
        bbox, err = valid_bbox("4.58565,52.03560,5.31360,52.10000")
        self.assertEqual(bbox, [4.58565, 52.03560, 5.31360, 52.10000])
        self.assertIsNone(err)

    def test_invalid_bbox(self):
        # Too few values
        bbox, err = valid_bbox("invalid_bbox")
        self.assertEqual(bbox, [])
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        bbox, err = valid_bbox("1,2,3")
        self.assertEqual(bbox, [])
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        # Too many values
        bbox, err = valid_bbox("1,2,3,4,5,6,7")
        self.assertEqual(bbox, [])
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        # Values are not floats
        bbox, err = valid_bbox("a,b,c,d")
        self.assertEqual(bbox, [])
        self.assertEqual(err, "Did not receive floats")

        # Mixed values
        bbox, err = valid_bbox("1,2.0,A,B")
        self.assertEqual(bbox, [])
        self.assertEqual(err, "Did not receive floats")

    def test_valid_bbox_invalid_coordinates(self):
        # Test case with coordinates outside the bounding box
        bboxp = "3.6,52.1,5.2,52.4"
        bbox, err = valid_bbox(bboxp)
        self.assertEqual(bbox, [3.6, 52.1, 5.2, 52.4])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lon not within max bbox 5.3136 > 3.6 > 4.58565")

        bboxp = "5.2,52.1,5.7,52.4"
        bbox, err = valid_bbox(bboxp)
        self.assertEqual(bbox, [5.2, 52.1, 5.7, 52.4])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lon not within max bbox 5.3136 > 5.7 > 4.58565")

        bboxp = "4.9,51.1,5.2,52.4"
        bbox, err = valid_bbox(bboxp)
        self.assertEqual(bbox, [4.9, 51.1, 5.2, 52.4])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lat not within max bbox 52.48769 > 51.1 > 52.0356")

        bboxp = "4.9,52.1,5.2,53.4"
        bbox, err = valid_bbox(bboxp)
        self.assertEqual(bbox, [4.9, 52.1, 5.2, 53.4])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lat not within max bbox 52.48769 > 53.4 > 52.0356")

    def test_valid_bbox_invalid_coordinates_28992(self):
        # Test case with coordinates outside the bounding box
        bboxp = "93000,470000,96000,485000"
        bbox, err = valid_bbox(bboxp, srid=28992)
        self.assertEqual(bbox, [93000, 470000, 96000, 485000])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lon not within max bbox 170000 > 93000.0 > 94000")

        bboxp = "95000,470000,180000,485000"
        bbox, err = valid_bbox(bboxp, srid=28992)
        self.assertEqual(bbox, [95000, 470000, 180000, 485000])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lon not within max bbox 170000 > 180000.0 > 94000")

        bboxp = "95000,460000,96000,485000"
        bbox, err = valid_bbox(bboxp, srid=28992)
        self.assertEqual(bbox, [95000, 460000, 96000, 485000])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lat not within max bbox 514000 > 460000.0 > 465000")

        bboxp = "95000,470000,96000,520000"
        bbox, err = valid_bbox(bboxp, srid=28992)
        self.assertEqual(bbox, [95000, 470000, 96000, 520000])
        self.assertIsNotNone(err)
        self.assertEqual(err, "lat not within max bbox 514000 > 520000.0 > 465000")


class DetermineBboxTestCase(TestCase):
    def test_default_bbox(self):
        request = Mock()
        request.query_params = {}

        bbox, err = determine_bbox(request)
        self.assertEqual(bbox, BBOX)
        self.assertIsNone(err)

    def test_valid_bbox(self):
        request = Mock()
        request.query_params = {"bbox": "4.58565,52.03560,5.31360,52.10000"}

        bbox, err = determine_bbox(request)
        self.assertEqual(bbox, [4.58565, 52.03560, 5.31360, 52.10000])
        self.assertIsNone(err)

    def test_invalid_bbox(self):
        # Too few values
        request = Mock()
        request.query_params = {"bbox": "invalid_bbox"}

        bbox, err = determine_bbox(request)
        self.assertIsNone(bbox)
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        request.query_params = {"bbox": "1,2"}
        bbox, err = determine_bbox(request)
        self.assertIsNone(bbox)
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        # Too many values
        request.query_params = {"bbox": "1,2,3,4,5"}
        bbox, err = determine_bbox(request)
        self.assertIsNone(bbox)
        self.assertEqual(err, "wrong numer of arguments (lon, lat, lon, lat)")

        # Values are not floats
        request.query_params = {"bbox": "a,b,c,d"}
        bbox, err = determine_bbox(request)
        self.assertIsNone(bbox)
        self.assertEqual(err, "Did not receive floats")

        # Mixed values
        request.query_params = {"bbox": "1,2.0,A,B"}
        bbox, err = determine_bbox(request)
        self.assertIsNone(bbox)
        self.assertEqual(err, "Did not receive floats")


class DistanceToDegreeTestCase(TestCase):
    def test_distance_lat_0(self):
        lat = 0.0
        distance = 1000
        expected_output = 0.00898312

        result = dist_to_deg(distance, lat)
        self.assertAlmostEqual(result, expected_output, places=8)  # Allowing for some rounding error

    def test_distance_lat_45(self):
        lat = 45.0
        distance = 500
        expected_output = 0.00526219

        result = dist_to_deg(distance, lat)
        self.assertAlmostEqual(result, expected_output, places=8)  # Allowing for some rounding error

    def test_distance_lat_minus_75(self):
        lat = -75.0
        distance = 1264
        expected_output = 0.01804019

        result = dist_to_deg(distance, lat)
        self.assertAlmostEqual(result, expected_output, places=8)  # Allowing for some rounding error

    def test_distance_lat_53_25367(self):
        lat = 52.25367
        distance = 80
        expected_output = 0.000891532

        result = dist_to_deg(distance, lat)
        self.assertAlmostEqual(result, expected_output, places=8)  # Allowing for some rounding error


class ParseXYRTestCase(TestCase):
    def test_valid_input_srid(self):
        input_string = '52.03560,4.58565,45.0'
        expected_point = Point(x=52.03560, y=4.58565, srid=4326)

        point, radius = parse_xyr(input_string)
        self.assertEqual(point, expected_point)
        self.assertAlmostEqual(radius, 0.00050055, places=8)  # Allowing for some rounding error

    def test_valid_input_srid_28992(self):
        input_string = '123456.789,987654.321,45.0'
        expected_point = Point(x=123456.789, y=987654.321, srid=28992).transform(ct=4326, clone=True)

        point, radius = parse_xyr(input_string)
        self.assertEqual(point, expected_point)
        self.assertEqual(radius, 45.0)

    def test_invalid_input_missing_radius(self):
        # Test with invalid input format: "12.34,56.78" (missing radius)
        input_string = "12.34,56.78"
        with self.assertRaises(ValidationError):
            parse_xyr(input_string)

    def test_invalid_input_type(self):
        # Test with input containing non-numeric values: "12.34,invalid,100"
        input_string = "12.34,invalid,100"
        with self.assertRaises(ValidationError):
            parse_xyr(input_string)

    def test_invalid_input_type_radius(self):
        # Test with invalid radius type (should be a float): "12.34,56.78,invalid"
        input_string = "12.34,56.78,invalid"
        with self.assertRaises(ValidationError):
            parse_xyr(input_string)
