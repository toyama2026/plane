# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Unit tests for REALIFE custom field value validation."""

from types import SimpleNamespace

import pytest
from rest_framework import serializers

from plane.app.serializers.custom_field import CustomFieldSerializer, validate_field_value


def _field(field_type, **kwargs):
    defaults = {"name": "Test", "field_type": field_type, "required": False, "options": {}}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


@pytest.mark.unit
class TestValidateFieldValue:
    def test_text_ok(self):
        assert validate_field_value(_field("text"), "hello") == "hello"

    def test_text_rejects_non_string(self):
        with pytest.raises(serializers.ValidationError):
            validate_field_value(_field("text"), 123)

    def test_number_ok(self):
        assert validate_field_value(_field("number"), 1500000) == 1500000

    def test_number_rejects_bool_and_string(self):
        with pytest.raises(serializers.ValidationError):
            validate_field_value(_field("number"), True)
        with pytest.raises(serializers.ValidationError):
            validate_field_value(_field("number"), "100")

    def test_date_ok(self):
        assert validate_field_value(_field("date"), "2026-10-31") == "2026-10-31"

    def test_date_rejects_bad_format(self):
        with pytest.raises(serializers.ValidationError):
            validate_field_value(_field("date"), "31/10/2026")

    def test_select_ok(self):
        field = _field("select", options={"options": ["A社", "B社"]})
        assert validate_field_value(field, "A社") == "A社"

    def test_select_rejects_unknown_option(self):
        field = _field("select", options={"options": ["A社", "B社"]})
        with pytest.raises(serializers.ValidationError):
            validate_field_value(field, "C社")

    def test_required_rejects_none(self):
        with pytest.raises(serializers.ValidationError):
            validate_field_value(_field("text", required=True), None)

    def test_optional_accepts_none(self):
        assert validate_field_value(_field("text"), None) is None


@pytest.mark.unit
class TestCustomFieldSerializer:
    def test_select_requires_options(self):
        serializer = CustomFieldSerializer(data={"name": "顧客", "field_type": "select"})
        assert not serializer.is_valid()
