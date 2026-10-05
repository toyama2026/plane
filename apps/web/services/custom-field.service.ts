/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

/* eslint-disable no-useless-catch */

// REALIFE extension: project custom fields for work items.

// types
import { API_BASE_URL } from "@plane/constants";
import type { ICustomField, IIssueCustomFieldValue } from "@plane/types";
// services
import { APIService } from "@/services/api.service";

export class CustomFieldService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async fetchProjectCustomFields(workspaceSlug: string, projectId: string): Promise<ICustomField[]> {
    try {
      const { data } = await this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/custom-fields/`);
      return data ?? [];
    } catch (error) {
      throw error;
    }
  }

  async createProjectCustomField(
    workspaceSlug: string,
    projectId: string,
    payload: Partial<ICustomField>
  ): Promise<ICustomField> {
    try {
      const { data } = await this.post(
        `/api/workspaces/${workspaceSlug}/projects/${projectId}/custom-fields/`,
        payload
      );
      return data;
    } catch (error) {
      throw error;
    }
  }

  async updateProjectCustomField(
    workspaceSlug: string,
    projectId: string,
    fieldId: string,
    payload: Partial<ICustomField>
  ): Promise<ICustomField> {
    try {
      const { data } = await this.patch(
        `/api/workspaces/${workspaceSlug}/projects/${projectId}/custom-fields/${fieldId}/`,
        payload
      );
      return data;
    } catch (error) {
      throw error;
    }
  }

  async deleteProjectCustomField(workspaceSlug: string, projectId: string, fieldId: string): Promise<void> {
    try {
      await this.delete(`/api/workspaces/${workspaceSlug}/projects/${projectId}/custom-fields/${fieldId}/`);
    } catch (error) {
      throw error;
    }
  }

  async fetchIssueCustomValues(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<IIssueCustomFieldValue[]> {
    try {
      const { data } = await this.get(
        `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/custom-values/`
      );
      return data ?? [];
    } catch (error) {
      throw error;
    }
  }

  async updateIssueCustomValues(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    values: Record<string, string | number | null>
  ): Promise<IIssueCustomFieldValue[]> {
    try {
      const { data } = await this.put(
        `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/custom-values/`,
        { values }
      );
      return data ?? [];
    } catch (error) {
      throw error;
    }
  }
}

const customFieldService = new CustomFieldService();

export default customFieldService;
