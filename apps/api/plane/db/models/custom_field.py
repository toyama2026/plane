# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# REALIFE extension: project-level custom fields for work items.
# (text / number / date / select). Values are stored per issue.

from enum import Enum

from django.db import models
from django.db.models import Q

from .project import ProjectBaseModel


class CustomFieldType(Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"

    @classmethod
    def choices(cls):
        return [(member.value, member.name.title()) for member in cls]


class CustomField(ProjectBaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    field_type = models.CharField(max_length=20, choices=CustomFieldType.choices(), default=CustomFieldType.TEXT.value)
    # For SELECT: {"options": ["A", "B", "C"]}
    options = models.JSONField(default=dict, blank=True)
    required = models.BooleanField(default=False)
    sort_order = models.FloatField(default=65535)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                condition=Q(deleted_at__isnull=True),
                name="unique_custom_field_project_name_when_not_deleted",
            ),
        ]
        verbose_name = "Custom Field"
        verbose_name_plural = "Custom Fields"
        db_table = "custom_fields"
        ordering = ("sort_order", "-created_at",)

    def save(self, *args, **kwargs):
        if self._state.adding:
            last = CustomField.objects.filter(project=self.project).aggregate(largest=models.Max("sort_order"))
            if last["largest"] is not None:
                self.sort_order = last["largest"] + 10000
        super(CustomField, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.project_id} {self.name} ({self.field_type})"


class IssueCustomFieldValue(ProjectBaseModel):
    issue = models.ForeignKey(
        "db.Issue",
        on_delete=models.CASCADE,
        related_name="custom_field_values",
    )
    custom_field = models.ForeignKey(
        CustomField,
        on_delete=models.CASCADE,
        related_name="issue_values",
    )
    value = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "custom_field"],
                condition=Q(deleted_at__isnull=True),
                name="unique_issue_custom_field_when_not_deleted",
            ),
        ]
        verbose_name = "Issue Custom Field Value"
        verbose_name_plural = "Issue Custom Field Values"
        db_table = "issue_custom_field_values"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.issue_id} {self.custom_field_id}"
