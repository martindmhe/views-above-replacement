"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

const NHL_LOGO_BASE = "https://assets.nhle.com/logos/nhl/svg";
function teamLogoUrl(abbrev: string) {
  return `${NHL_LOGO_BASE}/${abbrev}_light.svg`;
}

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

const ABBREV_TO_NAME: Record<string, string> = {
  ANA: "Ducks",
  ARI: "Coyotes",
  BOS: "Bruins",
  BUF: "Sabres",
  CGY: "Flames",
  CAR: "Hurricanes",
  CHI: "Blackhawks",
  COL: "Avalanche",
  CBJ: "Blue Jackets",
  DAL: "Stars",
  DET: "Red Wings",
  EDM: "Oilers",
  FLA: "Panthers",
  LAK: "Kings",
  MIN: "Wild",
  MTL: "Canadiens",
  NJD: "Devils",
  NSH: "Predators",
  NYI: "Islanders",
  NYR: "Rangers",
  OTT: "Senators",
  PHI: "Flyers",
  PIT: "Penguins",
  SJS: "Sharks",
  SEA: "Kraken",
  STL: "Blues",
  TBL: "Lightning",
  TOR: "Maple Leafs",
  UTA: "Mammoth",
  VAN: "Canucks",
  VGK: "Golden Knights",
  WPG: "Jets",
  WSH: "Capitals",
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

  const [y, m, d] = game.game_date.split("-").map(Number);
  const dateStr = new Date(y, m - 1, d).toLocaleDateString("en-CA", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-white font-sans">
      <main className="mx-auto max-w-2xl px-6 py-12">
        <h1 className="text-xl font-semibold text-zinc-900">
          Last Game
        </h1>
        <p className="mt-1 text-sm text-zinc-500">{dateStr}</p>
        <p className="text-sm text-zinc-500">
            {game.is_home ? "vs" : "@"} {ABBREV_TO_NAME[game.opponent] ?? game.opponent}
          </p>

        <div className="mt-8 flex flex-col items-center gap-6">
          <div className="flex items-center gap-8">
            <div className="flex flex-col items-center gap-2">
              <Image
                src={teamLogoUrl("TOR")}
                alt="Toronto Maple Leafs"
                width={120}
                height={120}
                className="object-contain"
              />
              <span className="text-md font-medium text-zinc-700">
                {ABBREV_TO_NAME.TOR}
              </span>
            </div>
            <p className="min-w-16 text-center text-5xl font-bold tabular-nums text-zinc-900">
              {game.leafs_score} – {game.opponent_score}
            </p>
            <div className="flex flex-col items-center gap-2">
              <Image
                src={teamLogoUrl(game.opponent)}
                alt={ABBREV_TO_NAME[game.opponent] ?? game.opponent}
                width={120}
                height={120}
                className="object-contain"
              />
              <span className="text-md font-medium text-zinc-700">
                {ABBREV_TO_NAME[game.opponent] ?? game.opponent}
              </span>
            </div>
          </div>
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
