# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""REALIFE extension contract tests: monthly operations summary."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import Intake, IntakeIssue, Issue, Project, ProjectMember, State


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(
        name="Summary Project", identifier="SUM", workspace=workspace, created_by=create_user
    )
    ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
    State.objects.create(
        name="Todo",
        color="#000000",
        group="unstarted",
        default=True,
        project=project,
        workspace=workspace,
        created_by=create_user,
    )
    State.objects.create(
        name="Done",
        color="#000000",
        group="completed",
        default=False,
        project=project,
        workspace=workspace,
        created_by=create_user,
    )
    return project


@pytest.mark.contract
@pytest.mark.django_db
class TestRealifeSummary:
    def test_monthly_counts(self, workspace, project, create_user):
        now = timezone.now()
        overdue_state = State.objects.get(project=project, group="unstarted")
        done_state = State.objects.get(project=project, group="completed")
        Issue.objects.create(
            name="Overdue",
            project=project,
            workspace=workspace,
            created_by=create_user,
            state=overdue_state,
            target_date=(now - timedelta(days=1)).date(),
        )
        Issue.objects.create(
            name="Done",
            project=project,
            workspace=workspace,
            created_by=create_user,
            state=done_state,
            completed_at=now,
        )
        intake = Intake.objects.create(name="Intake", project=project, workspace=workspace, is_default=True)
        pending = Issue.objects.create(
            name="Pending", project=project, workspace=workspace, created_by=create_user, state=overdue_state
        )
        IntakeIssue.objects.create(
            intake=intake, issue=pending, project=project, workspace=workspace, status=-2
        )

        client = APIClient()
        client.force_authenticate(user=create_user)
        response = client.get(f"/api/workspaces/{workspace.slug}/realife-summary/?month={now:%Y-%m}")

        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["month"] == f"{now:%Y-%m}"
        row = response.data["projects"][0]
        assert row["created"] == 3
        assert row["completed"] == 1
        assert row["pending_approval"] == 1
        assert row["overdue"] == 1
        assert response.data["totals"]["overdue"] == 1

    def test_bad_month_rejected(self, workspace, project, create_user):
        client = APIClient()
        client.force_authenticate(user=create_user)
        response = client.get(f"/api/workspaces/{workspace.slug}/realife-summary/?month=2026-13")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
