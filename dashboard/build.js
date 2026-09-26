#!/usr/bin/env node
/* =========================================================================
   Baghewala Digital Twin — dashboard build
   ---------------------------------------------------------------------
   Assembles the four SELF-CONTAINED pages in dashboard/ from the shared
   parts in dashboard/src/. Nothing is fetched at runtime except Plotly
   from cdnjs, so every built page opens straight off the filesystem.

       node dashboard/build.js

   Edit dashboard/src/*, never the generated *.html in dashboard/.
   ========================================================================= */
"use strict";
const fs = require("fs");
const path = require("path");

const SRC = path.join(__dirname, "src");
const OUT = __dirname;
const read = (f) => fs.readFileSync(path.join(SRC, f), "utf8");

const PAGES = [
  { out: "index.html",       nav: "overview",    pageKey: "pgOverview",
    title: "Overview — Baghewala Digital Twin BGW-07",
    body: "page-overview.html",    js: "page-overview.js",    plotly: true,  data: false },
  { out: "console.html",     nav: "console",     pageKey: "pgConsole",
    title: "Twin console — Baghewala Digital Twin BGW-07",
    body: "page-console.html",     js: "page-console.js",     plotly: true,  data: true  },
  { out: "optimizer.html",   nav: "optimizer",   pageKey: "pgOptimizer",
    title: "Optimiser — Baghewala Digital Twin BGW-07",
    body: "page-optimizer.html",   js: "page-optimizer.js",   plotly: false, data: false },
  { out: "methodology.html", nav: "methodology", pageKey: "pgMethod",
    title: "Model basis — Baghewala Digital Twin BGW-07",
    body: "page-methodology.html", js: "page-methodology.js", plotly: false, data: false }
];

const CORE_CSS = read("core.css");
const CORE_JS  = read("core.js");
const CHROME   = read("chrome.html");
const FOOTER   = read("footer.html");
const DATA_JS  = read("data.js");
const DYNO_JS  = read("dyno-data.js");

/* Applied before first paint so the page never flashes the wrong theme. */
const PREPAINT = [
  "(function(){",
  "  var d=document.documentElement;",
  "  var q=new URLSearchParams(location.search), s={};",
  "  try{ s=JSON.parse(localStorage.getItem('bgw.v4')||'{}')||{}; }catch(e){}",
  "  var t=q.get('theme')||s.theme; d.setAttribute('data-theme', t==='dark'?'dark':'light');",
  "  var l=q.get('lang')||s.lang; d.lang=(l==='hi')?'hi':'en';",
  "})();"
].join("\n");

/* Bundled locally for an offline venue (dashboard/vendor/plotly.min.js, same
   version cdnjs served — 2.35.3). If the vendor copy is missing or fails to
   load, onerror fetches the cdnjs copy so a networked machine still works. */
const PLOTLY = '<script src="vendor/plotly.min.js" onerror="this.onerror=null;var s=document.createElement(&#39;script&#39;);s.src=&#39;https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.3/plotly.min.js&#39;;document.head.appendChild(s);"><\/script>';

const BANNER = (p) => [
  "<!--",
  "  Baghewala Digital Twin — " + p.out,
  "  GENERATED FILE. Source of truth: dashboard/src/ (core.css, core.js, chrome.html,",
  "  footer.html, " + p.body + ", " + p.js + "). Rebuild with: node dashboard/build.js",
  "-->"
].join("\n");

let total = 0;
for (const p of PAGES){
  let css = CORE_CSS;
  const pageCssFile = p.body.replace(/\.html$/, ".css");
  if (fs.existsSync(path.join(SRC, pageCssFile))) css += "\n\n/* ---- page: " + p.out + " ---- */\n" + read(pageCssFile);

  const html = [
    "<!DOCTYPE html>",
    '<html lang="en" data-theme="light">',
    "<head>",
    '<meta charset="UTF-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
    "<title>" + p.title + "</title>",
    BANNER(p),
    "<script>\n" + PREPAINT + "\n</script>",
    p.plotly ? PLOTLY : "",
    "<style>\n" + css + "\n</style>",
    "</head>",
    "<body>",
    CHROME,
    read(p.body),
    FOOTER,
    "<script>\n" + CORE_JS + "\n</script>",
    p.data ? "<script>\n" + DATA_JS + "\n</script>" : "",
    p.data ? "<script>\n" + DYNO_JS + "\n</script>" : "",
    "<script>\n" + read(p.js).replace(/__PAGE_KEY__/g, p.pageKey).replace(/__NAV_KEY__/g, p.nav) + "\n</script>",
    "</body>",
    "</html>",
    ""
  ].filter(Boolean).join("\n");

  fs.writeFileSync(path.join(OUT, p.out), html, "utf8");
  const kb = (Buffer.byteLength(html, "utf8") / 1024).toFixed(0);
  total += Number(kb);
  console.log("  " + p.out.padEnd(20) + kb.padStart(5) + " KB");
}
console.log("  " + "".padEnd(20) + String(total).padStart(5) + " KB total");
