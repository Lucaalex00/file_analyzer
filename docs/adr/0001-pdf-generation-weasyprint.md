# 0001 — PDF generation via WeasyPrint

## Status

Accepted

## Context

The service needs to turn a structured `AnalysisResult` into a downloadable PDF
report. The two mainstream Python options are ReportLab (imperative, low-level
drawing API) and WeasyPrint (renders HTML/CSS to PDF).

## Decision

Use WeasyPrint with a Jinja2 HTML template. Report layout (headings, red-flag
cards, severity colors) is expressed as ordinary HTML/CSS, which is faster to
write and change than ReportLab's canvas-drawing API, and keeps the report's
visual design in one template file instead of scattered across Python code.

## Consequences

WeasyPrint depends on system libraries (Pango, Cairo, GDK-Pixbuf) that must be
installed in any environment that runs it — handled in `Dockerfile` and in the
CI workflow's `apt-get install` step. This is a known friction point on Azure
Functions' Consumption plan, which restricts custom system dependencies more
than a plain container; if Fase 2 deployment work runs into this, the fallback
is `xhtml2pdf`, a pure-Python HTML-to-PDF renderer with no native dependencies,
at the cost of weaker CSS support.
