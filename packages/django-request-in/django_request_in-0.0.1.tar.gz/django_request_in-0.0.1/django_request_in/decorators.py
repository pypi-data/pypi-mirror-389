# coding: utf-8

from typing import Dict, Callable
from django_request_in.fields import SourceEnum, Field


def request_decorator(**fileld_kwargs: Field) -> Callable:
    """ Decorator for request_in.
    Args:
        **fileld_kwargs: Keyword arguments for the fields. The key is the field name, and the value is the Field-like object.
    Returns:
        A decorator function that wraps the view function.
    """
    def wrapper(view_func):
        def inner_wrapper(self, request, *args, **kwargs):
            params = {}
            for field_name, field in fileld_kwargs.items():
                # For CompatiableRequest
                if field.source == SourceEnum.data or field.source == SourceEnum.xmov_data:
                    value = request.data.get(field_name)
                elif field.source == SourceEnum.query_params or field.source == SourceEnum.xmov_query_params:
                    value = request.query_params.get(field_name)
                elif field.source == SourceEnum.xmov_method:
                    value = request._request.method
                elif field.source == SourceEnum.xmov_GET:
                    value = request._request.GET.get(field_name)
                elif field.source == SourceEnum.xmov_POST:
                    value = request._request.POST.get(field_name)
                elif field.source == SourceEnum.xmov_COOKIES:
                    value = request._request.COOKIES.get(field_name)
                elif field.source == SourceEnum.xmov_FILES:
                    value = request._request.FILES.get(field_name)
                elif field.source == SourceEnum.xmov_META:
                    value = request._request.META.get(field_name)

                # For plain django request
                elif field.source == SourceEnum.method:
                    value = request.method
                elif field.source == SourceEnum.GET:
                    value = request.GET.get(field_name)
                elif field.source == SourceEnum.POST:
                    value = request.POST.get(field_name)
                elif field.source == SourceEnum.COOKIES:
                    value = request.COOKIES.get(field_name)
                elif field.source == SourceEnum.FILES:
                    value = request.FILES.get(field_name)
                elif field.source == SourceEnum.META:
                    value = request.META.get(field_name)
                else:
                    raise ValueError(f"invalid source: {field.source}")

                # 校验器校验
                for validator in field.validators:
                    validator(value)

                params[field_name] = value
            return view_func(self, request, **params)
        return inner_wrapper
    return wrapper
