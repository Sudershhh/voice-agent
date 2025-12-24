import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { getApiUrl, environmentConfiguration } from "@/lib/config";
import { motion, AnimatePresence } from "framer-motion";

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
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      <div className="flex items-center gap-4 flex-wrap">
        <motion.label
          htmlFor="pdf-upload"
          className="cursor-pointer"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
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
            className="gap-2"
          >
            <span>
              <Upload className="h-4 w-4" />
              Choose PDF
            </span>
          </Button>
        </motion.label>

        <AnimatePresence>
          {file && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex items-center gap-2 flex-1 min-w-0"
            >
              <span className="text-sm text-muted-foreground truncate">
                {file.name}
              </span>
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                  size="sm"
                  className="gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    "Upload"
                  )}
                </Button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`flex items-center gap-2 text-sm ${
              status === "success"
                ? "text-green-600 dark:text-green-400"
                : status === "error"
                ? "text-destructive"
                : "text-muted-foreground"
            }`}
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            >
              {status === "success" && <CheckCircle className="h-4 w-4" />}
              {status === "error" && <XCircle className="h-4 w-4" />}
            </motion.div>
            <span>{message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-xs text-muted-foreground"
      >
        Upload a travel guide PDF to enhance Paradise AI's knowledge. The PDF will be processed and indexed for retrieval.
      </motion.p>
    </motion.div>
  );
}

