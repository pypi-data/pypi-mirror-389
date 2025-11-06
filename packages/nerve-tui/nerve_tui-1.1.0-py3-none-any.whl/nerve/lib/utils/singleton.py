from typing import (TypeVar, Type, cast)

T: TypeVar = TypeVar("T", bound="Singleton")

class Singleton:
    _instances: dict[type, "Singleton"] = {}

    def __new__(cls: Type[T], *args: object, **kwargs: object) -> T:
        if cls not in cls._instances:
            cls._instances[cls] = cast(T, super().__new__(cls))

        return cast(T, cls._instances[cls])
