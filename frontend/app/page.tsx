"use client";

import { useEffect, useState } from "react";

type LatestGame = {
  game_id: number;
  game_date: string;
  opponent: string;
  is_home: boolean;
  leafs_score: number;
  opponent_score: number;
  predicted_views: number;
  features?: Record<string, unknown>;
};

export default function Home() {
  const [game, setGame] = useState<LatestGame | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/latest-predicted-game")
      .then((res) => {
        if (!res.ok) throw new Error(res.status === 404 ? "No game with prediction found" : "Failed to load");
        return res.json();
      })
      .then(setGame)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white font-sans">
        <p className="text-zinc-600">Loading…</p>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white font-sans">
        <p className="text-red-600">{error ?? "No game found"}</p>
      </div>
    );
  }

  const matchup = game.is_home ? `vs ${game.opponent}` : `@ ${game.opponent}`;
  const dateStr = new Date(game.game_date).toLocaleDateString("en-CA", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-white font-sans">
      <main className="mx-auto max-w-2xl px-6 py-12">
        <h1 className="text-xl font-semibold text-zinc-900">
          Latest game with prediction
        </h1>
        <p className="mt-1 text-sm text-zinc-500">{dateStr}</p>

        <div className="mt-6">
          <p className="text-lg font-medium text-zinc-800">
            Toronto Maple Leafs {matchup}
          </p>
          <p className="mt-2 text-3xl font-bold tabular-nums text-zinc-900">
            {game.leafs_score} – {game.opponent_score}
          </p>
        </div>

        <div className="mt-6">
          <p className="text-sm font-medium text-zinc-500">
            Predicted LFR views
          </p>
          <p className="mt-1 text-2xl font-semibold text-zinc-900">
            {game.predicted_views.toLocaleString()}
          </p>
        </div>
      </main>
    </div>
  );
}
