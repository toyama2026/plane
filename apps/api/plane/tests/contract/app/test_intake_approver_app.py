# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
REALIFE extension contract tests: designated approver for intake issues.

Flow: member files an intake issue with ``approver_id`` (a manager).
The designated approver — even with plain MEMBER role — may accept or
reject it. Other members may not change the status.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from plane.celery import app as celery_app
from plane.db.models import (
    Intake,
    IntakeIssue,
    Issue,
    Project,
    ProjectMember,
    State,
    User,
    WorkspaceMember,
)


@pytest.fixture(autouse=True)
def celery_eager():
    original_always_eager = celery_app.conf.task_always_eager
    original_eager_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    yield
    celery_app.conf.task_always_eager = original_always_eager
    celery_app.conf.task_eager_propagates = original_eager_propagates


def _make_user(email):
    local_part = email.split("@")[0]
    user = User.objects.create(email=email, username=local_part, first_name=local_part)
    user.set_password("test-password")
    user.save()
    return user


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(
        name="Approval Project", identifier="AP", workspace=workspace, created_by=create_user, intake_view=True
    )
    ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
    State.objects.create(
        name="Triage",
        color="#000000",
        group="triage",
        default=False,
        project=project,
        workspace=workspace,
        created_by=create_user,
    )
    State.objects.create(
        name="Todo",
        color="#000000",
        group="unstarted",
        default=True,
        project=project,
        workspace=workspace,
        created_by=create_user,
    )
    return project


@pytest.fixture
def intake(db, workspace, project, create_user):
    return Intake.objects.create(name="Intake", project=project, workspace=workspace, is_default=True)


def _add_member(workspace, project, user, *, ws_role=15, project_role=15):
    WorkspaceMember.objects.create(workspace=workspace, member=user, role=ws_role, is_active=True)
    ProjectMember.objects.create(
        workspace=workspace, project=project, member=user, role=project_role, is_active=True
    )


@pytest.mark.contract
@pytest.mark.django_db
class TestIntakeApproverFlow:
    def _create_url(self, workspace, project):
        return f"/api/workspaces/{workspace.slug}/projects/{project.id}/intake-issues/"

    def test_create_with_non_member_approver_is_rejected(self, workspace, project, intake, create_user):
        outsider = _make_user("outsider@plane.so")
        client = APIClient()
        client.force_authenticate(user=create_user)
        response = client.post(
            self._create_url(workspace, project),
            {"issue": {"name": "Need approval"}, "approver_id": str(outsider.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data

    def test_approver_member_can_accept(self, workspace, project, intake, create_user):
        approver = _make_user("manager@plane.so")
        _add_member(workspace, project, approver, project_role=15)

        creator = APIClient()
        creator.force_authenticate(user=create_user)
        created = creator.post(
            self._create_url(workspace, project),
            {"issue": {"name": "Need approval"}, "approver_id": str(approver.id)},
            format="json",
        )
        assert created.status_code == status.HTTP_200_OK, created.data
        issue_id = created.data["issue"]["id"]
        assert str(IntakeIssue.objects.get(issue_id=issue_id).approver_id) == str(approver.id)

        client = APIClient()
        client.force_authenticate(user=approver)
        response = client.patch(
            f"{self._create_url(workspace, project)}{issue_id}/",
            {"status": 1},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        assert IntakeIssue.objects.get(issue_id=issue_id).status == 1
        # accepted issues leave triage for the default state
        assert Issue.objects.get(pk=issue_id).state.group != "triage"

    def test_plain_member_cannot_accept(self, workspace, project, intake, create_user):
        approver = _make_user("manager@plane.so")
        _add_member(workspace, project, approver, project_role=15)
        other = _make_user("other@plane.so")
        _add_member(workspace, project, other, project_role=15)

        creator = APIClient()
        creator.force_authenticate(user=create_user)
        created = creator.post(
            self._create_url(workspace, project),
            {"issue": {"name": "Need approval"}, "approver_id": str(approver.id)},
            format="json",
        )
        assert created.status_code == status.HTTP_200_OK, created.data
        issue_id = created.data["issue"]["id"]

        client = APIClient()
        client.force_authenticate(user=other)
        response = client.patch(
            f"{self._create_url(workspace, project)}{issue_id}/",
            {"status": 1},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN, response.data
        assert IntakeIssue.objects.get(issue_id=issue_id).status == -2
