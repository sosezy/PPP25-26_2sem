from __future__ import annotations

import math
from functools import reduce, wraps
from itertools import count, islice, chain, tee
from typing import Iterable, Iterator, Callable, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

Point = Tuple[float, float]
Polygon = Tuple[Point, ...]
PolygonIterator = Iterable[Polygon]


# ============================================================
# БАЗОВЫЕ ГЕОМЕТРИЧЕСКИЕ ФУНКЦИИ
# ============================================================


def pairwise_cycle(points: Polygon):
    for i in range(len(points)):
        yield points[i], points[(i + 1) % len(points)]



def distance(p1: Point, p2: Point) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])



def polygon_perimeter(poly: Polygon) -> float:
    return reduce(
        lambda acc, edge: acc + distance(*edge),
        pairwise_cycle(poly),
        0.0,
    )



def polygon_area(poly: Polygon) -> float:
    s = reduce(
        lambda acc, edge: acc + edge[0][0] * edge[1][1] - edge[1][0] * edge[0][1],
        pairwise_cycle(poly),
        0.0,
    )
    return abs(s) / 2



def side_lengths(poly: Polygon):
    return tuple(map(lambda e: distance(*e), pairwise_cycle(poly)))



def polygon_centroid(poly: Polygon) -> Point:
    xs = tuple(map(lambda p: p[0], poly))
    ys = tuple(map(lambda p: p[1], poly))
    return sum(xs) / len(xs), sum(ys) / len(ys)



def orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


# ============================================================
# ВИЗУАЛИЗАЦИЯ
# ============================================================


def visualize(polygons: PolygonIterator, title: str = "Polygons"):
    fig, ax = plt.subplots(figsize=(10, 8))

    for poly in polygons:
        patch = MplPolygon(poly, closed=True, fill=False, linewidth=2)
        ax.add_patch(patch)

    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.grid(True)
    ax.set_title(title)

    plt.show()


# ============================================================
# ГЕНЕРАТОРЫ БЕСКОНЕЧНЫХ ПОСЛЕДОВАТЕЛЬНОСТЕЙ
# ============================================================


def gen_rectangle(width=2, height=1, spacing=3) -> Iterator[Polygon]:
    for i in count(0):
        x = i * spacing
        yield (
            (x, 0),
            (x + width, 0),
            (x + width, height),
            (x, height),
        )



def gen_triangle(size=2, spacing=3) -> Iterator[Polygon]:
    h = math.sqrt(3) / 2 * size

    for i in count(0):
        x = i * spacing
        yield (
            (x, 0),
            (x + size / 2, h),
            (x + size, 0),
        )



def gen_hexagon(radius=1, spacing=3) -> Iterator[Polygon]:
    for i in count(0):
        cx = i * spacing

        yield tuple(
            (
                cx + radius * math.cos(math.radians(angle)),
                radius * math.sin(math.radians(angle)),
            )
            for angle in range(0, 360, 60)
        )


# ============================================================
# ТРАНСФОРМАЦИИ
# ============================================================


def tr_translate(dx: float, dy: float):
    def transform(poly: Polygon) -> Polygon:
        return tuple((x + dx, y + dy) for x, y in poly)

    return transform



def tr_rotate(angle_deg: float, center: Point = (0, 0)):
    angle = math.radians(angle_deg)
    cx, cy = center

    def transform(poly: Polygon) -> Polygon:
        def rotate_point(p):
            x, y = p
            x -= cx
            y -= cy

            xr = x * math.cos(angle) - y * math.sin(angle)
            yr = x * math.sin(angle) + y * math.cos(angle)

            return xr + cx, yr + cy

        return tuple(map(rotate_point, poly))

    return transform



def tr_symmetry(axis="x"):
    def transform(poly: Polygon) -> Polygon:
        if axis == "x":
            return tuple((x, -y) for x, y in poly)

        if axis == "y":
            return tuple((-x, y) for x, y in poly)

        if axis == "origin":
            return tuple((-x, -y) for x, y in poly)

        raise ValueError("Unknown axis")

    return transform



def tr_homothety(scale: float, center: Point = (0, 0)):
    cx, cy = center

    def transform(poly: Polygon) -> Polygon:
        return tuple(
            (
                cx + scale * (x - cx),
                cy + scale * (y - cy),
            )
            for x, y in poly
        )

    return transform


# ============================================================
# ФИЛЬТРЫ
# ============================================================


def flt_convex_polygon(poly: Polygon) -> bool:
    signs = []

    for i in range(len(poly)):
        a = poly[i]
        b = poly[(i + 1) % len(poly)]
        c = poly[(i + 2) % len(poly)]

        signs.append(orientation(a, b, c) > 0)

    return all(signs) or not any(signs)



def flt_angle_point(point: Point):
    def predicate(poly: Polygon) -> bool:
        return point in poly

    return predicate



def flt_square(max_area: float):
    def predicate(poly: Polygon) -> bool:
        return polygon_area(poly) < max_area

    return predicate



def flt_short_side(max_length: float):
    def predicate(poly: Polygon) -> bool:
        return min(side_lengths(poly)) < max_length

    return predicate



def point_inside_polygon(point: Point, poly: Polygon) -> bool:
    x, y = point
    inside = False

    for (x1, y1), (x2, y2) in pairwise_cycle(poly):
        intersects = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
        )

        if intersects:
            inside = not inside

    return inside



def flt_point_inside(point: Point):
    def predicate(poly: Polygon) -> bool:
        return point_inside_polygon(point, poly)

    return predicate



def flt_polygon_angles_inside(other: Polygon):
    def predicate(poly: Polygon) -> bool:
        return any(point_inside_polygon(p, poly) for p in other)

    return predicate


# ============================================================
# ДЕКОРАТОРЫ-ФИЛЬТРЫ
# ============================================================


def filter_decorator(predicate_factory, *factory_args):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            polygons = func(*args, **kwargs)
            predicate = predicate_factory(*factory_args)
            return filter(predicate, polygons)

        return wrapper

    return decorator


# ============================================================
# ДЕКОРАТОРЫ-ТРАНСФОРМАЦИИ
# ============================================================


def transform_decorator(transform_factory, *factory_args):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            polygons = func(*args, **kwargs)
            transform = transform_factory(*factory_args)
            return map(transform, polygons)

        return wrapper

    return decorator


# ============================================================
# АГРЕГИРУЮЩИЕ ФУНКЦИИ
# ============================================================


def agr_origin_nearest(polygons: PolygonIterator):
    points = chain.from_iterable(polygons)

    return reduce(
        lambda best, p: p
        if distance((0, 0), p) < distance((0, 0), best)
        else best,
        points,
    )



def agr_max_side(polygons: PolygonIterator):
    return reduce(
        lambda best, poly: max(best, max(side_lengths(poly))),
        polygons,
        0.0,
    )



def agr_min_area(polygons: PolygonIterator):
    return reduce(
        lambda best, poly: min(best, polygon_area(poly)),
        polygons,
        float("inf"),
    )



def agr_perimeter(polygons: PolygonIterator):
    return reduce(
        lambda total, poly: total + polygon_perimeter(poly),
        polygons,
        0.0,
    )



def agr_area(polygons: PolygonIterator):
    return reduce(
        lambda total, poly: total + polygon_area(poly),
        polygons,
        0.0,
    )


# ============================================================
# ZIP POLYGONS
# ============================================================


def zip_polygons(*iterators: PolygonIterator) -> Iterator[Polygon]:
    return map(
        lambda polys: tuple(chain.from_iterable(polys)),
        zip(*iterators),
    )


# ============================================================
# ДОПОЛНИТЕЛЬНЫЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================


def apply_transform(polygons: PolygonIterator, transform):
    return map(transform, polygons)



def apply_filter(polygons: PolygonIterator, predicate):
    return filter(predicate, polygons)


# ============================================================
# ДЕМОНСТРАЦИЯ РАБОТЫ
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # 1. Семь фигур каждого типа
    # --------------------------------------------------------

    rectangles = islice(gen_rectangle(), 7)
    triangles = islice(gen_triangle(), 7)
    hexagons = islice(gen_hexagon(), 7)

    visualize(rectangles, "Rectangles")
    visualize(triangles, "Triangles")
    visualize(hexagons, "Hexagons")

    # --------------------------------------------------------
    # 2. Три параллельные ленты
    # --------------------------------------------------------

    base = islice(gen_rectangle(), 7)

    band1 = map(tr_translate(0, 0), base)
    band2 = map(tr_translate(0, 4), islice(gen_rectangle(), 7))
    band3 = map(tr_translate(0, 8), islice(gen_rectangle(), 7))

    angled = map(tr_rotate(25), chain(band1, band2, band3))

    visualize(angled, "Three Parallel Bands")

    # --------------------------------------------------------
    # 3. Две пересекающиеся ленты
    # --------------------------------------------------------

    line1 = map(tr_rotate(25), islice(gen_rectangle(), 7))

    line2 = map(
        tr_translate(5, 2),
        map(tr_rotate(-25), islice(gen_rectangle(), 7)),
    )

    visualize(chain(line1, line2), "Intersecting Bands")

    # --------------------------------------------------------
    # 4. Симметричные ленты треугольников
    # --------------------------------------------------------

    t1 = map(tr_translate(0, 4), islice(gen_triangle(), 7))

    t2 = map(
        tr_translate(0, -4),
        map(tr_symmetry("x"), islice(gen_triangle(), 7)),
    )

    visualize(chain(t1, t2), "Symmetric Triangle Bands")

    # --------------------------------------------------------
    # 5. Четырёхугольники разного масштаба
    # --------------------------------------------------------

    scales = map(lambda x: 1 + x * 0.3, range(15))

    scaled_rectangles = map(
        lambda pair: tr_homothety(pair[0])(pair[1]),
        zip(scales, islice(gen_rectangle(), 15)),
    )

    visualize(scaled_rectangles, "Scaled Rectangles")

    # --------------------------------------------------------
    # 6. Применение фильтров
    # --------------------------------------------------------

    polygons = list(islice(gen_rectangle(), 15))

    filtered = list(
        filter(
            flt_short_side(1.5),
            polygons,
        )
    )

    print("Filtered polygons:", len(filtered))

    # --------------------------------------------------------
    # 7. Агрегирующие функции
    # --------------------------------------------------------

    polygons = list(islice(gen_triangle(), 10))

    print("Nearest point:", agr_origin_nearest(polygons))
    print("Max side:", agr_max_side(polygons))
    print("Min area:", agr_min_area(polygons))
    print("Total perimeter:", agr_perimeter(polygons))
    print("Total area:", agr_area(polygons))

    # --------------------------------------------------------
    # 8. Zip polygons
    # --------------------------------------------------------

    p1 = [
        ((1, 1), (2, 2), (3, 1)),
        ((11, 11), (12, 12), (13, 11)),
    ]

    p2 = [
        ((1, -1), (2, -2), (3, -1)),
        ((11, -11), (12, -12), (13, -11)),
    ]

    zipped = list(zip_polygons(p1, p2))

    print("Zipped polygons:")

    for poly in zipped:
        print(poly)

    visualize(zipped, "Zip Polygons")


# ============================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ДЕКОРАТОРОВ
# ============================================================


@filter_decorator(flt_square, 5)
def small_polygons():
    return gen_rectangle()


@transform_decorator(tr_translate, 10, 5)
def moved_polygons():
    return gen_triangle()


# ============================================================
# ПРИМЕР КОМПОЗИЦИИ ФУНКЦИЙ
# ============================================================


def compose(*functions):
    return reduce(
        lambda f, g: lambda x: f(g(x)),
        functions,
        lambda x: x,
    )


complex_transform = compose(
    tr_translate(10, 0),
    tr_rotate(45),
    tr_homothety(1.5),
)
