/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// REALIFE extension: monthly operations summary tab.

import React, { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
// plane package imports
import type { IRealifeSummary } from "@plane/types";
import { Loader } from "@plane/blocks/skeleton";
// plane web services
import { AnalyticsService } from "@/services/analytics.service";
// plane web components
import AnalyticsSectionWrapper from "../analytics-section-wrapper";
import InsightCard from "../insight-card";

const analyticsService = new AnalyticsService();

const currentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

function RealifeSummary() {
  const { workspaceSlug } = useParams();
  const [month, setMonth] = useState(currentMonth());

  const { data, isLoading } = useSWR<IRealifeSummary>(
    workspaceSlug ? ["realifeSummary", workspaceSlug, month] : null,
    workspaceSlug ? () => analyticsService.getRealifeSummary(workspaceSlug.toString(), { month }) : null
  );

  const totals = useMemo(
    () => [
      { label: "作成", count: data?.totals.created ?? 0 },
      { label: "完了", count: data?.totals.completed ?? 0 },
      { label: "承認待ち", count: data?.totals.pending_approval ?? 0 },
      { label: "期限超過", count: data?.totals.overdue ?? 0 },
    ],
    [data]
  );

  return (
    <div className="px-6 py-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-20 font-bold">REALIFE 月次サマリー</h1>
        <input
          type="month"
          value={month}
          onChange={(e) => e.target.value && setMonth(e.target.value)}
          className="rounded border border-subtle bg-surface-1 px-2 py-1 text-13"
          aria-label="対象月"
        />
      </div>
      <div className="flex flex-col gap-14">
        <AnalyticsSectionWrapper title={data?.month ?? month}>
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            {totals.map((item) => (
              <InsightCard
                key={item.label}
                label={item.label}
                data={{ count: item.count, filter_count: item.count }}
                isLoading={isLoading}
              />
            ))}
          </div>
        </AnalyticsSectionWrapper>
        <AnalyticsSectionWrapper title="プロジェクト別">
          {isLoading ? (
            <Loader.Item height="120px" width="100%" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-13">
                <thead>
                  <tr className="text-left text-tertiary">
                    <th className="py-2 pr-4 font-medium">プロジェクト</th>
                    <th className="py-2 pr-4 font-medium">作成</th>
                    <th className="py-2 pr-4 font-medium">完了</th>
                    <th className="py-2 pr-4 font-medium">承認待ち</th>
                    <th className="py-2 pr-4 font-medium">期限超過</th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.projects ?? []).map((row) => (
                    <tr key={row.project_id} className="border-t border-subtle">
                      <td className="py-2 pr-4">
                        {row.project_name}
                        <span className="ml-2 text-tertiary">{row.project_identifier}</span>
                      </td>
                      <td className="py-2 pr-4">{row.created}</td>
                      <td className="py-2 pr-4">{row.completed}</td>
                      <td className="py-2 pr-4">{row.pending_approval}</td>
                      <td className="py-2 pr-4">{row.overdue}</td>
                    </tr>
                  ))}
                  {(data?.projects ?? []).length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-4 text-tertiary">
                        データがありません
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </AnalyticsSectionWrapper>
      </div>
    </div>
  );
}

export { RealifeSummary };
