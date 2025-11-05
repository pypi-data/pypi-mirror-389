from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Annotated, Dict, List, Type, Union, get_origin

from loguru import logger
from pydantic import BaseModel, TypeAdapter

from exactpy.exceptions import NoFiltersSetException
from exactpy.models.base import ExactOnlineBaseModel
from exactpy.utils import create_partial_model

if TYPE_CHECKING:
    from exactpy.client import Client


class BaseController:
    _resource: str
    _query_args_model: Type[BaseModel] | None = None
    _mandatory_filter_options: List[str] = []
    _model: Type[BaseModel]
    _expand: List[str] = []

    def __init__(
        self,
        client: Client,
    ):
        self._client = client
        self._list_adapter = TypeAdapter(List[self._model])

    def _check_query_args(
        self, query_args: Dict[str, Union[str, int, float]] = {}
    ) -> dict:
        """Validates query args using a pydantic model, and returns a dict
        dumped by the pydantic validation model if successful.

        Args:
            query_args (Dict[str, Union[str, int, float]], optional):
                Dict of query arg key, value pairs. Defaults to {}

        Raises:
            ValidationError: Raised if query args don't pass pydantic model validation.

        Returns:
            dict: The query arg pydantic model dump.
        """
        if self._query_args_model is None:
            return {}

        # Dump query args to dict in (Exact Online) aliases
        query_args = self._query_args_model.model_validate(query_args).model_dump()
        query_args_by_alias = self._query_args_model.model_validate(
            query_args
        ).model_dump(by_alias=True)
        # We have to modify GUID args so that its value matches guid '<val>'
        # print(self._query_args_model.model_fields)
        for key, val in query_args.items():
            if self._is_guid(key, model=self._query_args_model):
                query_args_by_alias[
                    self._query_args_model.model_fields[key].serialization_alias
                ] = f"guid'{val}'"
        # print(query_args_by_alias)
        return query_args_by_alias

    def _check_filters(self, filters: Dict[str, Union[str, int, float]] = {}):
        """Checks whether (the right) filters have been set in case
        they are mandatory.

        Args:
            filters (Dict[str, Union[str, int, float]], optional):  Dict of filter key, value pairs. Defaults to {}

        Raises:
            NoFiltersSetException: Raised when no filters are set while there are mandatory filters.
        """
        filter_options = ", ".join(self._mandatory_filter_options)
        if len(self._mandatory_filter_options) > 0 and len(filters) == 0:
            raise NoFiltersSetException(
                f"This model requires a mandatory filter. Choices are '{filter_options}'"
            )
        elif (
            len(self._mandatory_filter_options) > 0
            and set(self._mandatory_filter_options).intersection(filters.keys()) == {}
        ):
            raise NoFiltersSetException(
                f"No valid mandatory filter set. Choices are '{filter_options}'"
            )

        # Convert filter names to Exact Online naming (Pascal case)
        parsed_filters = {
            self._model.model_fields[field].alias: value
            for field, value in filters.items()
            if field in self._model.model_fields
        }

        return parsed_filters

    def _is_guid(self, key: str, model: Type[BaseModel]):
        is_guid = False
        pk_type = typing.get_type_hints(model, include_extras=True)[key]
        if get_origin(pk_type) is Annotated:
            is_guid = pk_type.__metadata__[-1] == "guid"
        return is_guid

    def show(
        self,
        primary_key_value: Union[str, int],
        expand: List[str] = [],
    ) -> Type[ExactOnlineBaseModel]:
        """Retrieve a single instance of a model by primary key.

        Args:
            primary_key_value (Union[str, int]): value of primary key field.
            expand (List[str], optional): Attributes to expand (in Exact Online naming, so
                Pascal case). Defaults to [].

        Returns:
            Type[ExactOnlineBaseModel]: In instance of a subclass of ExactOnlineBaseModel.
        """

        if self._model._pk is None:
            raise ValueError("Model's primary key (_pk) property is not set.")

        # Set expand attributes if they aren't set
        if expand == []:
            expand = self._expand

        is_guid = self._is_guid(self._model._pk.default, self._model)

        # Retrieve single instance and convert to pydantic
        return self._model.model_validate(
            self._client.show(
                resource=self._resource,
                primary_key=self._model.model_fields[self._model._pk.default].alias,
                primary_key_value=primary_key_value,
                expand=expand,
                is_guid=is_guid,
            ).json()["d"]["results"][0],
            extra="ignore",
        )

    def all(
        self,
        query_args: Dict[str, str] = {},
        filters: Dict[str, Union[str, int, float]] = {},
        select: List[str] = [],
        expand: List[str] = [],
        max_pages: int = -1,
    ) -> List[Type[ExactOnlineBaseModel]]:
        """Retrieve a collection of model instances using given
        filters.

        Args:
            query_args (Dict[str, str]): A dictionary of
                query arg name and value key pairs to send to the endpoint. Defaults to {}.
            filters (Dict[str, Union[str, int, float]], optional):  Dict of filter key,
                value pairs. Defaults to {}
            select (List[str], optional): Attributes to select (in Exact Online naming,
                so Pascal case). Defaults to [].
            expand (List[str], optional): Attributes to expand (in Exact Online naming,
                so Pascal case). Defaults to [].
            max_pages (int, optional): Max number of pages to retrieve. Defaults to -1 (no limit).

        Returns:
            List[Type[ExactOnlineBaseModel]]: List of instances of a subclass of ExactOnlineBaseModel.
        """
        if max_pages == 0:
            return []

        # Check mandatory filters and query args
        parsed_filters = self._check_filters(filters=filters)
        query_arg_dump = self._check_query_args(query_args=query_args)

        # Set expand attributes if they aren't set
        if expand == []:
            expand = self._expand

        # Check if select cols are set. If so, we have to
        # generate a partial model with those fields.
        list_adapter = self._list_adapter
        if len(select) > 0:
            partial_model = create_partial_model(
                model=self._model,
                fields=select,
            )
            list_adapter = TypeAdapter(List[partial_model])

        # Parse select cols into Exact Online naming (Pascal case)
        parsed_select = [self._model.model_fields[field].alias for field in select]

        # Initial get request to get first page
        resp = self._client.get(
            resource=self._resource,
            query_args=query_arg_dump,
            filters=parsed_filters,
            select=parsed_select,
            expand=expand,
        ).json()

        # Convert to Pydantic
        results = list_adapter.validate_python(resp["d"]["results"])

        # print("***" * 100)
        # pprint(resp["d"]["results"][0])
        page_count = 0

        if self._client.verbose:
            logger.info(f"Fetched page {page_count + 1}")
        while (next_url := resp["d"].get("__next")) is not None:
            page_count += 1
            if max_pages != -1 and page_count + 1 > max_pages:
                break

            if self._client.verbose:
                logger.info(f"Fetching page {page_count + 1}")

            # Extract the skip token, in order to obtain the next page
            skip_token = self._client._get_skip_token(next_url)

            # Get page
            resp = self._client.get(
                resource=self._resource,
                query_args=query_arg_dump,
                filters=parsed_filters,
                select=parsed_select,
                expand=expand,
                skip_token=skip_token,
            ).json()

            # Convert to Pydantic
            temp_results = list_adapter.validate_python(
                resp["d"]["results"], extra="ignore"
            )
            results.extend(temp_results)

        if self._client.verbose:
            logger.info(f"Fetched a total of {len(results)} records.")

        # Or return a list
        return results
