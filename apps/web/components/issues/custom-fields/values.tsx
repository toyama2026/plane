/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// REALIFE extension: display and edit per-issue custom field values.

import { useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
// plane package imports
import type { ICustomField, IIssueCustomFieldValue } from "@plane/types";
import { Loader } from "@plane/blocks/skeleton";
// plane web services
import customFieldService from "@/services/custom-field.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  disabled?: boolean;
};

const toInputValue = (value: IIssueCustomFieldValue["value"]): string =>
  value === null || value === undefined ? "" : String(value);

export const IssueCustomFieldValues = observer(function IssueCustomFieldValues(props: Props) {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const [savingId, setSavingId] = useState<string | null>(null);

  const { data: fields } = useSWR<ICustomField[]>(
    workspaceSlug && projectId ? ["customFields", workspaceSlug, projectId] : null,
    workspaceSlug && projectId ? () => customFieldService.fetchProjectCustomFields(workspaceSlug, projectId) : null
  );
  const { data: values, mutate } = useSWR<IIssueCustomFieldValue[]>(
    workspaceSlug && projectId && issueId ? ["customValues", workspaceSlug, projectId, issueId] : null,
    workspaceSlug && projectId && issueId
      ? () => customFieldService.fetchIssueCustomValues(workspaceSlug, projectId, issueId)
      : null
  );

  const activeFields = (fields ?? []).filter((field) => field.is_active);
  if (activeFields.length === 0) return <></>;

  const valueByFieldId = new Map((values ?? []).map((item) => [item.custom_field, item.value]));

  const save = async (field: ICustomField, raw: string) => {
    let parsed: string | number | null = raw === "" ? null : raw;
    if (field.field_type === "number" && raw !== "") {
      const num = Number(raw);
      if (Number.isNaN(num)) return;
      parsed = num;
    }
    setSavingId(field.id);
    try {
      const updated = await customFieldService.updateIssueCustomValues(workspaceSlug, projectId, issueId, {
        [field.id]: parsed,
      });
      await mutate(updated, false);
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className={`space-y-3 ${disabled ? "opacity-60" : ""}`}>
      {activeFields.map((field) => {
        const current = valueByFieldId.get(field.id) ?? null;
        return (
          <div key={field.id} className="flex items-start gap-2">
            <div className="flex h-7.5 w-30 shrink-0 items-center text-body-xs-regular text-tertiary">
              <span className="truncate">{field.name}</span>
            </div>
            <div className="flex grow items-center gap-1">
              {field.field_type === "select" ? (
                <select
                  value={toInputValue(current)}
                  disabled={disabled || savingId === field.id}
                  onChange={(e) => save(field, e.target.value)}
                  className="h-7.5 w-full grow rounded bg-transparent text-body-xs-medium"
                  aria-label={field.name}
                >
                  <option value="">—</option>
                  {(field.options?.options ?? []).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : "text"}
                  defaultValue={toInputValue(current)}
                  key={`${field.id}-${toInputValue(current)}`}
                  disabled={disabled || savingId === field.id}
                  onBlur={(e) => {
                    if (e.target.value !== toInputValue(current)) save(field, e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                  }}
                  placeholder="—"
                  className="h-7.5 w-full grow rounded bg-transparent text-body-xs-medium"
                  aria-label={field.name}
                />
              )}
            </div>
          </div>
        );
      })}
      {!values && <Loader.Item height="40px" width="100%" />}
    </div>
  );
});
