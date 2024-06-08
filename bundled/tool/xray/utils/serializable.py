from typing import Any


class Serializable:
    def to_json(self) -> dict[str, Any]:
        return {key: self.serialize(value) for key, value in vars(self).items()}

    @classmethod
    def serialize(cls, object: Any) -> Any:
        try:
            return object.to_json()
        except AttributeError:
            ...
        if isinstance(object, dict):
            return {key: cls.serialize(value) for key, value in object.items()}
        try:
            return {key: cls.serialize(value) for key, value in vars(object).items()}
        except TypeError:
            return object
