import { readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

const serverDir = path.join(process.cwd(), "dist", "server");
const workerEntry = path.join(serverDir, "index.js");
const rscEntry = path.join(serverDir, "rsc-index.js");
const ssrEntry = path.join(serverDir, "ssr", "index.js");

await rename(workerEntry, rscEntry);

const ssrSource = await readFile(ssrEntry, "utf8");
await writeFile(ssrEntry, ssrSource.replace('import("../index.js")', 'import("../rsc-index.js")'));

await writeFile(
  workerEntry,
  [
    'import app from "./ssr/index.js";',
    "",
    "export default {",
    "  fetch(request, env, ctx) {",
    "    return app.fetch(request, env, ctx);",
    "  },",
    "};",
    "",
  ].join("\n"),
);
