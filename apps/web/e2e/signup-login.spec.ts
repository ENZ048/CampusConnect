import { test, expect, request } from "@playwright/test";

const MAILHOG = "http://localhost:8025";

async function latestMessageFor(email: string) {
  const api = await request.newContext({ baseURL: MAILHOG });
  const res = await api.get("/api/v2/messages?limit=50");
  const body = await res.json();
  const item = (body.items as Array<{ Content: { Headers: { To: string[] }; Body: string } }>)
    .find((m) => m.Content.Headers.To?.[0]?.toLowerCase() === email.toLowerCase());
  expect(item, "no email found for " + email).toBeTruthy();
  return item!.Content.Body;
}

function extractLink(body: string): string {
  const decoded = body.replace(/=\r?\n/g, "").replace(/=3D/g, "=");
  const m = decoded.match(/https?:\/\/[^\s"<>]+api\/auth\/callback\/nodemailer[^\s"<>]*/);
  expect(m, "no magic link in email").toBeTruthy();
  return m![0];
}

test("user can sign up, receive a magic link, and reach the dashboard", async ({ page, browser }) => {
  const email = `test-${Date.now()}@example.com`;

  await page.goto("/signup");
  await page.fill('input[type="email"]', email);
  await page.click('button:has-text("Create account")');
  await page.waitForURL(/check=email/);

  await page.waitForTimeout(2000);

  const body = await latestMessageFor(email);
  const link = extractLink(body);

  const ctx = await browser.newContext();
  const verifyPage = await ctx.newPage();
  await verifyPage.goto(link);

  await verifyPage.waitForURL(/\/app/);
  await expect(verifyPage.locator("h1")).toHaveText("Dashboard");
});
