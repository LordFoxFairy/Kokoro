#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));

function writeJson(value) {
  process.stdout.write(`${JSON.stringify(value)}\n`);
}

async function evaluateRewrites(configFile) {
  const configUrl = pathToFileURL(resolve(configFile));
  configUrl.searchParams.set("kokoro-contract-inspection", String(Date.now()));
  const loaded = await import(configUrl.href);
  const config = loaded.default;
  if (config === null || typeof config !== "object" || typeof config.rewrites !== "function") {
    throw new Error("Next config must default-export an object with rewrites()");
  }
  writeJson(await config.rewrites());
}

function exported(node, ts) {
  return (ts.getModifiers(node) ?? []).some(
    (modifier) => modifier.kind === ts.SyntaxKind.ExportKeyword,
  );
}

async function loadTypescript() {
  const typescriptUrl = pathToFileURL(
    resolve(scriptDir, "../../kokoro-web/apps/admin/node_modules/typescript/lib/typescript.js"),
  );
  const loaded = await import(typescriptUrl.href);
  return loaded.default ?? loaded;
}

function parseTypescript(absolute, source, ts) {
  const sourceFile = ts.createSourceFile(
    absolute,
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TS,
  );
  if (sourceFile.parseDiagnostics.length > 0) {
    throw new Error(`TypeScript parse failed for ${absolute}`);
  }
  return sourceFile;
}

async function inspectRouteExports(files) {
  const ts = await loadTypescript();
  const result = [];

  for (const file of files) {
    const absolute = resolve(file);
    const source = await readFile(absolute, "utf8");
    const sourceFile = parseTypescript(absolute, source, ts);

    const declarations = [];
    for (const statement of sourceFile.statements) {
      if (ts.isFunctionDeclaration(statement) && exported(statement, ts) && statement.name !== undefined) {
        declarations.push({ kind: "function", name: statement.name.text });
        continue;
      }
      if (ts.isVariableStatement(statement) && exported(statement, ts)) {
        for (const declaration of statement.declarationList.declarations) {
          if (ts.isIdentifier(declaration.name)) {
            const callable =
              declaration.initializer !== undefined &&
              (ts.isArrowFunction(declaration.initializer) || ts.isFunctionExpression(declaration.initializer));
            declarations.push({
              kind: callable ? "variable-function" : "variable-non-function",
              name: declaration.name.text,
            });
          } else {
            declarations.push({ kind: "unsupported", name: "<binding-pattern>" });
          }
        }
        continue;
      }
      if (ts.isExportDeclaration(statement)) {
        if (statement.exportClause !== undefined && ts.isNamedExports(statement.exportClause)) {
          for (const element of statement.exportClause.elements) {
            declarations.push({ kind: "reexport", name: element.name.text });
          }
        } else {
          declarations.push({ kind: "export-all", name: "*" });
        }
        continue;
      }
      if (exported(statement, ts) && "name" in statement && ts.isIdentifier(statement.name)) {
        declarations.push({ kind: "unsupported", name: statement.name.text });
      }
    }
    result.push({ exports: declarations, file: absolute });
  }
  writeJson(result);
}

async function inspectServerRoutes(file) {
  const ts = await loadTypescript();
  const absolute = resolve(file);
  const source = await readFile(absolute, "utf8");
  const sourceFile = parseTypescript(absolute, source, ts);
  const browserRouteMethods = new Set(["get", "post", "put", "patch", "delete", "head", "options"]);
  const fastifyRouteMethods = new Set([...browserRouteMethods, "trace"]);
  const routeForms = new Set([...fastifyRouteMethods, "all", "route"]);
  const routes = [];
  const unreadableMethods = [];
  const unsupportedReceivers = [];
  const routeHelpers = [];
  const pluginRegisters = [];
  const customMethodRegistrations = [];
  const methodReferences = [];
  const unsupportedBrowserMethods = [];
  const wildcards = [];

  function visit(node) {
    if (
      ts.isPropertyAccessExpression(node) &&
      ts.isIdentifier(node.expression) &&
      node.expression.text === "app"
    ) {
      if (node.name.text === "addHttpMethod") {
        customMethodRegistrations.push(node.getText(sourceFile));
      } else if (routeForms.has(node.name.text)) {
        const directRegistration = ts.isCallExpression(node.parent) && node.parent.expression === node;
        if (!directRegistration) methodReferences.push(node.getText(sourceFile));
      }
    }
    if (ts.isCallExpression(node)) {
      const expression = node.expression;
      if (ts.isIdentifier(expression) && /^register[A-Za-z]*Routes?$/u.test(expression.text)) {
        routeHelpers.push(expression.text);
      } else if (ts.isPropertyAccessExpression(expression) && expression.name.text === "register") {
        pluginRegisters.push(expression.getText(sourceFile));
      } else if (ts.isPropertyAccessExpression(expression) && routeForms.has(expression.name.text)) {
        const method = expression.name.text;
        if (!ts.isIdentifier(expression.expression) || expression.expression.text !== "app") {
          unsupportedReceivers.push(expression.getText(sourceFile));
        } else if (method === "all" || method === "route") {
          wildcards.push(method);
        } else if (!browserRouteMethods.has(method)) {
          unsupportedBrowserMethods.push(method);
        } else {
          const path = node.arguments[0];
          if (path === undefined || !ts.isStringLiteral(path)) {
            unreadableMethods.push(method);
          } else {
            routes.push({ method, path: path.text });
          }
        }
      } else if (
        ts.isElementAccessExpression(expression) &&
        expression.argumentExpression !== undefined &&
        ts.isStringLiteral(expression.argumentExpression) &&
        routeForms.has(expression.argumentExpression.text)
      ) {
        unsupportedReceivers.push(expression.getText(sourceFile));
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
  writeJson({
    routes,
    routeHelpers,
    pluginRegisters,
    customMethodRegistrations,
    methodReferences,
    unsupportedBrowserMethods,
    unreadableMethods,
    unsupportedReceivers,
    wildcards,
  });
}

async function main() {
  const [mode, ...files] = process.argv.slice(2);
  if (mode === "rewrites" && files.length === 1) {
    await evaluateRewrites(files[0]);
    return;
  }
  if (mode === "route-exports" && files.length > 0) {
    await inspectRouteExports(files);
    return;
  }
  if (mode === "server-routes" && files.length === 1) {
    await inspectServerRoutes(files[0]);
    return;
  }
  throw new Error(
    "usage: inspect_admin_browser_sources.mjs rewrites <next.config.ts> | route-exports <route.ts>... | server-routes <server.ts>",
  );
}

main().catch((error) => {
  process.stderr.write(`${error instanceof Error ? error.stack : String(error)}\n`);
  process.exitCode = 1;
});
