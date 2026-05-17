import { DrizzleAdapter } from "@auth/drizzle-adapter";
import NextAuth from "next-auth";
import Nodemailer from "next-auth/providers/nodemailer";

import { db, accounts, sessions, users, verificationTokens } from "@/lib/db";
import { env } from "@/lib/env";

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: env.AUTH_SECRET,
  trustHost: true,
  adapter: DrizzleAdapter(db, {
    usersTable: users,
    accountsTable: accounts,
    sessionsTable: sessions,
    verificationTokensTable: verificationTokens,
  }),
  providers: [
    Nodemailer({
      server: {
        host: env.SMTP_HOST,
        port: env.SMTP_PORT,
        secure: false,
      },
      from: env.SMTP_FROM,
    }),
  ],
  pages: {
    signIn: "/login",
    verifyRequest: "/login?check=email",
  },
  session: { strategy: "database" },
});
