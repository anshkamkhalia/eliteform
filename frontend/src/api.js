import { API_BASE } from "./config";
import { supabase } from "./lib/supabaseClient";

// Both endpoints are synchronous and can run for minutes on longer clips.
// fetch() has no built-in timeout, so requests simply wait; the caller gets
// an AbortController signal for user-initiated cancellation.
async function postForm(path, formData, signal) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      body: formData,
      signal,
      credentials: "same-origin",
    });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new Error(
      "Could not reach the backend. Make sure the Flask server is running on port 5001 (bash api/run_api.sh from the repo root)."
    );
  }

  // Unhandled backend exceptions surface as HTML 500 pages, so any non-JSON
  // or non-200 response is treated as "analysis failed".
  const text = await res.text();
  let data = null;
  try {
    data = JSON.parse(text);
  } catch {
    data = null;
  }

  if (!res.ok || data === null) {
    const detail = data?.error;
    throw new Error(
      detail ||
        "Analysis failed on the server. This usually means the clip was too short, the player/net wasn't detected, or the pose couldn't be tracked — try a clearer or longer clip."
    );
  }
  return data;
}

async function jsonRequest(path, { signal } = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { signal, credentials: "same-origin" });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new Error(
      "Could not reach the backend. Make sure the Flask server is running on port 5001."
    );
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(data?.error || "Request failed.");
  return data;
}

export function processTennisVideo(file, signal) {
  const fd = new FormData();
  fd.append("video", file);
  return postForm("/process-tennis-video", fd, signal);
}

export async function fetchProClips(signal) {
  return jsonRequest("/pro-clips", { signal });
}

export function processShotAnalysis(file, shotType, comparisonPro, signal) {
  const fd = new FormData();
  fd.append("video", file);
  fd.append("shot_type", shotType);
  fd.append("comparison_pro", comparisonPro);
  return postForm("/process-tennis-shot-analysis", fd, signal);
}

// AI coaching feedback generated server-side from the comparison metrics
// (the AI API key never reaches the browser).
export async function fetchCoachingTips(results, shotType, comparisonPro, signal) {
  const res = await fetch(`${API_BASE}/coaching-tips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      results,
      shot_type: shotType,
      comparison_pro: comparisonPro,
    }),
    signal,
    credentials: "same-origin",
  });
  const data = await res.json().catch(() => null);
  if (!res.ok || !data?.tips) {
    throw new Error(data?.error || "Coaching feedback is unavailable right now.");
  }
  return { tldr: data.tldr || "", tips: data.tips };
}

// ---- history (Supabase) ----
//
// Auth and history are handled directly against Supabase from the browser
// (see AuthContext.jsx and supabaseClient.js) rather than through the Flask
// backend -- RLS on the `analyses` table (supabase/schema.sql) scopes every
// read/write to the signed-in user, so there's no separate backend auth
// check needed here.

const LIST_COLUMNS =
  "id, kind, created_at, original_filename, video_key, shot_type, comparison_pro";

async function currentUserId() {
  const { data, error } = await supabase.auth.getUser();
  if (error) throw error;
  if (!data.user) throw new Error("Not signed in.");
  return data.user.id;
}

/** Persist one analysis result for the signed-in user. Called by the two
 * analysis flows right after a successful backend response. */
export async function saveAnalysis({
  kind, // "session" | "comparison"
  originalFilename,
  videoKey,
  shotType,
  comparisonPro,
  payload, // the full JSON response from processTennisVideo / processShotAnalysis
}) {
  const userId = await currentUserId();
  const { error } = await supabase.from("analyses").insert({
    user_id: userId,
    kind,
    original_filename: originalFilename ?? null,
    video_key: videoKey ?? null,
    shot_type: shotType ?? null,
    comparison_pro: comparisonPro ?? null,
    results_json: payload,
  });
  if (error) throw error;
}

export async function fetchHistory() {
  const { data, error } = await supabase
    .from("analyses")
    .select(LIST_COLUMNS)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return data;
}

export async function fetchHistoryItem(id, signal) {
  let query = supabase
    .from("analyses")
    .select(`${LIST_COLUMNS}, results_json`)
    .eq("id", id)
    .single();
  if (signal) query = query.abortSignal(signal);
  const { data, error } = await query;
  if (error) throw error;
  return { ...data, payload: data.results_json };
}

export async function deleteHistoryItem(id) {
  const { error } = await supabase.from("analyses").delete().eq("id", id);
  if (error) throw error;
}

const SEARCH_MODES = [
  { id: "all", label: "Everything", placeholder: "Search filename, pro, shot type…" },
  { id: "filename", label: "Filename", placeholder: "e.g. test_forehand.mp4" },
  { id: "pro", label: "Pro / player", placeholder: "e.g. Dimitrov, Sinner" },
  { id: "shot_type", label: "Shot type", placeholder: "forehand, backhand, or serve" },
  { id: "kind", label: "Analysis type", placeholder: "session or comparison" },
];

// No backend search service (Typesense was removed along with the old
// sqlite history store) -- this is just Postgres ILIKE filtering, which is
// plenty for one user's history.
export async function fetchHistorySearchModes() {
  return { modes: SEARCH_MODES, engine: "supabase" };
}

/** Search saved analyses. mode: all | filename | pro | shot_type | kind */
export async function searchHistory(
  { q = "", mode = "all", kind, shotType, pro } = {},
  signal
) {
  let query = supabase.from("analyses").select(LIST_COLUMNS);
  if (signal) query = query.abortSignal(signal);

  const term = q.trim();
  if (term) {
    const like = `%${term}%`;
    if (mode === "filename") {
      query = query.ilike("original_filename", like);
    } else if (mode === "pro") {
      query = query.ilike("comparison_pro", like);
    } else if (mode === "shot_type") {
      query = query.ilike("shot_type", like);
    } else if (mode === "kind") {
      query = query.ilike("kind", like);
    } else {
      query = query.or(
        `original_filename.ilike.${like},comparison_pro.ilike.${like},shot_type.ilike.${like},kind.ilike.${like}`
      );
    }
  }
  if (kind) query = query.eq("kind", kind);
  if (shotType) query = query.eq("shot_type", shotType);
  if (pro) query = query.eq("comparison_pro", pro);

  const { data, error } = await query.order("created_at", { ascending: false });
  if (error) throw error;
  return { items: data, found: data.length, engine: "supabase" };
}
