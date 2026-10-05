# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# REALIFE extension: monthly operations summary per project.
# (created / completed / pending approval / overdue)

from datetime import datetime

from django.utils import timezone

# Third party imports
from rest_framework.response import Response
from rest_framework import status

# Module imports
from ..base import BaseAPIView
from plane.app.permissions import allow_permission, ROLE
from plane.db.models import IntakeIssue, Issue, Project

OPEN_GROUPS = ["backlog", "unstarted", "started"]


class RealifeSummaryEndpoint(BaseAPIView):
    @allow_permission([ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        month_param = request.GET.get("month")
        try:
            if month_param:
                target = datetime.strptime(month_param, "%Y-%m")
                year, month = target.year, target.month
            else:
                now = timezone.now()
                year, month = now.year, now.month
        except ValueError:
            return Response({"error": "month must be YYYY-MM"}, status=status.HTTP_400_BAD_REQUEST)

        project_ids = [pid for pid in request.GET.get("project_ids", "").split(",") if pid]
        projects = Project.objects.filter(workspace__slug=slug)
        if project_ids:
            projects = projects.filter(pk__in=project_ids)

        today = timezone.now().date()
        rows = []
        for project in projects:
            issues = Issue.issue_objects.filter(project=project)
            created = issues.filter(created_at__year=year, created_at__month=month).count()
            completed = issues.filter(completed_at__year=year, completed_at__month=month).count()
            pending_approval = IntakeIssue.objects.filter(project=project, status=-2).count()
            overdue = issues.filter(
                state__group__in=OPEN_GROUPS,
                target_date__isnull=False,
                target_date__lt=today,
            ).count()
            rows.append(
                {
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "project_identifier": project.identifier,
                    "created": created,
                    "completed": completed,
                    "pending_approval": pending_approval,
                    "overdue": overdue,
                }
            )

        totals = {
            key: sum(row[key] for row in rows) for key in ("created", "completed", "pending_approval", "overdue")
        }
        return Response(
            {"month": f"{year:04d}-{month:02d}", "projects": rows, "totals": totals},
            status=status.HTTP_200_OK,
        )
