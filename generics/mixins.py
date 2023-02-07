from enum import Enum
from typing import Any, Mapping, Type

from django.db.models import QuerySet
from rest_framework import mixins, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from generics.services import BaseService


class MethodActionType(str, Enum):
    GET = "read"
    POST = "create"
    PUT = "update"
    PATCH = "partial_update"
    DELETE = "delete"


class MultipleSerializersMixin:
    request: Request
    serializer_classes: Mapping[str, BaseSerializer]

    def get_serializer_class(self):
        try:
            action: MethodActionType = getattr(
                MethodActionType, self.request.method
            )
            return self.serializer_classes[action.value]
        except KeyError as error:
            raise Exception(
                "Key %s not found in serializer_classes mapping."
                % action.value
            ) from error
        except AttributeError:
            methods = map(lambda a: a.name, MethodActionType)
            assert self.request.method not in methods, (
                "Expected one of the following methods: %s. Got: %s"
                % (", ".join(methods), self.request.method),
            )


class ServiceMixin:
    service: Type[BaseService]

    def get_service(self, *args, **kwargs) -> BaseService:
        assert self.service is not None, (
            "'%s' should either include a `service` attribute, "
            "or override the `get_service()` method." % self.__class__.__name__
        )

        return self.service(*args, **kwargs)


class ServiceCreateModelMixin(ServiceMixin, mixins.CreateModelMixin):
    def create(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)  # type:ignore
        serializer.is_valid(raise_exception=True)
        data = self.execute_service(serializer)
        return Response(data, status=status.HTTP_201_CREATED)

    def execute_service(self, serializer: BaseSerializer):
        service = self.get_service()
        return service.execute(serializer)


class ServiceUpdateModelMixin(ServiceMixin, mixins.UpdateModelMixin):
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)  # type:ignore
        serializer.is_valid(raise_exception=True)
        service = self.get_service()
        data = service.execute(serializer, *args, **kwargs)
        return Response(data, status=status.HTTP_200_OK)


class ServiceURLKwargsMixin(ServiceMixin):
    def get(self, request: Request, *args, **kwargs):
        service = self.get_service()
        service.context.update({"request": request})
        service.execute(**kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceGetQuerySetMixin(ServiceMixin):
    def get_queryset(self) -> QuerySet:
        service = self.get_service()
        service.context.update({"request": self.request})  # type:ignore
        return service.get_queryset()


class ServiceListModelMixin(ServiceMixin):
    def list(self, request: Request, *args, **kwargs):
        service = self.get_service()
        service.context.update({"request": request})
        data = service.get_data()
        serializer = self.get_serializer(data, many=True)  # type:ignore
        return Response(serializer.data)
