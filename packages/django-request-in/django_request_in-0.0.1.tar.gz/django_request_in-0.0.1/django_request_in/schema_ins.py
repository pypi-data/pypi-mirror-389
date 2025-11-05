# coding: utf-8

from django_request_in import SourceEnum, Field, IntegerField, StringField, BooleanField, greater_than_zero


class BaseSchemaIn:
    def __init__(self, data: 'Request'):
        filed_keys = [k for k, v in self.__class__.__dict__.items()
                      if isinstance(v, Field)]
        fileds = [v for k, v in self.__class__.__dict__.items()
                  if isinstance(v, Field)]
        items = zip(filed_keys, fileds)
        print(filed_keys)
        for key, field in items:
            value = data.data.get(
                key) if field.source == SourceEnum.data else data.query_params.get(key)
            for validator in field.validators:
                validator(value)
            setattr(self, key, value)


class SchemaIn(BaseSchemaIn):
    """ 支持从request中解析数据，支持校验。"""
    x = IntegerField(source=SourceEnum.data, validators=[greater_than_zero])
    y = StringField(source=SourceEnum.query_params, allow_none=True)
    z = BooleanField(source=SourceEnum.query_params)