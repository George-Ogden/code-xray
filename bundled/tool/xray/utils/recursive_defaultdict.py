from collections import defaultdict
from typing import Optional


class recursive_defaultdict(defaultdict):
    """defaultdict(defaultdict) with utilities."""

    def __init__(self, default: Optional[defaultdict] = None):
        if default is None:
            default = recursive_defaultdict
        assert default is recursive_defaultdict
        super().__init__(default)

    def to_non_empty_dict(self) -> dict:
        """Get rid of attributes that are empty (recursively)."""
        non_empty_dict = {}
        for k, v in self.items():
            non_empty_v = v
            if isinstance(v, recursive_defaultdict):
                non_empty_v = v.to_non_empty_dict()
            if non_empty_v != {}:
                non_empty_dict[k] = non_empty_v
        return non_empty_dict
