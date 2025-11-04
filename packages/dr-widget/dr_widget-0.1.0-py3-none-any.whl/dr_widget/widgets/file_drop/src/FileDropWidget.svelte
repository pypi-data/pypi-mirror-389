<script lang="ts">
  import * as Tabs from "$lib/components/ui/tabs/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Badge } from "$lib/components/ui/badge/index.js";

  import BrowseConfigsPanel from "$lib/components/file-drop/BrowseConfigsPanel.svelte";
  import LoadedConfigPreview from "$lib/components/file-drop/LoadedConfigPreview.svelte";
  import SaveConfigPanel from "$lib/components/file-drop/SaveConfigPanel.svelte";
  import {
    createFileBindingHandlers,
    type BoundFile,
    type FileBinding,
  } from "$lib/hooks/use-file-bindings";

  const { bindings, maxFiles: maxFilesProp } = $props<{
    bindings: FileBinding;
    maxFiles?: number;
  }>();

  const bindingHandlers = createFileBindingHandlers({
    bindings,
    maxFilesProp,
  });

  const parsedFiles = $derived(bindingHandlers.readBoundFiles());

  const maxFiles = 1;

  const formatSavedAt = (value: unknown): string | undefined => {
    if (typeof value === "string" && value) {
      const parsed = new Date(value);
      if (!Number.isNaN(parsed.getTime())) {
        return new Intl.DateTimeFormat(undefined, {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }).format(parsed);
      }
      return value;
    }
    return undefined;
  };

  let previewFile = $state<BoundFile | undefined>(undefined);
  let previewText = $state<string | undefined>(bindings.selected_config);
  let previewJson = $state<unknown | undefined>(() => {
    if (!bindings.selected_config) return undefined;
    try {
      return JSON.parse(bindings.selected_config);
    } catch {
      return undefined;
    }
  });
  let managerOpen = $state(false);
  let activeTab = $state("find");
  let lastLoadedFileName = $state<string | undefined>(undefined);
  let loadedConfigSummary = $state<
    | {
        name?: string;
        savedAt?: string;
        version?: string;
        rawText?: string;
        parsed?: unknown;
      }
    | undefined
  >(undefined);
  let showLoadedPreview = $state(false);
  let previewFromLoaded = $state(false);
  let loadedConfigRaw = $state<string | undefined>(undefined);
  let loadedConfigPath = $state<string | undefined>(undefined);
  let isDirty = $state(false);

  const handleSaveSuccess = ({
    fileName,
    timestamp,
  }: {
    fileName?: string;
    timestamp: string;
  }) => {
    const raw = bindings.selected_config;
    loadedConfigRaw = raw ?? "";
    isDirty = false;
    if (fileName) {
      loadedConfigPath = fileName;
      lastLoadedFileName = fileName;
    }

    const formattedSavedAt = formatSavedAt(timestamp) ?? timestamp;

    let parsed: unknown;
    if (raw) {
      try {
        parsed = JSON.parse(raw);
      } catch {
        parsed = loadedConfigSummary?.parsed;
      }
    }

    loadedConfigSummary = {
      name: fileName ?? loadedConfigSummary?.name ?? "Config saved",
      savedAt: formattedSavedAt,
      version: loadedConfigSummary?.version,
      rawText: raw ?? loadedConfigSummary?.rawText,
      parsed: parsed ?? loadedConfigSummary?.parsed,
    };

    previewFromLoaded = false;
    showLoadedPreview = false;
    bindings.error = "";
  };

  const handleSaveError = (message: string) => {
    bindings.error = message;
  };

  const computeByteSize = (input: string): number => {
    if (typeof TextEncoder !== "undefined") {
      return new TextEncoder().encode(input).byteLength;
    }
    return input.length;
  };

  const resetPreviewState = () => {
    previewFile = undefined;
    previewText = undefined;
    previewJson = undefined;
  };

  $effect(() => {
    if (!previewText) {
      previewJson = undefined;
      return;
    }

    try {
      previewJson = JSON.parse(previewText);
    } catch {
      previewJson = undefined;
    }
  });

  $effect(() => {
    if (parsedFiles.length === 0 && previewFile && !previewFromLoaded) {
      resetPreviewState();
    }
  });

  const previewSavedAt = $derived.by(() => {
    if (!previewJson || typeof previewJson !== "object") return undefined;
    return formatSavedAt((previewJson as Record<string, unknown>)["saved_at"]);
  });

  const previewVersion = $derived.by(() => {
    if (!previewJson || typeof previewJson !== "object") return undefined;
    const value = (previewJson as Record<string, unknown>)["version"];
    if (typeof value === "string" && value) return value;
    if (typeof value === "number") return String(value);
    return undefined;
  });

  $effect(() => {
    if (!managerOpen) return;
    activeTab = isDirty ? "save" : "find";
  });

  $effect(() => {
    const raw = bindings.selected_config;
    if (!raw || raw.trim().length === 0) {
      loadedConfigSummary = undefined;
      previewFromLoaded = false;
      showLoadedPreview = false;
      lastLoadedFileName = undefined;
      loadedConfigRaw = undefined;
      isDirty = false;
      if (!managerOpen) {
        resetPreviewState();
      }
      return;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      parsed = undefined;
    }

    const savedAt =
      parsed && typeof parsed === "object"
        ? formatSavedAt((parsed as Record<string, unknown>)["saved_at"])
        : undefined;

    let version: string | undefined;
    if (parsed && typeof parsed === "object") {
      const value = (parsed as Record<string, unknown>)["version"];
      if (typeof value === "string" && value) {
        version = value;
      } else if (typeof value === "number") {
        version = String(value);
      }
    }

    if (loadedConfigRaw === undefined) {
      loadedConfigRaw = raw;
      isDirty = false;
    } else {
      isDirty = raw !== loadedConfigRaw;
    }

    loadedConfigSummary = {
      name: lastLoadedFileName ?? loadedConfigSummary?.name ?? "Config loaded",
      savedAt,
      version,
      rawText: raw,
      parsed,
    };

    if (!previewFromLoaded && !managerOpen) {
      previewText = raw;
      previewJson = parsed;
    }
  });

  const handleUpload = async (files: File[]) => {
    const [file] = files;
    if (!file) return;

    const fileText = await file.text();

    await bindingHandlers.handleUpload([file]);

    previewFile = {
      name: file.name,
      size: file.size,
      type: file.type,
    };
    previewText = fileText;
    bindings.error = "";
    previewFromLoaded = false;
  };

  const handleRemove = () => {
    if (previewFromLoaded) {
      bindingHandlers.writeSelectedConfig(null);
      loadedConfigSummary = undefined;
      previewFromLoaded = false;
      showLoadedPreview = false;
      lastLoadedFileName = undefined;
      loadedConfigPath = undefined;
      bindings.error = "";
      resetPreviewState();
      loadedConfigRaw = undefined;
      isDirty = false;
      return;
    }

    if (parsedFiles.length > 0) {
      bindingHandlers.removeFile(0);
    }
    bindings.error = "";
    resetPreviewState();
    loadedConfigPath = undefined;
    loadedConfigRaw = undefined;
    isDirty = false;
  };

  const handleLoadConfig = () => {
    if (!previewText) {
      bindings.error = "Unable to load config: missing file contents.";
      return;
    }

    lastLoadedFileName = previewFile?.name ?? lastLoadedFileName;
    const summaryName = lastLoadedFileName ?? previewFile?.name ?? "Config loaded";
    let normalized: unknown = previewJson;
    if (!normalized || typeof normalized !== "object") {
      try {
        normalized = JSON.parse(previewText);
      } catch {
        bindings.error = "Config is not valid JSON.";
        return;
      }
    }

    if (!normalized || typeof normalized !== "object") {
      return;
    }

    loadedConfigSummary = {
      name: summaryName,
      savedAt: previewSavedAt,
      version: previewVersion,
      rawText: previewText,
      parsed: normalized,
    };
    bindingHandlers.writeSelectedConfig(previewText);
    loadedConfigRaw = previewText;
    loadedConfigPath = summaryName;
    isDirty = false;

    if (parsedFiles.length > 0) {
      bindingHandlers.removeFile(0);
    }

    bindings.error = "";
    resetPreviewState();
    managerOpen = false;
    showLoadedPreview = false;
    previewFromLoaded = false;
  };

  $effect(() => {
    if (managerOpen) {
      showLoadedPreview = false;

      if (!previewFile && loadedConfigSummary?.rawText) {
        previewFromLoaded = true;
        previewText = loadedConfigSummary.rawText;
        previewFile = {
          name: loadedConfigSummary.name ?? "Loaded config",
          size: computeByteSize(loadedConfigSummary.rawText),
          type: "application/json",
        };
        previewJson = loadedConfigSummary.parsed;
      }
    } else if (previewFromLoaded) {
      resetPreviewState();
      previewFromLoaded = false;
    }
  });

  const isLoadedConfigCurrent = $derived.by(() => {
    if (!loadedConfigSummary?.rawText) return false;
    if (!previewText) return false;
    return previewText === loadedConfigSummary.rawText;
  });
</script>

<div class="space-y-6">
  {#if managerOpen}
    <div class="space-y-4 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Manage Configs
          </p>
          <p class="text-sm text-zinc-500 dark:text-zinc-400">
            Load a JSON config or prepare a notebook save.
          </p>
        </div>
        <Button variant="outline" onclick={() => (managerOpen = false)}>
          Close
        </Button>
      </div>

      <Tabs.Root bind:value={activeTab}>
        <Tabs.List>
          <Tabs.Trigger value="find">Browse Configs</Tabs.Trigger>
          <Tabs.Trigger value="save">Save Config</Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="find">
          <BrowseConfigsPanel
            file={previewFile}
            rawContents={previewText}
            parsedContents={previewJson}
            savedAtLabel={previewSavedAt}
            versionLabel={previewVersion}
            dirty={isDirty}
            error={bindings.error}
            maxFiles={maxFiles}
            onUpload={handleUpload}
            onFileRejected={bindingHandlers.handleFileRejected}
            onRemove={handleRemove}
            onLoad={handleLoadConfig}
            disableLoad={isLoadedConfigCurrent}
          />
        </Tabs.Content>

        <Tabs.Content value="save">
          <SaveConfigPanel
            rawConfig={bindings.selected_config}
            defaultFileName={loadedConfigPath ?? lastLoadedFileName ?? "config.json"}
            dirty={isDirty}
            onSaveSuccess={handleSaveSuccess}
            onSaveError={handleSaveError}
          />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  {:else if showLoadedPreview && loadedConfigSummary?.rawText}
    <LoadedConfigPreview
      fileName={loadedConfigSummary.name}
      savedAtLabel={loadedConfigSummary.savedAt}
      versionLabel={loadedConfigSummary.version}
      rawContents={loadedConfigSummary.rawText}
      parsedContents={loadedConfigSummary.parsed}
      dirty={isDirty}
      onClose={() => (showLoadedPreview = false)}
      onManage={() => {
        showLoadedPreview = false;
        managerOpen = true;
      }}
    />
  {:else}
    <div
      class="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div class="space-y-1">
          <p class="text-sm font-medium text-zinc-500 dark:text-zinc-400">
            Configuration
          </p>
          {#if loadedConfigSummary}
            <p class="text-base font-semibold text-zinc-900 dark:text-zinc-100">
              {loadedConfigSummary.name}
            </p>
            {#if loadedConfigSummary.savedAt || loadedConfigSummary.version}
              <div class="flex flex-wrap items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                {#if loadedConfigSummary.savedAt}
                  <span>Saved {loadedConfigSummary.savedAt}</span>
                {/if}
                {#if loadedConfigSummary.version}
                  <Badge variant="secondary" class="px-2 py-0.5 text-[0.65rem]">
                    v{loadedConfigSummary.version}
                  </Badge>
                {/if}
                {#if isDirty}
                  <Badge variant="secondary" class="bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-200">
                    Unsaved changes
                  </Badge>
                {/if}
              </div>
            {/if}
          {:else}
            <p class="text-base text-zinc-600 dark:text-zinc-300">
              No config loaded.
            </p>
          {/if}
        </div>

        <div class="flex gap-2">
          <Button variant="outline" onclick={() => (managerOpen = true)}>
            Manage Configs
          </Button>
          {#if loadedConfigSummary?.rawText}
            <Button
              variant="outline"
              disabled={!loadedConfigSummary?.rawText}
              onclick={() => (showLoadedPreview = true)}
            >
              View Config
            </Button>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>
