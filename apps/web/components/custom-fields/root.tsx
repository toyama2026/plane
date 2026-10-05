/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// REALIFE extension: manage project custom fields (admin settings).

import { useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
// plane imports
import { Icon } from "@makeplane/propel/components/icon";
import { IconButton } from "@makeplane/propel/components/icon-button";
import { DeleteOutline, EditOutline } from "@makeplane/propel/icons";
import type { ICustomField, TCustomFieldType } from "@plane/types";
import { Loader } from "@plane/blocks/skeleton";
// plane web services
import customFieldService from "@/services/custom-field.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
};

const FIELD_TYPE_LABELS: Record<TCustomFieldType, string> = {
  text: "テキスト",
  number: "数値",
  date: "日付",
  select: "選択肢",
};

export const CustomFieldManager = observer(function CustomFieldManager(props: Props) {
  const { workspaceSlug, projectId } = props;
  const [name, setName] = useState("");
  const [fieldType, setFieldType] = useState<TCustomFieldType>("text");
  const [optionsText, setOptionsText] = useState("");
  const [required, setRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const {
    data: fields,
    isLoading,
    mutate,
  } = useSWR<ICustomField[]>(["projectCustomFields", workspaceSlug, projectId], () =>
    customFieldService.fetchProjectCustomFields(workspaceSlug, projectId)
  );

  const resetForm = () => {
    setName("");
    setFieldType("text");
    setOptionsText("");
    setRequired(false);
    setError(null);
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      setError("名前を入力してください");
      return;
    }
    const options =
      fieldType === "select"
        ? {
            options: optionsText
              .split(/[,、\n]/)
              .map((s) => s.trim())
              .filter(Boolean),
          }
        : {};
    if (fieldType === "select" && (options.options ?? []).length === 0) {
      setError("選択肢をカンマ区切りで入力してください");
      return;
    }
    setBusy(true);
    try {
      await customFieldService.createProjectCustomField(workspaceSlug, projectId, {
        name: name.trim(),
        field_type: fieldType,
        options,
        required,
      });
      resetForm();
      await mutate();
    } catch {
      setError("作成に失敗しました");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async (fieldId: string) => {
    setBusy(true);
    try {
      await customFieldService.deleteProjectCustomField(workspaceSlug, projectId, fieldId);
      await mutate();
    } finally {
      setBusy(false);
    }
  };

  const handleToggleActive = async (field: ICustomField) => {
    setBusy(true);
    try {
      await customFieldService.updateProjectCustomField(workspaceSlug, projectId, field.id, {
        is_active: !field.is_active,
      });
      await mutate();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 rounded border border-subtle bg-surface-1 p-4">
        <div className="text-14 font-medium">新しい項目</div>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-13">
            名前
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="例: 顧客名"
              className="rounded border border-subtle bg-surface-1 px-2 py-1.5"
            />
          </label>
          <label className="flex flex-col gap-1 text-13">
            種類
            <select
              value={fieldType}
              onChange={(e) => setFieldType(e.target.value as TCustomFieldType)}
              className="rounded border border-subtle bg-surface-1 px-2 py-1.5"
            >
              {(Object.keys(FIELD_TYPE_LABELS) as TCustomFieldType[]).map((type) => (
                <option key={type} value={type}>
                  {FIELD_TYPE_LABELS[type]}
                </option>
              ))}
            </select>
          </label>
        </div>
        {fieldType === "select" && (
          <label className="flex flex-col gap-1 text-13">
            選択肢（カンマ区切り）
            <input
              value={optionsText}
              onChange={(e) => setOptionsText(e.target.value)}
              placeholder="例: A社, B社, C社"
              className="rounded border border-subtle bg-surface-1 px-2 py-1.5"
            />
          </label>
        )}
        <label className="flex items-center gap-2 text-13">
          <input type="checkbox" checked={required} onChange={(e) => setRequired(e.target.checked)} />
          必須にする
        </label>
        {error && <div className="text-13 text-danger-primary">{error}</div>}
        <div>
          <button
            onClick={handleCreate}
            disabled={busy}
            className="bg-primary rounded px-4 py-1.5 text-13 font-medium text-white disabled:opacity-50"
          >
            追加
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {isLoading && <Loader.Item height="80px" width="100%" />}
        {!isLoading &&
          (fields ?? []).map((field) => (
            <div
              key={field.id}
              className="flex items-center justify-between gap-3 rounded border border-subtle bg-surface-1 px-3 py-2"
            >
              <div className="flex items-center gap-3 text-13">
                <span className="font-medium">{field.name}</span>
                <span className="text-tertiary">{FIELD_TYPE_LABELS[field.field_type]}</span>
                {field.required && <span className="text-tertiary">必須</span>}
                {!field.is_active && <span className="text-tertiary">無効</span>}
              </div>
              <div className="flex items-center gap-1">
                <IconButton
                  icon={<Icon icon={EditOutline} />}
                  aria-label={field.is_active ? "無効にする" : "有効にする"}
                  variant="ghost"
                  size="xs"
                  onClick={() => handleToggleActive(field)}
                />
                <IconButton
                  icon={<Icon icon={DeleteOutline} />}
                  aria-label="削除"
                  variant="ghost"
                  size="xs"
                  onClick={() => handleDelete(field.id)}
                />
              </div>
            </div>
          ))}
        {!isLoading && (fields ?? []).length === 0 && <div className="text-13 text-tertiary">項目はまだありません</div>}
      </div>
    </div>
  );
});
