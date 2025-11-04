<script lang="ts">
  type Primitive = string | number | boolean | null | undefined;

  const {
    data,
    depth = 2,
    currentDepth = 0,
    isLast = true,
  } = $props<{
    data?: unknown;
    depth?: number;
    currentDepth?: number;
    isLast?: boolean;
  }>();

  let items = $state<string[]>([]);
  let isArray = $state(false);
  let brackets = $state<[string, string]>(["{", "}"]);
  let collapsed = $state(false);

  const getType = (value: unknown): string => {
    if (value === null) return "null";
    return typeof value;
  };

  const stringify = (value: unknown): string => JSON.stringify(value);

  const formatPrimitive = (value: Primitive): string => {
    const type = getType(value);
    if (type === "string") return stringify(value);
    if (type === "number" || type === "bigint") return String(value);
    if (type === "boolean") return value ? "true" : "false";
    if (value === null) return "null";
    if (value === undefined) return "undefined";
    return String(value);
  };

  const toggleCollapsed = () => {
    collapsed = !collapsed;
  };

  const handleKeyPress = (event: KeyboardEvent) => {
    if (["Enter", " "].includes(event.key)) {
      event.preventDefault();
      toggleCollapsed();
    }
  };

  $effect(() => {
    const json = data;
    const type = getType(json);

    if (type === "object") {
      items = Object.keys(json as Record<string, unknown>);
      isArray = Array.isArray(json);
      brackets = isArray ? ["[", "]"] : ["{", "}"];
    } else {
      items = [];
      isArray = false;
      brackets = ["{", "}"];
    }
  });

  $effect(() => {
    collapsed = depth < currentDepth;
  });
</script>

{#if data === undefined}
  <div
    class="flex h-80 w-full items-center justify-center rounded-md border border-dashed border-zinc-200 bg-zinc-50 text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400"
  >
    <p>No JSON selected.</p>
  </div>
{:else}
  {#if !items.length}
    <span class="_jsonBkt empty" class:isArray={isArray}>
      {brackets[0]}{brackets[1]}
    </span>
    {#if !isLast}
      <span class="_jsonSep">,</span>
    {/if}
  {:else if collapsed}
    <span
      class="_jsonBkt"
      class:isArray={isArray}
      role="button"
      tabindex="0"
      onclick={toggleCollapsed}
      onkeydown={handleKeyPress}
    >{brackets[0]}...{brackets[1]}</span>
    {#if !isLast && collapsed}
      <span class="_jsonSep">,</span>
    {/if}
  {:else}
    <span
      class="_jsonBkt"
      class:isArray={isArray}
      role="button"
      tabindex="0"
      onclick={toggleCollapsed}
      onkeydown={handleKeyPress}
    >{brackets[0]}</span>
    <ul class="_jsonList">
      {#each items as key, idx}
        <li>
          {#if !isArray}
            <span class="_jsonKey">{stringify(key)}</span>
            <span class="_jsonSep">:</span>
          {/if}
          {#if getType((data as Record<string, unknown>)[key]) === "object"}
            <svelte:self
              data={(data as Record<string, unknown>)[key]}
              {depth}
              currentDepth={currentDepth + 1}
              isLast={idx === items.length - 1}
            />
          {:else}
            <span class="_jsonVal {getType((data as Record<string, unknown>)[key])}">
              {formatPrimitive((data as Record<string, unknown>)[key] as Primitive)}
            </span>
            {#if idx < items.length - 1}
              <span class="_jsonSep">,</span>
            {/if}
          {/if}
        </li>
      {/each}
    </ul>
    <span
      class="_jsonBkt"
      class:isArray={isArray}
      role="button"
      tabindex="0"
      onclick={toggleCollapsed}
      onkeydown={handleKeyPress}
    >{brackets[1]}</span>
    {#if !isLast}
      <span class="_jsonSep">,</span>
    {/if}
  {/if}
{/if}

<style>
  :global(.dark) {
    --jsonBracketHoverBackground: rgba(63, 63, 70, 0.4);
    --jsonBorderLeft: 1px dashed rgba(63, 63, 70, 0.6);
    --jsonValColor: rgba(228, 228, 231, 0.8);
  }

  :where(._jsonList) {
    list-style: none;
    margin: 0;
    padding: 0;
    padding-left: var(--jsonPaddingLeft, 1rem);
    border-left: var(--jsonBorderLeft, 1px dotted);
  }

  :where(._jsonBkt) {
    color: var(--jsonBracketColor, currentcolor);
    border-radius: 0.25rem;
    padding: 0.1rem 0.25rem;
  }

  :where(._jsonBkt):not(.empty):hover,
  :where(._jsonBkt):focus-visible {
    cursor: pointer;
    outline: none;
    background: var(--jsonBracketHoverBackground, #e5e7eb);
  }

  :where(._jsonSep) {
    color: var(--jsonSeparatorColor, currentcolor);
  }

  :where(._jsonKey) {
    color: var(--jsonKeyColor, currentcolor);
    margin-right: 0.35rem;
  }

  :where(._jsonVal) {
    color: var(--jsonValColor, #9ca3af);
  }

  :where(._jsonVal).string {
    color: var(--jsonValStringColor, #059669);
  }

  :where(._jsonVal).number {
    color: var(--jsonValNumberColor, #d97706);
  }

  :where(._jsonVal).boolean {
    color: var(--jsonValBooleanColor, #2563eb);
  }
</style>
