# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# REALIFE extension: project custom fields and per-issue values.

# Third party imports
from rest_framework.response import Response
from rest_framework import status

# Module imports
from ..base import BaseViewSet, BaseAPIView
from plane.app.permissions import ProjectEntityPermission, allow_permission, ROLE
from plane.db.models import Project, Issue, CustomField, IssueCustomFieldValue
from plane.app.serializers import (
    CustomFieldSerializer,
    IssueCustomFieldValueSerializer,
)
from plane.app.serializers.custom_field import validate_field_value
from plane.utils.cache import invalidate_cache


class CustomFieldViewSet(BaseViewSet):
    permission_classes = [ProjectEntityPermission]
    model = CustomField
    serializer_class = CustomFieldSerializer

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def list(self, request, slug, project_id):
        fields = CustomField.objects.filter(workspace__slug=slug, project_id=project_id)
        serializer = CustomFieldSerializer(fields, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    @invalidate_cache(path="/api/workspaces/:slug/projects/:project_id/custom-fields/", url_params=True, user=False)
    def create(self, request, slug, project_id):
        project = Project.objects.get(workspace__slug=slug, pk=project_id)
        serializer = CustomFieldSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(project=project, workspace=project.workspace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def retrieve(self, request, slug, project_id, field_id):
        field = CustomField.objects.get(pk=field_id, workspace__slug=slug, project_id=project_id)
        serializer = CustomFieldSerializer(field)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    @invalidate_cache(path="/api/workspaces/:slug/projects/:project_id/custom-fields/", url_params=True, user=False)
    def partial_update(self, request, slug, project_id, field_id):
        field = CustomField.objects.get(pk=field_id, workspace__slug=slug, project_id=project_id)
        serializer = CustomFieldSerializer(field, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN])
    @invalidate_cache(path="/api/workspaces/:slug/projects/:project_id/custom-fields/", url_params=True, user=False)
    def destroy(self, request, slug, project_id, field_id):
        field = CustomField.objects.get(pk=field_id, workspace__slug=slug, project_id=project_id)
        field.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IssueCustomFieldValueEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def get(self, request, slug, project_id, issue_id):
        values = IssueCustomFieldValue.objects.filter(
            workspace__slug=slug,
            project_id=project_id,
            issue_id=issue_id,
        ).select_related("custom_field")
        serializer = IssueCustomFieldValueSerializer(values, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission([ROLE.ADMIN, ROLE.MEMBER])
    def put(self, request, slug, project_id, issue_id):
        # Body: {"values": {"<field_uuid>": value, ...}}
        issue = Issue.objects.get(pk=issue_id, workspace__slug=slug, project_id=project_id)
        fields = {
            str(field.id): field
            for field in CustomField.objects.filter(workspace__slug=slug, project_id=project_id, is_active=True)
        }
        incoming = request.data.get("values", {})
        if not isinstance(incoming, dict):
            return Response({"error": "values must be an object"}, status=status.HTTP_400_BAD_REQUEST)

        unknown = [key for key in incoming if key not in fields]
        if unknown:
            return Response(
                {"error": f"Unknown custom fields: {unknown}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validated = {key: validate_field_value(fields[key], value) for key, value in incoming.items()}
        except Exception as exc:
            detail = exc.detail[0] if hasattr(exc, "detail") else exc
            return Response({"error": str(detail)}, status=status.HTTP_400_BAD_REQUEST)

        existing = {
            str(item.custom_field_id): item
            for item in IssueCustomFieldValue.objects.filter(issue=issue, custom_field_id__in=list(fields.keys()))
        }
        to_create, to_update = [], []
        for key, value in validated.items():
            if key in existing:
                record = existing[key]
                record.value = value
                to_update.append(record)
            else:
                to_create.append(
                    IssueCustomFieldValue(
                        issue=issue,
                        custom_field=fields[key],
                        project_id=project_id,
                        workspace_id=issue.workspace_id,
                        value=value,
                        created_by=request.user,
                        updated_by=request.user,
                    )
                )
        if to_create:
            IssueCustomFieldValue.objects.bulk_create(to_create)
        if to_update:
            IssueCustomFieldValue.objects.bulk_update(to_update, ["value", "updated_by", "updated_at"])

        values = IssueCustomFieldValue.objects.filter(issue=issue).select_related("custom_field")
        serializer = IssueCustomFieldValueSerializer(values, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
