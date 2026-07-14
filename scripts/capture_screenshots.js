const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const OUT = path.join(__dirname, "..", "docs", "screenshots");
const BASE = "http://127.0.0.1:8504";

async function appFrame(page) {
  // Streamlit puts the app in an iframe after boot
  const frame = page.frameLocator('iframe[title="streamlitApp"]').first();
  return frame;
}

async function waitReady(page) {
  await page.goto(BASE, { waitUntil: "networkidle", timeout: 180000 });
  // Allow cold Python script run
  for (let i = 0; i < 60; i++) {
    const body = await page.content();
    if (body.includes("streamlitApp") || body.includes("Pipeline Health")) {
      break;
    }
    await page.waitForTimeout(3000);
  }
  await page.waitForTimeout(5000);
  // Prefer iframe if present
  try {
    const frame = await appFrame(page);
    await frame.locator("body").waitFor({ timeout: 60000 });
  } catch (_) {
    // Fall through — screenshot the outer page
  }
}

async function shot(page, name) {
  const target = path.join(OUT, name);
  // Try full page from main frame; iframe screenshots via page
  await page.screenshot({ path: target, fullPage: false });
  console.log("wrote", target);
}

async function clickNav(page, label) {
  const frame = page.frameLocator('iframe[title="streamlitApp"]').first();
  try {
    await frame.getByText(label, { exact: true }).first().click({ timeout: 15000 });
  } catch (_) {
    await page.getByText(label, { exact: true }).first().click({ timeout: 15000 });
  }
  await page.waitForTimeout(3500);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await waitReady(page);
  await shot(page, "health-board.png");
  await clickNav(page, "Metrics Explorer");
  await shot(page, "metrics-explorer.png");
  await clickNav(page, "Solution");
  await shot(page, "solution.png");
  await browser.close();
  console.log("wrote screenshots to", OUT);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
