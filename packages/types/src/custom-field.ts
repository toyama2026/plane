/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// REALIFE extension: project custom fields for work items.

export type TCustomFieldType = "text" | "number" | "date" | "select";

export interface ICustomField {
  id: string;
  name: string;
  description?: string;
  field_type: TCustomFieldType;
  options?: { options?: string[] };
  required: boolean;
  sort_order: number;
  is_active: boolean;
  project: string;
  workspace: string;
}

export interface IIssueCustomFieldValue {
  id: string;
  issue: string;
  custom_field: string;
  field_name: string;
  field_type: TCustomFieldType;
  value: string | number | null;
  project: string;
  workspace: string;
}
