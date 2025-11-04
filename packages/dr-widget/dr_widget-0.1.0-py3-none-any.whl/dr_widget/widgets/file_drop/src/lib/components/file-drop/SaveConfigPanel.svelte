<script lang="ts">
  import * as Card from "$lib/components/ui/card/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";

  type SaveResult = {
    fileName?: string;
    timestamp: string;
  };

  type SaveFilePickerOptions = {
    suggestedName?: string;
    startIn?: BrowserFileHandle;
    types?: Array<{ description?: string; accept: Record<string, string[]> }>;
  };

  type BrowserFileHandle = {
    readonly kind?: "file" | "directory";
    name: string;
    createWritable: () => Promise<{
      write: (data: Blob | BufferSource | string) => Promise<void>;
      close: () => Promise<void>;
    }>;
    getFile?: () => Promise<File>;
    requestPermission?: (options?: { mode?: "read" | "readwrite" }) => Promise<PermissionState>;
  };

  type FileSystemAccessWindow = Window &
    typeof globalThis & {
      showSaveFilePicker?: (options?: SaveFilePickerOptions) => Promise<BrowserFileHandle>;
    };

  const {
    rawConfig,
    defaultFileName = "config.json",
    dirty = false,
    onSaveSuccess,
    onSaveError,
  } = $props<{
    rawConfig?: string;
    defaultFileName?: string;
    dirty?: boolean;
    onSaveSuccess?: (result: SaveResult) => void;
    onSaveError?: (message: string) => void;
  }>();

  let fileHandle = $state<BrowserFileHandle | null>(null);
  let chosenFileName = $state(defaultFileName);
  let lastSavedMessage = $state("");
  let saveError = $state("");
  let saving = $state(false);

  const fsWindow: FileSystemAccessWindow | undefined =
    typeof window !== "undefined"
      ? (window as FileSystemAccessWindow)
      : undefined;

  const supportsFileSystemAccess = Boolean(fsWindow?.showSaveFilePicker);
  const inputId = `save-config-${Math.random().toString(36).slice(2)}`;

  $effect(() => {
    if (!fileHandle && defaultFileName && !chosenFileName) {
      chosenFileName = defaultFileName;
    }
  });

  const buildPickerOptions = (): SaveFilePickerOptions => {
    const options: SaveFilePickerOptions = {
      suggestedName: chosenFileName || defaultFileName,
      types: [
        {
          description: "JSON",
          accept: {
            "application/json": [".json"],
          },
        },
      ],
    };

    if (fileHandle) {
      options.startIn = fileHandle;
    }

    return options;
  };

  const pickHandle = async () => {
    if (!supportsFileSystemAccess || !fsWindow?.showSaveFilePicker) return null;
    try {
      const handle = await fsWindow.showSaveFilePicker(buildPickerOptions());
      fileHandle = handle;
      chosenFileName = handle.name;
      saveError = "";
      return handle;
    } catch (error) {
      if ((error as DOMException).name === "AbortError") {
        return null;
      }
      const message = (error as Error)?.message ?? "Unable to choose file location.";
      saveError = message;
      onSaveError?.(message);
      return null;
    }
  };

  const downloadFallback = () => {
    if (!rawConfig) return;
    const blob = new Blob([rawConfig], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = chosenFileName || defaultFileName;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleSave = async () => {
    if (!rawConfig) {
      saveError = "No config data available to save.";
      onSaveError?.(saveError);
      return;
    }

    saveError = "";
    lastSavedMessage = "";

    if (!supportsFileSystemAccess) {
      downloadFallback();
      const timestamp = new Date().toISOString();
      onSaveSuccess?.({ fileName: chosenFileName || defaultFileName, timestamp });
      lastSavedMessage = `Downloaded ${chosenFileName || defaultFileName}`;
      return;
    }

    try {
      saving = true;
      const handle = fileHandle ?? (await pickHandle());
      if (!handle) {
        saving = false;
        return;
      }

      await handle.requestPermission?.({ mode: "readwrite" });

      const writable = await handle.createWritable();
      await writable.write(rawConfig);
      await writable.close();

      const timestamp = new Date().toISOString();
      lastSavedMessage = `Saved ${handle.name} at ${new Date(timestamp).toLocaleString()}`;
      fileHandle = handle;
      onSaveSuccess?.({ fileName: handle.name, timestamp });
      saveError = "";
    } catch (error) {
      const message = (error as Error)?.message ?? "Failed to save config.";
      saveError = message;
      onSaveError?.(message);
    } finally {
      saving = false;
    }
  };
</script>

<Card.Root>
  <Card.Header>
    <Card.Title>Save Config</Card.Title>
    <Card.Description>
      {#if dirty}
        Choose where to write the modified configuration.
      {:else}
        Config matches the last saved version.
      {/if}
    </Card.Description>
  </Card.Header>
  <Card.Content class="space-y-4">
    <div class="space-y-2">
      <label class="text-sm font-medium text-zinc-600 dark:text-zinc-300" for={inputId}>File name</label>
      <input
        class="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:border-zinc-700 dark:bg-zinc-900"
        id={inputId}
        value={chosenFileName}
        placeholder={defaultFileName}
        oninput={(event) => (chosenFileName = (event.target as HTMLInputElement).value)}
      />
      {#if !supportsFileSystemAccess}
        <p class="text-xs text-zinc-500 dark:text-zinc-400">
          Your browser doesn’t support the File System Access API. We’ll download the file instead.
        </p>
      {/if}
    </div>

    <div class="flex flex-wrap items-center gap-3">
      {#if dirty}
        <Badge variant="secondary" class="bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-200">
          Unsaved changes
        </Badge>
      {:else}
        <Badge variant="secondary">Up to date</Badge>
      {/if}
    </div>

    <div class="flex flex-wrap gap-2">
      {#if supportsFileSystemAccess}
        <Button variant="outline" onclick={pickHandle} disabled={saving}>
          Choose location…
        </Button>
      {/if}
      <Button onclick={handleSave} disabled={!rawConfig || saving}>
        {saving ? "Saving…" : supportsFileSystemAccess ? "Save" : "Download"}
      </Button>
    </div>

    {#if lastSavedMessage}
      <p class="text-sm text-emerald-600 dark:text-emerald-400">{lastSavedMessage}</p>
    {/if}

    {#if saveError}
      <p class="text-sm text-red-500 dark:text-red-400">{saveError}</p>
    {/if}
  </Card.Content>
</Card.Root>
