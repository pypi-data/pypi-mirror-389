import math

class Geometry:
    def area_circle(self, radius):
        return math.pi * radius ** 2

    def perimeter_circle(self, radius):
        return 2 * math.pi * radius

    def area_rectangle(self, length, width):
        return length * width
