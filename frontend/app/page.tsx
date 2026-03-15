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

type NextGame = {
  game_id: number;
  game_date: string;
  opponent: string;
  is_home: boolean;
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
  const [nextGame, setNextGame] = useState<NextGame | null>(null);
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

  useEffect(() => {
    fetch("/api/next-game")
      .then((res) => res.json())
      .then((data) => setNextGame(data && data.game_id ? data : null))
      .catch(() => setNextGame(null));
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
    <div className="min-h-dvh bg-white font-sans">
      <main
        className="mx-auto max-w-2xl px-4 py-8 pb-[max(2rem,env(safe-area-inset-bottom))] pl-[max(1.5rem,env(safe-area-inset-left))] pr-[max(1.5rem,env(safe-area-inset-right))] sm:px-6 sm:py-12"
      >
        <h1 className="text-lg font-semibold text-zinc-900 sm:text-xl">
          Last Game
        </h1>
        <p className="mt-1 text-sm text-zinc-500">{dateStr}</p>
        <p className="text-sm text-zinc-500">
          {game.is_home ? "vs" : "@"} {ABBREV_TO_NAME[game.opponent] ?? game.opponent}
        </p>

        <div className="mt-6 flex flex-col items-center gap-4 sm:mt-8 sm:gap-6">
          <div className="flex w-full max-w-sm items-center justify-between gap-3 sm:max-w-none sm:justify-center sm:gap-8">
            <div className="flex min-w-0 flex-1 flex-col items-center gap-1.5 sm:flex-none sm:gap-2">
              <Image
                src={teamLogoUrl("TOR")}
                alt="Toronto Maple Leafs"
                width={120}
                height={120}
                className="h-16 w-16 shrink-0 object-contain sm:h-24 sm:w-24 md:h-[120px] md:w-[120px]"
              />
              <span className="truncate text-center text-sm font-medium text-zinc-700 sm:text-base">
                {ABBREV_TO_NAME.TOR}
              </span>
            </div>
            <p className="min-w-12 shrink-0 text-center text-3xl font-bold tabular-nums text-zinc-900 sm:min-w-16 sm:text-5xl">
              {game.leafs_score} – {game.opponent_score}
            </p>
            <div className="flex min-w-0 flex-1 flex-col items-center gap-1.5 sm:flex-none sm:gap-2">
              <Image
                src={teamLogoUrl(game.opponent)}
                alt={ABBREV_TO_NAME[game.opponent] ?? game.opponent}
                width={120}
                height={120}
                className="h-16 w-16 shrink-0 object-contain sm:h-24 sm:w-24 md:h-[120px] md:w-[120px]"
              />
              <span className="truncate text-center text-sm font-medium text-zinc-700 sm:text-base">
                {ABBREV_TO_NAME[game.opponent] ?? game.opponent}
              </span>
            </div>
          </div>
        </div>

        <div className="mt-5 sm:mt-6">
          <p className="text-sm font-medium text-zinc-500">
            Predicted LFR views
          </p>
          <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-900 sm:text-2xl">
            {game.predicted_views.toLocaleString()}
          </p>
        </div>

        {nextGame && (
          <div className="mt-8 border-t border-zinc-200 pt-6 sm:mt-10 sm:pt-8">
            <p className="text-xs font-medium uppercase tracking-widest text-zinc-400">
              Next game
            </p>
            <div className="mt-3 flex items-center justify-center gap-3 sm:gap-4">
              <Image
                src={teamLogoUrl("TOR")}
                alt="Maple Leafs"
                width={40}
                height={40}
                className="h-9 w-9 shrink-0 object-contain sm:h-10 sm:w-10"
              />
              <span className="text-sm text-zinc-400 sm:text-base">vs</span>
              <Image
                src={teamLogoUrl(nextGame.opponent)}
                alt={ABBREV_TO_NAME[nextGame.opponent] ?? nextGame.opponent}
                width={40}
                height={40}
                className="h-9 w-9 shrink-0 object-contain sm:h-10 sm:w-10"
              />
            </div>
            <p className="mt-1 text-center text-sm font-medium text-zinc-700">
              {nextGame.is_home ? "vs" : "@"} {ABBREV_TO_NAME[nextGame.opponent] ?? nextGame.opponent}
            </p>
            <p className="mt-2 text-center text-sm text-zinc-500">
              {(() => {
                const [y, m, d] = nextGame.game_date.split("-").map(Number);
                return new Date(y, m - 1, d).toLocaleDateString("en-CA", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                });
              })()}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
