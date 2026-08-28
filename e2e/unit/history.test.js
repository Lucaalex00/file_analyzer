const test = require("node:test");
const assert = require("node:assert/strict");

const { loadHistory, saveHistoryEntry } = require("../../frontend/history.js");

function makeFakeStorage() {
  const data = new Map();
  return {
    getItem: (key) => (data.has(key) ? data.get(key) : null),
    setItem: (key, value) => data.set(key, value),
  };
}

test("loadHistory returns an empty array when nothing is stored", () => {
  const storage = makeFakeStorage();

  assert.deepEqual(loadHistory(storage), []);
});

test("loadHistory returns an empty array when the stored value is corrupt JSON", () => {
  const storage = makeFakeStorage();
  storage.setItem("file-analyzer-history", "not json");

  assert.deepEqual(loadHistory(storage), []);
});

test("saveHistoryEntry prepends the new entry so the most recent is first", () => {
  const storage = makeFakeStorage();
  saveHistoryEntry(storage, { filename: "first.txt" });
  saveHistoryEntry(storage, { filename: "second.txt" });

  const history = loadHistory(storage);

  assert.equal(history.length, 2);
  assert.equal(history[0].filename, "second.txt");
  assert.equal(history[1].filename, "first.txt");
});

test("saveHistoryEntry evicts the oldest entry once maxEntries is exceeded", () => {
  const storage = makeFakeStorage();
  for (let i = 0; i < 5; i++) {
    saveHistoryEntry(storage, { filename: `file-${i}.txt` }, 3);
  }

  const history = loadHistory(storage);

  assert.equal(history.length, 3);
  assert.deepEqual(
    history.map((entry) => entry.filename),
    ["file-4.txt", "file-3.txt", "file-2.txt"],
  );
});
