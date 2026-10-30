import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export async function resolve(specifier, context, nextResolve) {
  if (specifier.startsWith(".")) {
    const parent = context.parentURL ? fileURLToPath(context.parentURL) : process.cwd();
    const base = join(dirname(parent), specifier);
    for (const ext of ["", ".ts", ".js", ".mjs"]) {
      if (existsSync(base + ext)) {
        return { url: pathToFileURL(base + ext).href, shortCircuit: true };
      }
    }
  }
  return nextResolve(specifier, context);
}
