import unittest

from django_request_in import IntegerField, StringField, BooleanField, SourceEnum, greater_than_zero, request_decorator, Request, SchemaIn


class TestDescriptor(unittest.TestCase):
    def setUp(self):
        self.request = Request(
            data={"x": 1, "y": 'xx', "z": False},
            query_params={"x": 1, "y": None, "z": True}
        )

    @request_decorator(
        x=IntegerField(source=SourceEnum.data, validators=[greater_than_zero]),
        y=StringField(source=SourceEnum.data, allow_none=True),
        z=BooleanField(source=SourceEnum.data)
    )
    def request_in(self, request, x=None, y=None, z=None):
        print(x)
        print(y)
        print(z)
        return dict(x=x, y=y, z=z)

    def test_request_decorator(self):
        print('===> test_request_decorator <===')
        request = Request(
            data={"x": 1, "y": 'xx', "z": False},
            query_params={"x": 1, "y": None, "z": True}
        )
        response = self.request_in(request)
        print('---->response', response)

    def test_descriptor(self):
        request = Request(
            data={"x": 1, "y": 'xx', "z": False},
            query_params={"x": 1, "y": None, "z": True}
        )
        p = SchemaIn(request)
        print(p.x)
        print(p.y)
        print(p.z)
        p.x = 4
        print(p.x)

    def test_xx(self):
        pass
