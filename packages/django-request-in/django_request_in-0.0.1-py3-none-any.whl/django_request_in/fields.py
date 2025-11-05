# coding: utf-8

from enum import Enum
from typing import List, Callable


class SourceEnum(Enum):
    # For CustoCustomizedAPIView which is modified from Django's APIView by the backend team of xmov.ai
    data = "data"
    query_params = "query_params"
    xmov_data = "xmov_data"  # alias of data
    xmov_query_params = "xmov_query_params"  # alias of query_params
    xmov_method = "xmov_method"
    xmov_GET = "xmov_GET"
    xmov_POST = "xmov_POST"
    xmov_COOKIES = "xmov_COOKIES"
    xmov_FILES = "xmov_FILES"
    xmov_META = "xmov_META"

    # For plain django request
    method = "method"
    GET = "GET"
    POST = "POST"
    COOKIES = "COOKIES"
    FILES = "FILES"
    META = "META"


class Field:
    data_type = None

    def __init__(self, source: SourceEnum, validators: List[Callable] = [], allow_none: bool = False, post_callable: Callable = None):
        """ 初始化Field对象。 
            ⚠️注意：
                这里如果提供了post_callable，则会在检查data_type之后调用post_callable但会造成data_type不准确。
                例如，data_type是str, 但post_callable处理之后是其他类型。所以data_type应该是一个通用的类型，
                比如object。所以AnyField是更好的选择。
        Args:
            source: 数据来源。
            validators: 校验器列表。
            allow_none: 是否允许None值。
            post_callable: 后处理函数。
        """
        self.source = source
        self.validators = validators
        self.allow_none = allow_none
        self.post_callable = post_callable

    def __get__(self, instance, owner):
        return self.value

    def __set__(self, instance, value):
        """ 设置Field的值。
            1. 检查value是否为None
            2. 检查value是否为正确的类型
            3. 如果post_callable提供，则调用它
            4. 设置value到instance
        Args:
            instance: 类实例。
            value: 要设置的值。
        """
        if value is None:
            if not self.allow_none:
                raise ValueError(f"value must not be None")
        elif not isinstance(value, self.data_type):
            raise ValueError(
                f"value must be {self.data_type}, but got {type(value)}")
        if self.post_callable and isinstance(self.post_callable, Callable):
            value = self.post_callable(value)
        elif self.post_callable and not isinstance(self.post_callable, Callable):
            raise ValueError(f"post_callable must be a callable, but got {type(self.post_callable)}")
        else:
            value = value
        self.value = value


class IntegerField(Field):
    data_type = int


class StringField(Field):
    data_type = str


class BooleanField(Field):
    data_type = bool


class DictField(Field):
    data_type = dict


class AnyField(Field):
    data_type = object
