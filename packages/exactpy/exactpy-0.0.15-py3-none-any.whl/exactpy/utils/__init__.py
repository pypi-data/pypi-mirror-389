from typing import List, Type

from pydantic import create_model

from exactpy.models.base import ExactOnlineBaseModel


def create_partial_model(
    model: Type[ExactOnlineBaseModel], fields: List[str]
) -> Type[ExactOnlineBaseModel]:
    """
    Create a new ExactOnlineBaseModel subclass with only the specified fields.

    Args:
        model (Type[ExactOnlineBaseModel]): The original ExactOnlineBaseModel subclass.
        fields (List[str]): List of field names to include in the new model.

    Returns:
        A new ExactOnlineBaseModel subclass with only the specified fields.
    """
    model_fields = model.model_fields
    partial_fields = {
        field: (model_fields[field].annotation, model_fields[field].default)
        for field in fields
        if field in model_fields
    }

    partial_model = create_model(
        f"{model.__name__}__partial", __base__=model, **partial_fields
    )

    return partial_model
