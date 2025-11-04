import type { FileDropZoneProps } from "$lib/components/ui/file-drop-zone";

export type BoundFile = {
  name: string;
  size: number;
  type: string;
};

export type FileBinding = {
  file_count: number;
  files: string;
  error: string;
  max_files?: number;
  selected_config?: string | null;
};

type UploadHandler = FileDropZoneProps["onUpload"];
type RejectHandler = NonNullable<FileDropZoneProps["onFileRejected"]>;

export function createFileBindingHandlers({
  bindings,
  maxFilesProp,
}: {
  bindings: FileBinding;
  maxFilesProp?: number;
}) {
  const normalizeFiles = (files: unknown): BoundFile[] => {
    if (!Array.isArray(files)) return [];

    return files
      .filter(
        (item) =>
          item &&
          typeof item.name === "string" &&
          typeof item.size === "number" &&
          typeof item.type === "string"
      )
      .slice(0, 1)
      .map((item) => ({
        name: item.name,
        size: item.size,
        type: item.type,
      }));
  };

  const readBoundFiles = (): BoundFile[] => {
    if (!bindings?.files) return [];
    try {
      const parsed = JSON.parse(bindings.files) as unknown;
      return normalizeFiles(parsed);
    } catch {
      return [];
    }
  };

  const writeBoundFiles = (files: BoundFile[]): void => {
    const normalized = normalizeFiles(files);
    bindings.files = JSON.stringify(normalized);
    bindings.file_count = normalized.length;
  };

  const maxFiles = (): number => maxFilesProp ?? bindings?.max_files ?? 5;

  const handleUpload: UploadHandler = async (files) => {
    const [first] = files;
    if (!first) return;

    const nextFile = {
      name: first.name,
      size: first.size,
      type: first.type,
    };

    writeBoundFiles([nextFile]);
    bindings.error = "";
  };

  const handleFileRejected: RejectHandler = ({ reason, file }) => {
    bindings.error = `${file.name}: ${reason}`;
  };

  const removeFile = (index: number): void => {
    const current = readBoundFiles();
    current.splice(index, 1);
    writeBoundFiles(current);

    if (current.length === 0) {
      bindings.error = "";
    }
  };

  const writeSelectedConfig = (contents: string | null | undefined): void => {
    bindings.selected_config = contents ?? "";
  };

  return {
    bindings,
    readBoundFiles,
    writeBoundFiles,
    maxFiles,
    handleUpload,
    handleFileRejected,
    removeFile,
    writeSelectedConfig,
  };
}
