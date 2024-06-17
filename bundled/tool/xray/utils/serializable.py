class Serializable:
    """Define an object that can be converted to JSON."""

    def to_json(self) -> dict[str, any]:
        return {key: self.serialize(value) for key, value in vars(self).items()}

    @classmethod
    def serialize(cls, object: any) -> any:
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
