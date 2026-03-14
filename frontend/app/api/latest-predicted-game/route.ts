import { createClient } from "@supabase/supabase-js";
import { NextResponse } from "next/server";

export async function GET() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) {
    return NextResponse.json(
      { error: "Supabase not configured" },
      { status: 503 }
    );
  }

  const supabase = createClient(url, key);
  const { data, error } = await supabase
    .from("views")
    .select(
      "game_id, game_date, opponent, is_home, leafs_score, opponent_score, predicted_views, features"
    )
    .not("predicted_views", "is", null)
    .order("game_date", { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  if (!data) {
    return NextResponse.json(
      { error: "No game with prediction found" },
      { status: 404 }
    );
  }

  return NextResponse.json(data);
}
