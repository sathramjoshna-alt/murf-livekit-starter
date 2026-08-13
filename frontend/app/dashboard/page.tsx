"use client";

import { useEffect, useState } from "react";

interface Analytics {
    total: number;
    successful: number;
    failed: number;
}

export default function DashboardPage() {
    const [stats, setStats] = useState<Analytics>({
        total: 0,
        successful: 0,
        failed: 0,
    });

    const [loading, setLoading] = useState(true);

    async function loadStats() {
        try {
            setLoading(true);

            const response = await fetch("/api/analytics", {
                cache: "no-store",
            });

            if (!response.ok) {
                throw new Error("Unable to load analytics");
            }

            const data = await response.json();

            setStats(data);
        } catch (error) {
            console.error("Dashboard error:", error);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadStats();

        const interval = setInterval(loadStats, 5000);

        return () => clearInterval(interval);
    }, []);

    const successRate =
        stats.total > 0
            ? Math.round((stats.successful / stats.total) * 100)
            : 0;

    return (
        <main className="min-h-screen bg-slate-950 text-white p-8">
            <div className="mx-auto max-w-6xl">

                {/* Header */}
                <div className="mb-10">
                    <p className="text-sm font-medium text-blue-400">
                        FINASSIST
                    </p>

                    <h1 className="mt-2 text-4xl font-bold">
                        Call Performance Dashboard
                    </h1>

                    <p className="mt-2 text-slate-400">
                        Monitor your AI financial assistance calls
                    </p>
                </div>

                {/* Refresh */}
                <div className="mb-6 flex justify-end">
                    <button
                        onClick={loadStats}
                        className="rounded-lg bg-blue-600 px-5 py-2 font-medium hover:bg-blue-700"
                    >
                        Refresh
                    </button>
                </div>

                {/* Statistics */}
                <div className="grid gap-6 md:grid-cols-3">

                    {/* Total */}
                    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
                        <p className="text-sm text-slate-400">
                            Total Calls
                        </p>

                        <p className="mt-3 text-5xl font-bold">
                            {loading ? "..." : stats.total}
                        </p>

                        <p className="mt-2 text-sm text-slate-500">
                            All recorded calls
                        </p>
                    </div>

                    {/* Successful */}
                    <div className="rounded-2xl border border-green-900 bg-slate-900 p-6">
                        <p className="text-sm text-green-400">
                            Successful Calls
                        </p>

                        <p className="mt-3 text-5xl font-bold text-green-400">
                            {loading ? "..." : stats.successful}
                        </p>

                        <p className="mt-2 text-sm text-slate-500">
                            Completed objectives
                        </p>
                    </div>

                    {/* Failed */}
                    <div className="rounded-2xl border border-red-900 bg-slate-900 p-6">
                        <p className="text-sm text-red-400">
                            Failed Calls
                        </p>

                        <p className="mt-3 text-5xl font-bold text-red-400">
                            {loading ? "..." : stats.failed}
                        </p>

                        <p className="mt-2 text-sm text-slate-500">
                            Objectives not completed
                        </p>
                    </div>
                </div>

                {/* Success Rate */}
                <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">

                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold">
                                Success Rate
                            </h2>

                            <p className="mt-1 text-sm text-slate-400">
                                Percentage of calls that completed their objective
                            </p>
                        </div>

                        <span className="text-3xl font-bold text-blue-400">
                            {successRate}%
                        </span>
                    </div>

                    <div className="mt-6 h-4 overflow-hidden rounded-full bg-slate-800">
                        <div
                            className="h-full rounded-full bg-blue-500 transition-all duration-500"
                            style={{ width: `${successRate}%` }}
                        />
                    </div>
                </div>

                {/* Day 8 Definition */}
                <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8">

                    <h2 className="text-xl font-semibold">
                        FinAssist Success Definition
                    </h2>

                    <p className="mt-3 leading-7 text-slate-400">
                        A successful call is one where FinAssist completes the
                        user&apos;s financial enquiry, eligibility check, or
                        appropriate human-support escalation.
                    </p>
                </div>

            </div>
        </main>
    );
}
