import { registerOTel } from "@vercel/otel";

export function register() {
  registerOTel({
    serviceName: process.env.OTEL_SERVICE_NAME_WEB ?? "campusconnect-web",
  });
  if (process.env.NEXT_RUNTIME === "nodejs") {
    require("./sentry.server.config");
  }
  if (process.env.NEXT_RUNTIME === "edge") {
    require("./sentry.server.config");
  }
}
