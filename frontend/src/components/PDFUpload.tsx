import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { getApiUrl, environmentConfiguration } from "@/lib/config";

interface PDFUploadProps {
  onUploadSuccess?: () => void;
}

export function PDFUpload({ onUploadSuccess }: PDFUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === "application/pdf") {
        setFile(selectedFile);
        setStatus("idle");
        setMessage("");
      } else {
        setStatus("error");
        setMessage("Please select a PDF file");
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus("idle");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(getApiUrl(environmentConfiguration.endpoints.uploadPdf), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const result = await response.json();
      setStatus("success");
      setMessage(result.message || "PDF uploaded successfully");
      setFile(null);
      
      const fileInput = document.getElementById("pdf-upload") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
      
      onUploadSuccess?.();
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Failed to upload PDF");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <label htmlFor="pdf-upload" className="cursor-pointer">
          <input
            id="pdf-upload"
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
          />
          <Button
            variant="outline"
            asChild
            disabled={uploading}
          >
            <span>
              <Upload className="h-4 w-4 mr-2" />
              Choose PDF
            </span>
          </Button>
        </label>

        {file && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">{file.name}</span>
            <Button
              onClick={handleUpload}
              disabled={uploading}
              size="sm"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                "Upload"
              )}
            </Button>
          </div>
        )}
      </div>

      {message && (
        <div
          className={`flex items-center gap-2 text-sm ${
            status === "success"
              ? "text-green-600"
              : status === "error"
              ? "text-red-600"
              : "text-muted-foreground"
          }`}
        >
          {status === "success" && <CheckCircle className="h-4 w-4" />}
          {status === "error" && <XCircle className="h-4 w-4" />}
          <span>{message}</span>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Upload a travel guide PDF to enhance Paradise's knowledge. The PDF will be processed and indexed for retrieval.
      </p>
    </div>
  );
}

