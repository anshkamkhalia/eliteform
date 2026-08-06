import { useEffect, useState } from "react";
import { fetchProClips, processShotAnalysis, saveAnalysis } from "../api";
import { SHOT_TYPES } from "../config";
import { useAnalysisJob } from "../hooks/useAnalysisJob";
import Panel from "../components/Panel";
import FileDrop from "../components/FileDrop";
import AnalysisStatus from "../components/AnalysisStatus";
import ComparisonResults from "../components/ComparisonResults";
import { IconAlert, IconChart } from "../components/icons";

function referenceLabel(file) {
  if (!file?.name) return "Custom";
  return file.name.replace(/\.[^.]+$/, "") || "Custom";
}

export default function ShotComparisonFlow() {
  const job = useAnalysisJob();
  const { file, setFile, phase, result, error, saveError } = job;

  const [shotType, setShotType] = useState("forehand");
  const [refMode, setRefMode] = useState("pro"); // "pro" | "custom"
  const [pro, setPro] = useState("");
  const [proOptions, setProOptions] = useState(null);
  const [proOptionsError, setProOptionsError] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchProClips()
      .then((data) => {
        if (cancelled) return;
        setProOptions(data);
        setPro(data[shotType]?.[0] || "");
      })
      .catch((err) => {
        if (!cancelled) setProOptionsError(err.message);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pickShotType = (t) => {
    setShotType(t);
    setPro(proOptions?.[t]?.[0] || "");
  };

  const comparisonLabel =
    refMode === "custom" ? referenceLabel(referenceFile) : pro;

  const canRun =
    Boolean(file) &&
    phase !== "running" &&
    (refMode === "custom" ? Boolean(referenceFile) : Boolean(pro));

  const resetAll = () => {
    job.reset();
    setReferenceFile(null);
  };

  return (
    <div className="workspace">
      <aside className="rail">
        <Panel title="Your shot">
          <FileDrop
            file={file}
            onFile={setFile}
            hint="One shot per clip · native resolution is preserved"
          />
        </Panel>

        <Panel title="Options">
          <div className="field">
            <label>Shot type</label>
            <div className="seg" role="group" aria-label="Shot type">
              {SHOT_TYPES.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={t === shotType ? "active" : ""}
                  onClick={() => pickShotType(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Compare against</label>
            <div className="seg" role="group" aria-label="Reference source">
              <button
                type="button"
                className={refMode === "pro" ? "active" : ""}
                onClick={() => setRefMode("pro")}
              >
                Pro clip
              </button>
              <button
                type="button"
                className={refMode === "custom" ? "active" : ""}
                onClick={() => setRefMode("custom")}
              >
                Your video
              </button>
            </div>
          </div>

          {refMode === "pro" ? (
            <div className="field">
              <label>Professional</label>
              <select
                value={pro}
                onChange={(e) => setPro(e.target.value)}
                disabled={!proOptions}
              >
                {!proOptions && <option>Loading professional clips…</option>}
                {proOptions?.[shotType]?.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="field">
              <label>Reference video</label>
              <FileDrop
                file={referenceFile}
                onFile={setReferenceFile}
                hint="Any player or coach clip to compare against"
              />
            </div>
          )}
        </Panel>

        {refMode === "pro" && proOptionsError && (
          <div className="alert alert-error" role="alert">
            <IconAlert size={16} />
            <div>Couldn't load professional clips: {proOptionsError}</div>
          </div>
        )}

        {error && (
          <div className="alert alert-error" role="alert">
            <IconAlert size={16} />
            <div>{error}</div>
          </div>
        )}
        {saveError && (
          <div className="alert alert-error" role="alert">
            <IconAlert size={16} />
            <div>Saved analysis to history failed: {saveError}</div>
          </div>
        )}

        <div className="rail-actions">
          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled={!canRun}
            onClick={() =>
              job.run(
                (f, signal) =>
                  processShotAnalysis(
                    f,
                    shotType,
                    comparisonLabel,
                    signal,
                    refMode === "custom" ? referenceFile : null
                  ),
                (data) =>
                  saveAnalysis({
                    kind: "comparison",
                    originalFilename: file?.name,
                    videoKey: data.key,
                    shotType,
                    comparisonPro: data.comparison_pro || comparisonLabel,
                    payload: data,
                  })
              )
            }
          >
            Compare shot
          </button>
          {(file || referenceFile || result) && phase !== "running" && (
            <button
              type="button"
              className="btn btn-subtle btn-block"
              onClick={resetAll}
            >
              Reset
            </button>
          )}
        </div>
      </aside>

      <section className="canvas">
        {phase === "running" && (
          <AnalysisStatus
            title={`Comparing ${shotType} against ${comparisonLabel}`}
            message="Running pose estimation over your clip and the reference clip, then diffing wrist velocity and six joint angles."
            onCancel={job.cancel}
          />
        )}

        {phase === "idle" && (
          <div className="empty">
            <div className="e-icon">
              <IconChart />
            </div>
            <h3>No comparison yet</h3>
            <p>
              Upload a single-shot clip, pick a pro reference or upload your own
              comparison video, then run the comparison to see velocity, joint
              angles, and swing path side by side.
            </p>
          </div>
        )}

        {phase === "done" && result && (
          <ComparisonResults
            result={result}
            shotType={shotType}
            pro={result.comparison_pro || comparisonLabel}
            actionLabel="New comparison"
            onAction={resetAll}
          />
        )}
      </section>
    </div>
  );
}
