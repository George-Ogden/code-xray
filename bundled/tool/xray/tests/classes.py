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


def external(x):
    return x
