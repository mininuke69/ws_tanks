from __future__ import annotations
from dataclasses import dataclass
from math import sqrt



@dataclass
class Player:
    nick: str | None = None
    hp: float = 0.0
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0

    shot_cooldown: float = 0.0

    kills: int = 0
    deaths: int = 0


class Rect:
    def __init__(self, x, y, width, height) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def collide(self, other_rect: Rect):
        # not not colliding = colliding
        return not (
            self.x > other_rect.x + other_rect.width or # left bound right of other right bound
            self.x + self.width < other_rect.x or # right bound left of other left bound
            self.y > other_rect.y + other_rect.height or # top lower than other bottom
            self.y + self.height < other_rect.y # bottom higher than other top
        )
    
    def __repr__(self) -> str:
        return "Rect({}, {}, {}, {})".format(self.x, self.y, self.width, self.height)


class Vector:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y


    def __repr__(self) -> str:
        return f'Vector({self.x}, {self.y})'
    

    def __mul__(self, o: int | float):
        return Vector(self.x * o, self.y * o)
    

    def __rmul__(self, o: int | float):
        return self.__mul__(o)

    @property
    def magnitude(self):
        return sqrt(self.x ** 2 + self.y ** 2)
    

    @property
    def normalized(self):
        if self.magnitude == 0:
            return Vector(0, 0)
        return Vector(
            x=self.x / self.magnitude,
            y=self.y / self.magnitude
        )
    
@dataclass
class GameObject:
    obj_type: str
    rect: Rect
    vel: Vector = Vector(0, 0)
    player: str | None = None
    hp: float = 0 # change in hp when touching player


@dataclass
class ExampleMaps:
    map1 = [
        Rect(0, 0, 200, 10),
        Rect(0, 0, 10, 200),
        Rect(0, 190, 200, 10),
        Rect(190, 0, 10, 200),
    ]

@dataclass
class Settings:
    player_size: int = 18
    player_speed: float = 20
    spawn_hp: float = 5
    shot_cooldown: float = 1.2
    bullet_size: float = 2.0
    bullet_speed: float = 40
    bullet_damage: float = -1.0 # this must be negative, unless you want healing bullets...
    physics_interval: float = 1/25

# testing
if __name__ == '__main__':
    v1 = Vector(4, 3)
    print(v1.magnitude)
    print(v1.normalized)
    