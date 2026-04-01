import pytest

from mofaflex._core.api.utils import DynamicAPIMixin


@pytest.fixture
def Foo():
    class Foo(DynamicAPIMixin):
        def __init__(self):
            super().__init__()
            self._prop = 42

        def not_api_method(self):
            pass

        @property
        def not_api_property(self):
            pass

        @DynamicAPIMixin._api
        def api_method(self):
            pass

        @DynamicAPIMixin._api
        @property
        def api_property(self):
            return self._prop

        @api_property.setter
        def api_property(self, val):
            self._prop = val

        @api_property.deleter
        def api_property(self):
            self._prop = None

    return Foo


@pytest.fixture
def Bar(Foo):
    class Bar(Foo):
        def not_api_method_bar(self):
            pass

        @property
        def not_api_property_bar(self):
            pass

        @Foo._api
        def api_method_bar(self):
            pass

        @Foo._api
        @property
        def api_property_bar(self):
            pass

    return Bar


def test_class(Foo):
    assert "not_api_method" not in Foo.api()
    assert "not_api_property" not in Foo.api()
    assert "api_method" in Foo.api()
    assert "api_property" in Foo.api()

    assert "not_api_method" not in Foo.api_methods()
    assert "not_api_property" not in Foo.api_methods()
    assert "api_method" in Foo.api_methods()
    assert "api_property" not in Foo.api_methods()

    assert "not_api_method" not in Foo.api_properties()
    assert "not_api_property" not in Foo.api_properties()
    assert "api_method" not in Foo.api_properties()
    assert "api_property" in Foo.api_properties()


def test_subclass(Foo, Bar):

    for api in Foo.api():
        assert api in Bar.api()

    assert "not_api_method_bar" not in Bar.api()
    assert "not_api_property_bar" not in Bar.api()
    assert "api_method_bar" in Bar.api()
    assert "api_property_bar" in Bar.api()

    assert "not_api_method_bar" not in Bar.api_methods()
    assert "not_api_property_bar" not in Bar.api_methods()
    assert "api_method_bar" in Bar.api_methods()
    assert "api_property_bar" not in Bar.api_methods()

    assert "not_api_method_bar" not in Bar.api_properties()
    assert "not_api_property_bar" not in Bar.api_properties()
    assert "api_method_bar" not in Bar.api_properties()
    assert "api_property_bar" in Bar.api_properties()

    assert "not_api_method_bar" not in Foo.api()
    assert "not_api_property_bar" not in Foo.api()
    assert "api_method_bar" not in Foo.api()
    assert "api_property_bar" not in Foo.api()


def test_instance(Foo):
    obj = Foo()

    assert "not_api_method" not in obj.api()
    assert "not_api_property" not in obj.api()
    assert "api_method" in obj.api()
    assert "api_property" in obj.api()

    assert "not_api_method" not in obj.api_methods()
    assert "not_api_property" not in obj.api_methods()
    assert "api_method" in obj.api_methods()
    assert "api_property" not in obj.api_methods()

    assert "not_api_method" not in obj.api_properties()
    assert "not_api_property" not in obj.api_properties()
    assert "api_method" not in obj.api_properties()
    assert "api_property" in obj.api_properties()

    obj.baz = (lambda self: None).__get__(obj)
    obj._api("baz")
    assert "baz" in obj.api()
    assert "baz" in obj.api_methods()
    assert "baz" not in Foo.api()

    obj._api(obj.not_api_method)
    assert "not_api_method" in obj.api()
    assert "not_api_method" in obj.api_methods()
    assert "not_api_method" not in Foo.api()

    assert obj.api_property == 42

    obj.api_property = 1337
    assert obj.api_property == 1337

    del obj.api_property
    assert obj.api_property is None


def test_subclass_instance(Foo, Bar):
    obj = Bar()

    assert "not_api_method_bar" not in obj.api()
    assert "not_api_property_bar" not in obj.api()
    assert "api_method_bar" in obj.api()
    assert "api_property_bar" in obj.api()

    assert "not_api_method_bar" not in obj.api_methods()
    assert "not_api_property_bar" not in obj.api_methods()
    assert "api_method_bar" in obj.api_methods()
    assert "api_property_bar" not in obj.api_methods()

    assert "not_api_method_bar" not in obj.api_properties()
    assert "not_api_property_bar" not in obj.api_properties()
    assert "api_method_bar" not in obj.api_properties()
    assert "api_property_bar" in obj.api_properties()

    obj.baz = (lambda self: None).__get__(obj)
    obj._api("baz")
    assert "baz" in obj.api()
    assert "baz" in obj.api_methods()
    assert "baz" not in Bar.api()

    obj._api(obj.not_api_method)
    assert "not_api_method" in obj.api()
    assert "not_api_method" in obj.api_methods()
    assert "not_api_method" not in Bar.api()
