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
  ShieldCheck,
  Sparkle,
} from "@phosphor-icons/react";
import {
  type EvidenceFileRecord,
  type CrossFileAnalysisResult,
  processEvidenceFile,
  analyzeCrossFileEvidence,
} from "../utils/crossFileIntelligence";

interface EvidenceDropzoneProps {
  files: EvidenceFileRecord[];
  onFilesChange: (files: EvidenceFileRecord[]) => void;
  analysis: CrossFileAnalysisResult | null;
  onAnalysisChange: (analysis: CrossFileAnalysisResult) => void;
  onLoadSample?: (sampleKey: string) => void;
  disabled?: boolean;
}

export function EvidenceDropzone({
  files,
  onFilesChange,
  analysis,
  onAnalysisChange,
  onLoadSample,
  disabled = false,
}: EvidenceDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [processing, setProcessing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleIncomingFiles(fileList: File[]) {
    if (fileList.length === 0) return;
    setProcessing(true);

    const processedList: EvidenceFileRecord[] = [];
    for (const file of fileList) {
      const content = await file.text();
      const record = await processEvidenceFile(file.name, file.size, content);
      processedList.push(record);
    }

    // Merge with existing files, deduplicating by filename
    const merged = [...files];
    processedList.forEach((incoming) => {
      const existingIdx = merged.findIndex((f) => f.name === incoming.name);
      if (existingIdx >= 0) {
        merged[existingIdx] = incoming;
      } else {
        merged.push(incoming);
      }
    });

    onFilesChange(merged);
    const newAnalysis = analyzeCrossFileEvidence(merged);
    onAnalysisChange(newAnalysis);
    setProcessing(false);
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
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
    if (disabled) return;
    const droppedFiles = Array.from(e.dataTransfer.files ?? []);
    void handleIncomingFiles(droppedFiles);
  }

  function handleFileInput(e: ChangeEvent<HTMLInputElement>) {
    const selectedFiles = Array.from(e.target.files ?? []);
    e.target.value = "";
    void handleIncomingFiles(selectedFiles);
  }

  function removeFile(fileId: string) {
    const remaining = files.filter((f) => f.id !== fileId);
    onFilesChange(remaining);
    const newAnalysis = analyzeCrossFileEvidence(remaining);
    onAnalysisChange(newAnalysis);
  }

  async function retryFile(fileRecord: EvidenceFileRecord) {
    const retried = await processEvidenceFile(
      fileRecord.name,
      fileRecord.size,
      fileRecord.rawContent,
    );
    const updated = files.map((f) => (f.id === fileRecord.id ? retried : f));
    onFilesChange(updated);
    const newAnalysis = analyzeCrossFileEvidence(updated);
    onAnalysisChange(newAnalysis);
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
    >
      <div
        className={`evidence-dropzone ${isDragging ? "dragging" : ""} ${disabled ? "disabled" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={disabled ? -1 : 0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            if (!disabled) inputRef.current?.click();
          }
        }}
        aria-describedby="dropzone-instructions"
      >
        <input
          ref={inputRef}
          type="file"
          multiple
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
              <strong>.csv</strong> (authoritative refund ledger exports) up to
              256 KB.
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

      {onLoadSample && (
        <div className="sample-quick-load">
          <span className="sample-quick-title">Or load a sample case:</span>
          <div className="sample-quick-buttons">
            <button
              type="button"
              className="sample-pill"
              onClick={() => onLoadSample("wrong_amount")}
            >
              Amount Mismatch
            </button>
            <button
              type="button"
              className="sample-pill"
              onClick={() => onLoadSample("missing_ledger")}
            >
              Missing Ledger
            </button>
            <button
              type="button"
              className="sample-pill"
              onClick={() => onLoadSample("contradiction")}
            >
              Contradictory Email
            </button>
            <button
              type="button"
              className="sample-pill"
              onClick={() => onLoadSample("prompt_injection")}
            >
              Prompt Injection
            </button>
          </div>
        </div>
      )}

      {files.length > 0 && (
        <div className="evidence-tray" aria-label="Ingested Evidence Files">
          <div className="evidence-tray-header">
            <h4>
              Ingested Evidence ({files.length} document
              {files.length > 1 ? "s" : ""})
            </h4>
            <span className="evidence-tray-summary">
              {files.filter((f) => f.status === "complete").length} verified ·{" "}
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
                    <strong className="card-name" title={file.name}>
                      {file.name}
                    </strong>
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
                      title="Retry parsing file"
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
            <div
              className="cross-file-insights"
              aria-label="Cross-File Synthesis"
            >
              <div className="insights-header">
                <Sparkle size={18} />
                <h5>Cross-Document Case Intelligence</h5>
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
              {analysis.corroborations.length > 0 && (
                <div className="corroborations-list">
                  <ShieldCheck size={16} />
                  <span>{analysis.corroborations.join(" ")}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
