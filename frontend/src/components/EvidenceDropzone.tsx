import { useState, useRef, type DragEvent, type ChangeEvent } from "react";
import {
  UploadSimple,
  FileCode,
  FileText,
  FileCsv,
  CheckCircle,
  Warning,
  XCircle,
  Trash,
  ArrowClockwise,
} from "@phosphor-icons/react";
import {
  type EvidenceFileRecord,
  type CrossFileAnalysisResult,
  processMultiFileBatch,
  parseEvidenceFile,
  analyzeCrossFileEvidence,
} from "../utils/crossFileIntelligence";

interface EvidenceDropzoneProps {
  files: EvidenceFileRecord[];
  onFilesChange: (files: EvidenceFileRecord[]) => void;
  analysis: CrossFileAnalysisResult | null;
  onAnalysisChange: (analysis: CrossFileAnalysisResult) => void;
  disabled?: boolean;
  onBusyChange?: (busy: boolean) => void;
}

export function EvidenceDropzone({
  files,
  onFilesChange,
  analysis,
  onAnalysisChange,
  disabled = false,
  onBusyChange,
}: EvidenceDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const busyRef = useRef(false);
  const originals = useRef(new Map<string, File>());
  const [batchError, setBatchError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleIncomingFiles(fileList: File[]) {
    if (fileList.length === 0 || disabled || busyRef.current) return;
    if (files.length + fileList.length > 20) {
      setBatchError(
        "Keep at most 20 files per case. No files from this selection were added.",
      );
      return;
    }
    busyRef.current = true;
    setProcessing(true);
    onBusyChange?.(true);
    setBatchError(null);
    try {
      const processed = await processMultiFileBatch(fileList);
      processed.forEach((record, i) =>
        originals.current.set(record.id, fileList[i]),
      );
      const merged = [...files, ...processed];
      onFilesChange(merged);
      onAnalysisChange(analyzeCrossFileEvidence(merged));
    } finally {
      busyRef.current = false;
      setProcessing(false);
      onBusyChange?.(false);
    }
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !processing) setIsDragging(true);
  }

  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled || processing) return;
    const droppedFiles = Array.from(e.dataTransfer.files ?? []);
    void handleIncomingFiles(droppedFiles);
  }

  function handleFileInput(e: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(e.target.files ?? []);
    e.target.value = "";
    void handleIncomingFiles(selectedFiles);
  }

  function removeFile(fileId: string) {
    if (disabled || busyRef.current) return;
    originals.current.delete(fileId);
    const remaining = files.filter((f) => f.id !== fileId);
    onFilesChange(remaining);
    const newAnalysis = analyzeCrossFileEvidence(remaining);
    onAnalysisChange(newAnalysis);
  }

  async function retryFile(fileRecord: EvidenceFileRecord) {
    const original = originals.current.get(fileRecord.id);
    if (!original || disabled || busyRef.current) return;
    busyRef.current = true;
    setProcessing(true);
    onBusyChange?.(true);
    try {
      const retried = {
        ...(await parseEvidenceFile(original)),
        id: fileRecord.id,
      };
      const updated = files.map((f) => (f.id === fileRecord.id ? retried : f));
      onFilesChange(updated);
      onAnalysisChange(analyzeCrossFileEvidence(updated));
    } finally {
      busyRef.current = false;
      setProcessing(false);
      onBusyChange?.(false);
    }
  }

  function getFileIcon(type: EvidenceFileRecord["type"]) {
    switch (type) {
      case "json":
        return <FileCode size={20} className="file-icon json-icon" />;
      case "csv":
        return <FileCsv size={20} className="file-icon csv-icon" />;
      default:
        return <FileText size={20} className="file-icon txt-icon" />;
    }
  }

  function getStatusBadge(status: EvidenceFileRecord["status"]) {
    switch (status) {
      case "complete":
        return (
          <span className="file-status-badge status-complete">
            <CheckCircle size={14} /> Ready
          </span>
        );
      case "warning":
        return (
          <span className="file-status-badge status-warning">
            <Warning size={14} /> Warning
          </span>
        );
      case "failed":
        return (
          <span className="file-status-badge status-failed">
            <XCircle size={14} /> Failed
          </span>
        );
      default:
        return (
          <span className="file-status-badge status-processing">
            <ArrowClockwise size={14} className="spin" /> {status}
          </span>
        );
    }
  }

  return (
    <section
      className="evidence-dropzone-wrapper"
      aria-label="Evidence File Ingestion"
      aria-busy={processing}
    >
      <div
        className={`evidence-dropzone ${isDragging ? "dragging" : ""} ${disabled || processing ? "disabled" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && !processing && inputRef.current?.click()}
        role="button"
        aria-disabled={disabled || processing}
        tabIndex={disabled || processing ? -1 : 0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!disabled && !processing) inputRef.current?.click();
          }
        }}
        aria-describedby="dropzone-instructions"
      >
        <input
          ref={inputRef}
          type="file"
          name="evidence_file"
          multiple
          disabled={disabled || processing}
          aria-label="Import evidence files"
          accept=".json,.txt,.csv,application/json,text/plain,text/csv"
          onChange={handleFileInput}
          style={{ display: "none" }}
          tabIndex={-1}
        />

        <div className="dropzone-content">
          <div className="dropzone-icon-circle">
            <UploadSimple size={28} />
          </div>
          <div className="dropzone-text">
            <h3>Drag & drop dispute evidence files here</h3>
            <p id="dropzone-instructions">
              Supports <strong>.json</strong> (dispute bundles),{" "}
              <strong>.txt</strong> (customer chat / emails), and{" "}
              <strong>.csv</strong> (ledger exports for inspection) up to 256 KB
              per file; 20 files per case. UTF-8 text only.
            </p>
          </div>
          <div className="dropzone-formats-badge">
            <span>JSON</span>
            <span>TXT</span>
            <span>CSV</span>
          </div>
          {processing && (
            <div className="dropzone-processing-bar" role="status">
              <ArrowClockwise className="spin" size={16} />
              <span>Processing and extracting multi-document evidence…</span>
            </div>
          )}
        </div>
      </div>

      {batchError && <p role="alert">{batchError}</p>}
      {analysis?.errors.map((message) => (
        <p key={message} role="alert">
          {message}
        </p>
      ))}
      {files.length > 0 && (
        <div className="evidence-tray" aria-label="Ingested Evidence Files">
          <div className="evidence-tray-header">
            <h4>
              Ingested Evidence ({files.length} document
              {files.length > 1 ? "s" : ""})
            </h4>
            <span className="evidence-tray-summary">
              {files.filter((f) => f.status === "complete").length} parsed ·{" "}
              {(files.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(1)} KB
              total
            </span>
          </div>

          <div className="evidence-cards-list">
            {files.map((file) => (
              <div
                key={file.id}
                className={`evidence-card ${file.status === "failed" ? "card-failed" : ""}`}
              >
                <div className="card-left">
                  {getFileIcon(file.type)}
                  <div className="card-meta">
                    <details className="source-preview">
                      <summary className="card-name">{file.name}</summary>
                      <p>
                        Original local text. Reading a file does not
                        authenticate its source.
                      </p>
                      <pre>
                        {file.rawContent ||
                          "No readable text retained. Retry or select the file again."}
                      </pre>
                      {analysis?.sources
                        .filter((source) => source.id === file.id)
                        .map((source) => (
                          <p key={source.id}>
                            Communication offsets [{source.start}, {source.end})
                            in the combined input. The body is preserved
                            verbatim.
                          </p>
                        ))}
                    </details>
                    <span className="card-size">
                      {(file.size / 1024).toFixed(1)} KB ·{" "}
                      {file.type.toUpperCase()} · {file.facts.sourceLineCount}{" "}
                      lines
                    </span>
                  </div>
                </div>

                <div className="card-center">
                  {getStatusBadge(file.status)}
                  {file.errorMessage && (
                    <p className="card-error" role="alert">
                      {file.errorMessage}
                    </p>
                  )}
                  {file.warnings.length > 0 && (
                    <p className="card-warning">{file.warnings.join("; ")}</p>
                  )}
                </div>

                <div className="card-actions">
                  {file.status === "failed" && (
                    <button
                      type="button"
                      className="card-btn btn-retry"
                      disabled={disabled || processing}
                      title="Read and parse the file again"
                      onClick={(e) => {
                        e.stopPropagation();
                        void retryFile(file);
                      }}
                    >
                      <ArrowClockwise size={14} /> Retry
                    </button>
                  )}
                  <button
                    type="button"
                    className="card-btn btn-remove"
                    disabled={disabled || processing}
                    aria-label={`Remove ${file.name}`}
                    title="Remove file"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(file.id);
                    }}
                  >
                    <Trash size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {analysis && analysis.anomalies.length > 0 && (
            <div className="cross-file-insights" aria-label="File review notes">
              <div className="insights-header">
                <Warning size={18} />
                <h5>Files to inspect</h5>
              </div>
              <ul className="anomalies-list">
                {analysis.anomalies.map((anomaly, idx) => (
                  <li
                    key={idx}
                    className={`anomaly-item anomaly-${anomaly.severity}`}
                  >
                    <div className="anomaly-title-row">
                      <Warning size={15} />
                      <strong>{anomaly.title}</strong>
                      <span className="anomaly-sources">
                        Sources: {anomaly.sources.join(", ")}
                      </span>
                    </div>
                    <p className="anomaly-desc">{anomaly.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
