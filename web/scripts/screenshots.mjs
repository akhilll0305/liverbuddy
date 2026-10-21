// Capture UI screenshots (README + visual QA). Requires `liverbuddy serve` running and the UI built.
// Usage: node scripts/screenshots.mjs [baseUrl] [outDir]
import { chromium } from "playwright";

const base = process.argv[2] ?? "http://localhost:8000";
const out = process.argv[3] ?? "../docs/screenshots";
const pages = [
  ["landing", "/", 2600],
  ["dashboard", "/app", 3500],
  ["check", "/app/check", 1500],
  ["meds", "/app/meds", 1500],
  ["chat", "/app/chat", 1500],
  ["labs", "/app/labs", 1200],
  ["meals", "/app/meals", 1200],
  ["ask", "/app/ask", 1200],
];

const browser = await chromium.launch({ channel: "chrome" });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
const page = await ctx.newPage();
page.on("pageerror", (e) => console.error("PAGE ERROR", e.message));

const { access_token } = await (await fetch(`${base}/api/auth/demo`, { method: "POST" })).json();
await page.goto(base);
await page.evaluate((t) => localStorage.setItem("lb_token", t), access_token);

for (const [name, path, wait] of pages) {
  if (name === "landing") await page.evaluate(() => localStorage.removeItem("lb_token"));
  else await page.evaluate((t) => localStorage.setItem("lb_token", t), access_token);
  await page.goto(base + path, { waitUntil: "networkidle" });
  if (name === "check") await page.getByRole("button", { name: "Load an example" }).click(), await page.getByRole("button", { name: "Calculate" }).click();
  if (name === "meds") await page.getByPlaceholder("Search a medicine or supplement…").fill("Crocin");
  await page.waitForTimeout(wait);
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: name !== "chat" });
  console.log("saved", name);
}
if (!process.env.SKIP_AI) {
  // live AI interactions (need the LLM provider running)
  await page.goto(base + "/app/chat", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Lipitor and Crocin/ }).click();
  await page.getByText(/tool call/).first().waitFor({ timeout: 180_000 });
  await page.getByText(/tool call/).first().click();
  await page.waitForTimeout(1200);
  await page.screenshot({ path: `${out}/chat-answer.png` });
  console.log("saved chat-answer");

  await page.goto(base + "/app/meals", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: "Chicken biryani with raita and a cola" }).click();
  await page.getByRole("button", { name: "Analyse meal" }).click();
  await page.getByText("Liver-diet score").waitFor({ timeout: 180_000 });
  await page.waitForTimeout(2200);
  await page.screenshot({ path: `${out}/meals-result.png`, fullPage: true });
  console.log("saved meals-result");
}

await page.setViewportSize({ width: 390, height: 844 });
await page.goto(base + "/app", { waitUntil: "networkidle" });
await page.waitForTimeout(3000);
await page.screenshot({ path: `${out}/mobile-dashboard.png` });
console.log("saved mobile-dashboard");
await browser.close();
