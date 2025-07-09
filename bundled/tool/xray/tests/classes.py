class TestClass:
    @staticmethod
    def static(x):
        return x

    @classmethod
    def class_(cls, x):
        return x

    def instance(self, x):
        return x

    class InnerClass:
        def method(self, y):
            return y

    @classmethod
    def docstring(cls, arg: int) -> int:
        """Docstring for function."""
        return arg

    def single_line(self): ...

    @classmethod
    def multiline(
        cls,
        argument_with_super_duper_long_name_that_is_unnecessary_to_force_line_break,
    ):
        return

    @classmethod
    def multiline_docstring(
        cls,
        argument_with_super_duper_long_name_that_is_returned_to_force_line_break,
    ):
        """Multiline docstring
        to make it different."""
        return argument_with_super_duper_long_name_that_is_returned_to_force_line_break


def external(x):
    return x


@decorator
def multiline(
argument_with_super_duper_long_name_that_is_unnecessary_to_force_line_break,
):
    return
