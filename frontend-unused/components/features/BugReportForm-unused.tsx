import React, { useState, useEffect } from 'react';

// --- Scan status polling hook ---
export function useScanStatus(fileName: string) {
  const [status, setStatus] = useState<"pending" | "clean" | "infected" | "error">("pending");

  useEffect(() => {
    let retries = 60; // 2 minutes (60 × 2s)
    let stopped = false;
    const check = async () => {
      try {
        console.log(`[SCAN] Checking temp/${fileName}`);
        const tempResp = await fetch(`/check-file-status?key=temp/${fileName}`, { method: "HEAD" });
        if (tempResp.ok) {
          console.log(`[SCAN] Found in temp/${fileName} (pending)`);
          if (!stopped && status !== "pending") setStatus("pending");
        } else if (tempResp.status === 404) {
          console.log(`[SCAN] Not found in temp/${fileName}, checking permanent/${fileName}`);
          const permResp = await fetch(`/check-file-status?key=permanent/${fileName}`, { method: "HEAD" });
          if (permResp.ok) {
            console.log(`[SCAN] Found in permanent/${fileName} (clean)`);
            if (!stopped) setStatus("clean");
            return;
          } else if (permResp.status === 404) {
            console.log(`[SCAN] Not found in permanent/${fileName}`);
            if (retries <= 0) {
              console.log(`[SCAN] Not found after retries, marking as infected`);
              if (!stopped) setStatus("infected");
              return;
            }
          } else {
            console.log(`[SCAN] Error response from permanent/${fileName}:`, permResp.status);
            if (!stopped) setStatus("error");
            return;
          }
        } else {
          console.log(`[SCAN] Error response from temp/${fileName}:`, tempResp.status);
          if (!stopped) setStatus("error");
          return;
        }
      } catch (e) {
        console.log(`[SCAN] Exception:`, e);
        if (!stopped) setStatus("error");
        return;
      }
      if (retries-- > 0 && status === "pending") {
        setTimeout(check, 2000);
      }
    };
    check();
    return () => { stopped = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileName]);
  return status;
}

// --- UploadStatus component ---
function UploadStatus({ fileName }: { fileName: string }) {
  const status = useScanStatus(fileName);
  if (status === "pending") return <span>🕐 Scanning...</span>;
  if (status === "clean") return <span>✅ Clean — uploaded</span>;
  if (status === "infected") return <span style={{ color: "red" }}>🚨 INFECTED (deleted)</span>;
  return <span>⚠️ Error</span>;
}

const BugReportForm: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle file selection and upload
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setError(null);
    setUploading(true);
    try {
      // Step 1: Get presigned URL
      const res = await fetch("/generate-presigned-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: selected.name, type: selected.type, size: selected.size }),
      });
      if (!res.ok) throw new Error("Failed to get presigned URL");
      const { url } = await res.json();
      // Step 2: Upload to S3
      const upload = await fetch(url, {
        method: "PUT",
        body: selected,
        headers: { "Content-Type": selected.type },
      });
      if (!upload.ok) throw new Error("Upload failed");
      setUploadedFileName(selected.name);
    } catch (err: any) {
      setError(err.message || "Unknown error");
      setUploadedFileName(null);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form>
      <h2>Bug Report</h2>
      <input type="text" name="reporterName" placeholder="Your Name" required />
      <div style={{ margin: '1em 0' }}>
        <label>
          Attachment:
          <input type="file" onChange={handleFileChange} disabled={uploading} />
        </label>
        {uploading && <span style={{ marginLeft: 8 }}>Uploading...</span>}
        {error && <div style={{ color: 'red' }}>{error}</div>}
      </div>
      {uploadedFileName && (
        <div style={{ margin: '1em 0' }}>
          <strong>Attachment scan status:</strong> <UploadStatus fileName={uploadedFileName} />
        </div>
      )}
      <button type="submit">Submit</button>
    </form>
  );
};

export default BugReportForm;
