import { useRef, useState } from "react";

// Shared workflow state for both analysis flows: holds the selected file and
// the phase machine (idle → running → done/error), and wraps a backend call
// with cancellation. Keeps the two flow components focused on their own UI.
export function useAnalysisJob() {
  const [file, setFile] = useState(null);
  const [phase, setPhase] = useState("idle"); // idle | running | done
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);
  const abortRef = useRef(null);

  // `onSuccess(data)`, if given, runs after a successful analysis (e.g. to
  // save it to history). Its failure doesn't affect `phase`/`result` -- the
  // analysis itself still succeeded -- it just surfaces via `saveError`.
  const run = async (call, onSuccess) => {
    if (!file) return;
    setError(null);
    setSaveError(null);
    setResult(null);
    setPhase("running");
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const data = await call(file, controller.signal);
      setResult(data);
      setPhase("done");
      if (onSuccess) {
        try {
          await onSuccess(data);
        } catch (err) {
          setSaveError(err.message || "Could not save this analysis to history.");
        }
      }
    } catch (err) {
      if (err.name === "AbortError") setPhase("idle");
      else {
        setError(err.message);
        setPhase("idle");
      }
    }
  };

  const cancel = () => abortRef.current?.abort();

  const reset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setSaveError(null);
    setPhase("idle");
  };

  return { file, setFile, phase, result, error, saveError, run, cancel, reset };
}
