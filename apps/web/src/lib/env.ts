import { z } from "zod";

const Env = z.object({
  AUTH_SECRET: z.string().min(16),
  SMTP_HOST: z.string().default("localhost"),
  SMTP_PORT: z.coerce.number().default(1025),
  SMTP_FROM: z.string().default("no-reply@campusconnect.local"),
  API_BASE_URL: z.string().url().default("http://localhost:8000"),
  NEXTAUTH_URL: z.string().url().default("http://localhost:3000"),
});

export const env = Env.parse({
  AUTH_SECRET: process.env.AUTH_SECRET,
  SMTP_HOST: process.env.SMTP_HOST,
  SMTP_PORT: process.env.SMTP_PORT,
  SMTP_FROM: process.env.SMTP_FROM,
  API_BASE_URL: process.env.API_BASE_URL,
  NEXTAUTH_URL: process.env.NEXTAUTH_URL,
});
