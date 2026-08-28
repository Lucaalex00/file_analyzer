(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FileAnalyzerFilename = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  const UNSAFE_CHARS = /[^A-Za-z0-9._-]/g;

  function reportFilenameFor(originalFilename) {
    const baseName = (originalFilename || "upload").split(/[\\/]/).pop();
    const dotIndex = baseName.lastIndexOf(".");
    const stem = dotIndex > -1 ? baseName.slice(0, dotIndex) : baseName;
    const safeStem = stem.replace(UNSAFE_CHARS, "_") || "report";
    return `${safeStem}-report.pdf`;
  }

  return { reportFilenameFor };
});
