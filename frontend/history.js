(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FileAnalyzerHistory = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  const STORAGE_KEY = "file-analyzer-history";
  const DEFAULT_MAX_ENTRIES = 10;

  function loadHistory(storage) {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (parseError) {
      return [];
    }
  }

  function saveHistoryEntry(storage, entry, maxEntries) {
    const limit = maxEntries || DEFAULT_MAX_ENTRIES;
    const history = [entry, ...loadHistory(storage)].slice(0, limit);
    storage.setItem(STORAGE_KEY, JSON.stringify(history));
    return history;
  }

  return { loadHistory, saveHistoryEntry, STORAGE_KEY };
});
