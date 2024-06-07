from __future__ import annotations

import ast
import inspect
import itertools
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Generic, Set, Type, _generic_class_getitem


class Attribute: ...


@dataclass
class Variable(Attribute):
    name: str


@dataclass
class Constant(Attribute):
    value: Any


class renamable:
    """Decorator to make a class renamable."""

    def __new__(mcls, cls: Type[Renamable]) -> Type[Renamable]:
        if not hasattr(cls, "_renamable"):
            bases = cls.__bases__
            if bases == (object,):
                bases = ()
            cls = type(
                cls.__name__,
                (Renamable,) + bases,
                dict(cls.__dict__),
            )
        elif Generic in cls.__bases__:
            # This is only necessary if Generic is in __bases__ and before the renamable (the class_getitem takes precedence).
            cls.__class_getitem__ = Renamable.__class_getitem__.__get__(cls)
        cls = mcls._rename_attributes(cls)
        cls = mcls._add_property(cls)
        return cls

    @classmethod
    def _rename_attributes(mcls, cls: Type[Renamable]) -> Type[Renamable]:
        attributes_names = set(itertools.chain(vars(cls), inspect.get_annotations(cls)))
        cls._renamable_attributes = {name for name in attributes_names if not name.startswith("_")}
        return cls

    @classmethod
    def _add_property(mcls, cls: Type[Renamable]) -> Type[Renamable]:
        """Add a property that acts as an alias via the current name."""

        @property
        def base_property(derived_self):
            public_properties: Dict[str, property] = {}
            for name in cls._renamable_attributes:
                public_properties[name] = mcls._make_property(derived_self, name, settable=True)
            return type(cls.__name__, (), public_properties)()

        setattr(cls, cls.__name__, base_property)
        return cls

    @classmethod
    def _make_property(mcls, derived_self: Renamable, name: str, settable: bool = True) -> property:
        """Make a property to get attributes from the root."""

        def getter(self: object) -> Any:
            attribute = derived_self._lookup_attribute(name)
            match attribute:
                case Variable():
                    return getattr(derived_self, attribute.name)
                case Constant():
                    return attribute.value

        def setter(self: object, value: Any):
            attribute = derived_self._lookup_attribute(name)
            match attribute:
                case Variable():
                    return setattr(derived_self, attribute.name, value)
                case Constant():
                    raise AttributeError("Trying to set a constant value.")

        if settable:
            return property(getter, setter)
        else:
            return property(getter)


class Renamable:
    _renamable: bool = (
        True  # We check for the presence of this attribute so setting it to false has no effect.
    )
    _attributes_lookup: ClassVar[Dict[str, str]] = dict()
    _renamable_attributes: ClassVar[Set[str]] = set()

    def __class_getitem__(
        cls: Type[Renamable], attribute_renaming: Dict[str, Any]
    ) -> Type[Renamable]:
        """Return a new class with the renaming."""
        if Generic in cls.__bases__:
            cls_dict = dict(cls.__dict__)
            # In this case, attribute renaming is the argument passed to the generic.
            type_alias = _generic_class_getitem(cls, attribute_renaming)
            bases = tuple(base for base in cls.__bases__ if base != Generic)
            cls = type(type_alias.__name__ + f"[{attribute_renaming.__name__}]", bases, cls_dict)
            cls.__class_getitem__ = Renamable.__class_getitem__.__get__(cls)
            return cls

        # Add the renames to the class name.
        name_suffix = f'[{",".join(f"{k}={v}" for k,v in attribute_renaming.items())}]'
        # Copy class.
        cls = type(cls.__name__ + name_suffix, cls.__bases__, dict(cls.__dict__))
        cls._attributes_lookup = dict(cls._attributes_lookup)
        cls._renamable_attributes = set(cls._renamable_attributes)

        bases = tuple(
            type(base.__name__, base.__bases__, dict(base.__dict__)) for base in cls.__bases__
        )

        for old_name, new_name in attribute_renaming.items():
            if old_name not in cls._renamable_attributes:
                raise ValueError(
                    f"`{old_name}` not allowed to be renamed in {cls.__name__} but trying to rename to `{new_name}`"
                )

            attribute = cls._parse_attribute(new_name)
            # Record that this has been updated.
            cls._attributes_lookup[old_name] = attribute
            # Disallow renaming in the future.
            cls._renamable_attributes.remove(old_name)

            match attribute:
                case Variable():
                    if hasattr(cls, old_name):
                        # Copy if there is an attribute (not an annotation).
                        setattr(cls, new_name, getattr(cls, old_name))
                        # Delete old name to avoid confusion.
                        delattr(cls, old_name)
                case Constant():
                    # Add a property with the same name for ease of use.
                    if not hasattr(cls, old_name):

                        def getter(self):
                            return attribute.value

                        setattr(cls, old_name, property(getter))

            # Delete the current method from all bases.
            for base in bases:
                if hasattr(base, old_name):
                    delattr(base, old_name)

        # Recreate the class with the updated bases.
        cls = type(cls.__name__, bases, dict(cls.__dict__))

        return cls

    def _lookup_attribute(self, name: str) -> Attribute:
        """Return an attribute indicating either a constant or variable."""
        attribute = Variable(name)
        while isinstance(attribute, Variable) and attribute.name in self._attributes_lookup:
            attribute = self._attributes_lookup[attribute.name]
        return attribute

    @classmethod
    def _parse_attribute(cls, attribute: str) -> Attribute:
        """Check whether an attribute is a value or a name."""
        try:
            expression = ast.parse(attribute, mode="eval")
            match expression:
                # Expression is a string containing a string (string constant).
                case ast.Expression(body=ast.Constant()):
                    return Constant(expression.body.value)
        except (SyntaxError, TypeError, ValueError):
            if not isinstance(attribute, str):
                # Expression is not a string (constant).
                return Constant(attribute)
        # Expression is a string (variable name).
        return Variable(attribute)
