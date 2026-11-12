"""Candidate regression tests for the approved v5 interface geometry."""
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from lmmp_charts.geometry.curves import CurveGeometry
from lmmp_charts.geometry.rectangle import Rectangle, RectangleGeometry
from lmmp_charts.geometry.triangle import Triangle, TriangleGeometry


class CurveTests(unittest.TestCase):
    def test_direction_is_unit_vector(self):
        np.testing.assert_allclose(CurveGeometry.direction(45), np.array([2**-0.5, 2**-0.5]))

    def test_bezier_endpoints(self):
        p0 = [0, 0]
        p3 = [1, 1]
        curve = CurveGeometry.cubic_bezier(p0, [0, 1], [1, 0], p3)
        self.assertEqual(curve.shape, (220, 2))
        np.testing.assert_allclose(curve[0], p0)
        np.testing.assert_allclose(curve[-1], p3)

    def test_arc_start_end(self):
        arc = CurveGeometry.circular_arc([0, 0], 2, 0, 90)
        np.testing.assert_allclose(arc[0], [2, 0], atol=1e-14)
        np.testing.assert_allclose(arc[-1], [0, 2], atol=1e-14)

    def test_invalid_samples(self):
        with self.assertRaises(ValueError):
            CurveGeometry.cubic_bezier([0,0], [1,1], [2,2], [3,3], n_points=1)
        with self.assertRaises(ValueError):
            CurveGeometry.circular_arc([0,0], -1, 0, 90)


class RectanglePrimitiveTests(unittest.TestCase):
    def test_from_bounds_creates_ordered_vertices_and_edges(self):
        rectangle = Rectangle.from_bounds(1, 2, 5, 7)
        np.testing.assert_array_equal(
            rectangle.vertices,
            [[1, 2], [5, 2], [5, 7], [1, 7]],
        )
        np.testing.assert_array_equal(
            rectangle.edges,
            [
                [[1, 2], [5, 2]],
                [[5, 2], [5, 7]],
                [[5, 7], [1, 7]],
                [[1, 7], [1, 2]],
            ],
        )

    def test_accepts_rotated_rectangle(self):
        rectangle = Rectangle(np.array([[0, 0], [1, 1], [0, 2], [-1, 1]]))
        self.assertEqual(rectangle.vertices.shape, (4, 2))

    def test_rejects_invalid_vertices(self):
        for vertices in (
            [[0, 0], [1, 0], [1, 1]],
            [[0, 0], [1, 0], [2, 1], [0, 1]],
            [[0, 0], [1, 0], [1, float("nan")], [0, 1]],
        ):
            with self.subTest(vertices=vertices), self.assertRaises(ValueError):
                Rectangle(np.asarray(vertices))

    def test_from_bounds_rejects_nonpositive_or_nonfinite_dimensions(self):
        for bounds in ((1, 0, 1, 2), (0, 2, 1, 1), (0, 0, float("inf"), 1)):
            with self.subTest(bounds=bounds), self.assertRaises(ValueError):
                Rectangle.from_bounds(*bounds)

    def test_vertices_are_read_only(self):
        rectangle = Rectangle.from_bounds(0, 0, 1, 1)
        with self.assertRaises(ValueError):
            rectangle.vertices[0, 0] = 4


class TrianglePrimitiveTests(unittest.TestCase):
    def test_vertices_and_edges(self):
        triangle = Triangle(np.array([[0, 0], [3, 0], [0, 4]]))
        np.testing.assert_array_equal(
            triangle.edges,
            [
                [[0, 0], [3, 0]],
                [[3, 0], [0, 4]],
                [[0, 4], [0, 0]],
            ],
        )

    def test_rejects_invalid_or_degenerate_vertices(self):
        for vertices in (
            [[0, 0], [1, 0]],
            [[0, 0], [1, 0], [2, 0]],
            [[0, 0], [1, 0], [float("inf"), 1]],
        ):
            with self.subTest(vertices=vertices), self.assertRaises(ValueError):
                Triangle(np.asarray(vertices))

    def test_vertices_are_read_only(self):
        triangle = Triangle(np.array([[0, 0], [1, 0], [0, 1]]))
        with self.assertRaises(ValueError):
            triangle.vertices[0, 0] = 4


class RectangleTests(unittest.TestCase):
    def test_v5_fixed_coordinates(self):
        data = RectangleGeometry().calculate(45)
        np.testing.assert_array_equal(data.contact_point, [6.15, 11.0])
        np.testing.assert_array_equal(data.interface_curve[-1], [8.45, 15.3])
        np.testing.assert_array_equal(data.rock_segment, [[1.2, 11], [10.8, 11]])

    def test_curve_tangent(self):
        data = RectangleGeometry().calculate(45)
        tangent = data.interface_curve[1] - data.interface_curve[0]
        tangent /= np.linalg.norm(tangent)
        self.assertGreater(float(np.dot(tangent, data.tangent_direction)), .999)

    def test_invalid_theta(self):
        for theta in (-1, 0, 90, float("nan"), True):
            with self.subTest(theta=theta), self.assertRaises(ValueError):
                RectangleGeometry().calculate(theta)


class TriangleTests(unittest.TestCase):
    def test_v5_fixed_coordinates(self):
        data = TriangleGeometry().calculate(45, 75, 25)
        np.testing.assert_allclose(data.corner, [1.30, 0.94])
        np.testing.assert_allclose(data.lower_contact, [7.128, 0.94])
        np.testing.assert_allclose(data.inclined_contact,
                                   [1.30 + .62 * 9.4 * .5, 0.94 + .62 * 9.4 * np.sin(np.pi / 3)])
        self.assertEqual(data.meniscus.shape, (220, 2))
        np.testing.assert_allclose(data.meniscus[0], data.lower_contact)
        np.testing.assert_allclose(data.meniscus[-1], data.inclined_contact)

    def test_contact_tangent_for_full_v5_domain(self):
        for theta in (10, 25, 45, 55, 60, 70, 85):
            with self.subTest(theta=theta):
                data = TriangleGeometry().calculate(theta, (theta+90)/2, theta/2)
                tangent = data.meniscus[1] - data.meniscus[0]
                tangent /= np.linalg.norm(tangent)
                self.assertGreater(float(np.dot(tangent, data.tangent_direction)), .999)

    def test_hysteresis_rays_reference_same_lower_point(self):
        data = TriangleGeometry().calculate(45, 75, 25)
        np.testing.assert_allclose(data.tangent_direction, CurveGeometry.direction(135))
        np.testing.assert_allclose(data.advancing_direction, CurveGeometry.direction(105))
        np.testing.assert_allclose(data.receding_direction, CurveGeometry.direction(155))

    def test_meniscus_does_not_depend_on_hysteresis_angles(self):
        g = TriangleGeometry()
        a = g.calculate(45, 75, 25)
        b = g.calculate(45, 80, 10)
        np.testing.assert_array_equal(a.meniscus, b.meniscus)

    def test_invalid_order(self):
        for args in [(45, 30, 25), (45, 90, 25), (45, 75, 50), (0, 75, 0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                TriangleGeometry().calculate(*args)


class V5ParityTests(unittest.TestCase):
    """Numerically precise comparison against stored coordinates from v5.

    The reference fixture is intentionally independent of the old module.
    """

    @classmethod
    def setUpClass(cls):
        cls.reference = np.load(Path(__file__).with_name('v5_geometry_reference.npz'))

    @classmethod
    def tearDownClass(cls):
        cls.reference.close()

    def test_rectangle_matches_v5_bezier(self):
        new = RectangleGeometry().calculate(45).interface_curve
        np.testing.assert_allclose(new, self.reference['rectangle_45'], rtol=0, atol=2e-15)

    def test_triangle_matches_v5_arc(self):
        for theta in (10, 25, 45, 55, 60, 70, 85):
            with self.subTest(theta=theta):
                new = TriangleGeometry().calculate(theta, (theta + 90) / 2, theta / 2)
                np.testing.assert_array_equal(
                    new.inclined_contact, self.reference[f'triangle_{theta}_P'])
                np.testing.assert_array_equal(
                    new.lower_contact, self.reference[f'triangle_{theta}_Q'])
                np.testing.assert_array_equal(
                    new.meniscus, self.reference[f'triangle_{theta}_arc'])


if __name__ == '__main__':
    unittest.main()
