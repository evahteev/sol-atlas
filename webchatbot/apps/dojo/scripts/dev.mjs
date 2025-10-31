#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const rootDir = process.cwd();

const truthy = new Set(["1", "true", "yes", "on"]);
const wantsHttps = truthy.has((process.env.NEXT_DEV_HTTPS ?? "").toLowerCase());

function runOrExit(command, args, options = {}) {
  const result = spawnSync(command, args, { stdio: "inherit", ...options });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function ensureCertificates() {
  const certDir = path.join(rootDir, ".next-dev-certs");
  const certPath = path.join(certDir, "localhost.pem");
  const keyPath = path.join(certDir, "localhost-key.pem");

  if (!existsSync(certDir)) {
    mkdirSync(certDir, { recursive: true });
  }

  if (existsSync(certPath) && existsSync(keyPath)) {
    return { certPath, keyPath };
  }

  return generateCertificates(certPath, keyPath);
}

async function generateCertificates(certPath, keyPath) {
  const selfsignedMod = await import("selfsigned");
  const generator = selfsignedMod.generate ?? selfsignedMod.default?.generate ?? selfsignedMod.default;

  if (typeof generator !== "function") {
    throw new Error("Unable to load selfsigned.generate");
  }

  const attrs = [{ name: "commonName", value: "localhost" }];
  const options = {
    days: 365,
    algorithm: "sha256",
    keySize: 2048,
    extensions: [
      {
        name: "subjectAltName",
        altNames: [
          { type: 2, value: "localhost" },
          { type: 7, ip: "127.0.0.1" },
          { type: 7, ip: "0.0.0.0" },
        ],
      },
    ],
  };

  const pems = generator(attrs, options);
  writeFileSync(certPath, pems.cert);
  writeFileSync(keyPath, pems.private);

  console.log(`Created self-signed certificate for https dev server: ${certPath}`);

  return { certPath, keyPath };
}

async function main() {
  runOrExit("pnpm", ["run", "generate-content-json"]);

  const nextArgs = ["exec", "next", "dev"];

  if (wantsHttps) {
    const { certPath, keyPath } = await ensureCertificates();
    nextArgs.push("--experimental-https", "--experimental-https-key", keyPath, "--experimental-https-cert", certPath);
    console.log("Starting Next.js dev server with HTTPS enabled");
  } else {
    console.log("Starting Next.js dev server over HTTP. Set NEXT_DEV_HTTPS=1 to enable HTTPS.");
  }

  const child = spawn("pnpm", nextArgs, {
    stdio: "inherit",
    env: process.env,
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
    } else {
      process.exit(code ?? 0);
    }
  });
}

await main();
