from typing import Optional
from marshmallow import Schema, ValidationError
from marshmallow.fields import (
    Nested,
    Field,
    Boolean,
    Integer,
    Method
)
from marshmallow.decorators import (
    post_load,
    pre_dump
)
from app.entities import (
    DebugData,
    TestData,
    TestsData
)
from app.utils import clean_str
from app.service.exceptions import ServiceException


class StrField(Field):

    def _deserialize(self, value: Optional[str], *args, **kwargs):
        return clean_str(value)

    def _serialize(self, value: Optional[str], *args, **kwargs):
        return clean_str(value)


class DebugSchema(Schema):

    data_in = StrField(
        required=False,
        allow_none=True,
        load_only=True
    )
    code = StrField(required=True, load_only=True)
    result = StrField(dump_only=True)
    error = StrField(dump_only=True)

    @post_load
    def make_debug_data(self, data, **kwargs) -> DebugData:
        return DebugData(**data)


class TestSchema(Schema):

    data_in = StrField(load_only=True)
    data_out = StrField(required=True, load_only=True)
    result = StrField(dump_only=True)
    error = StrField(dump_only=True)
    ok = Boolean(dump_only=True)

    @post_load
    def make_test_data(self, data, **kwargs) -> TestData:
        return TestData(**data)


class TestsSchema(Schema):

    tests = Nested(TestSchema, many=True, required=True)
    checker = StrField(load_only=True, required=True)
    code = StrField(load_only=True, required=True)
    num = Integer(dump_only=True)
    num_ok = Integer(dump_only=True)
    ok = Boolean(dump_only=True)

    @post_load
    def make_tests_data(self, data, **kwargs) -> TestsData:
        return TestsData(**data)

    @pre_dump
    def calculate_properties(self, data: TestsData, **kwargs):
        data.num = len(data.tests)
        for test in data.tests:
            if test.ok:
                data.num_ok += 1
        data.ok = data.num == data.num_ok
        return data


class BadRequestSchema(Schema):

    error = Method('dump_error')
    details = Method('dump_details')

    def dump_error(self, obj):
        desc = getattr(obj, 'description', None)
        if isinstance(desc, str):
            return desc
        if hasattr(desc, 'message'):
            return desc.message
        return str(desc)

    def dump_details(self, obj):
        desc = getattr(obj, 'description', None)
        if hasattr(desc, 'details'):
            return desc.details
        return None


class ServiceExceptionSchema(Schema):

    error = Method('dump_error')
    details = Method('dump_details')

    def dump_error(self, obj):
        return obj.description.message

    def dump_details(self, obj):
        return obj.description.details



class ServiceExceptionSchema(Schema):

    error = Method('dump_error')
    details = Method('dump_details')

    def _get_description(self, obj):
        # description may be missing or be a simple string
        return getattr(obj, 'description', obj)

    def dump_error(self, obj):
        desc = self._get_description(obj)
        if isinstance(desc, str):
            return desc
        return getattr(desc, 'message', str(desc))

    def dump_details(self, obj):
        desc = self._get_description(obj)
        if isinstance(desc, str):
            return None
        return getattr(desc, 'details', None)
