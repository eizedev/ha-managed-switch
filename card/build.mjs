// Bundle the card into one file that the integration serves and loads in the frontend:
// custom_components/managed_switch/www/managed-switch-card.js. The bundle is committed, because
// HACS installs the integration's folder as it is in the repository; CI checks that it matches
// a fresh build. The card's version is the integration's.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const integration = new URL("../custom_components/managed_switch/", import.meta.url);
const { version } = JSON.parse(readFileSync(new URL("manifest.json", integration), "utf8"));
const outfile = fileURLToPath(new URL("www/managed-switch-card.js", integration));

await build({
  entryPoints: ["src/managed-switch-card.ts"],
  bundle: true,
  format: "esm",
  target: "es2022",
  minify: true,
  sourcemap: false,
  legalComments: "eof",
  define: { __VERSION__: JSON.stringify(version) },
  outfile,
});
console.log(`built ${outfile} ${version}`);
