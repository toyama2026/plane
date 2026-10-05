# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# REALIFE extension: serializers for project custom fields.

from datetime import datetime

from rest_framework import serializers

from .base import BaseSerializer
from plane.db.models import CustomField, IssueCustomFieldValue
from plane.db.models.custom_field import CustomFieldType


def validate_field_value(custom_field, value):
    field_type = custom_field.field_type
    if value is None:
        if custom_field.required:
            raise serializers.ValidationError(f"{custom_field.name} is required")
        return value
    if field_type == CustomFieldType.TEXT.value:
        if not isinstance(value, str):
            raise serializers.ValidationError(f"{custom_field.name} must be text")
        if len(value) > 2000:
            raise serializers.ValidationError(f"{custom_field.name} must be 2000 characters or less")
    elif field_type == CustomFieldType.NUMBER.value:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise serializers.ValidationError(f"{custom_field.name} must be a number")
    elif field_type == CustomFieldType.DATE.value:
        if not isinstance(value, str):
            raise serializers.ValidationError(f"{custom_field.name} must be a date (YYYY-MM-DD)")
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise serializers.ValidationError(f"{custom_field.name} must be a date (YYYY-MM-DD)")
    elif field_type == CustomFieldType.SELECT.value:
        options = (custom_field.options or {}).get("options", [])
        if value not in options:
            raise serializers.ValidationError(f"{custom_field.name} must be one of {options}")
    return value


class CustomFieldSerializer(BaseSerializer):
    class Meta:
        model = CustomField
        fields = "__all__"
        read_only_fields = ["workspace", "project"]

    def validate(self, data):
        field_type = data.get("field_type", getattr(self.instance, "field_type", CustomFieldType.TEXT.value))
        if field_type == CustomFieldType.SELECT.value:
            options = data.get("options", getattr(self.instance, "options", {}) or {})
            if not (options or {}).get("options"):
                raise serializers.ValidationError("Select fields require options.options list")
        return data


class IssueCustomFieldValueSerializer(BaseSerializer):
    field_name = serializers.CharField(source="custom_field.name", read_only=True)
    field_type = serializers.CharField(source="custom_field.field_type", read_only=True)

    class Meta:
        model = IssueCustomFieldValue
        fields = "__all__"
        read_only_fields = ["workspace", "project", "issue", "custom_field"]
