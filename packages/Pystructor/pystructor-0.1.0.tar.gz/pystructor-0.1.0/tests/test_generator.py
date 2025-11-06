import pytest

from pydantic import Field
from pydantic import ValidationError

from pystructor import generate_crud_schemas


def test_create_schema_excludes_id(FooModel):
    CreateSchema, _, _ = generate_crud_schemas(FooModel)
    assert "id" not in CreateSchema.model_fields


def test_read_schema_excludes_password(FooModel):
    _, ReadSchema, _ = generate_crud_schemas(FooModel)
    assert "password" not in ReadSchema.model_fields
    # поля name и id есть
    assert "name" in ReadSchema.model_fields
    assert "id" in ReadSchema.model_fields


def test_update_schema_optional_fields(FooModel):
    _, _, UpdateSchema = generate_crud_schemas(FooModel)
    # все поля обязательные стали optional
    assert UpdateSchema.model_fields["name"].is_required() is False
    assert UpdateSchema.model_fields["password"].is_required() is False


def test_schemas_descriptions(FooModel):
    crud_schemas = generate_crud_schemas(FooModel)
    for schema in crud_schemas:
        assert schema.model_fields["name"].description == "Name"

        if schema.__name__ != "FooRead":
            # password есть только в create и update
            assert schema.model_fields["password"].description == "Password"


def test_include_additional_field_to_read(FooModel):
    def compute():
        return 10

    _, ReadSchema, _ = generate_crud_schemas(
        FooModel,
        include_to_read={
            "computed": (int, Field(default_factory=compute))
        }
    )
    # дополнительное поле есть и default работает
    inst = ReadSchema(name="x", id=1)
    assert inst.computed == 10


def test_constraints(FooModel):
    _, ReadSchema, _ = generate_crud_schemas(
        FooModel,
    )

    assert ReadSchema.model_fields["name"].max_length == 20


def test_create_validation(FooModel):
    CreateSchema, _, _ = generate_crud_schemas(FooModel)
    # name обязателен
    with pytest.raises(ValidationError):
        CreateSchema()
