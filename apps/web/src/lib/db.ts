import Database from "better-sqlite3";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { integer, primaryKey, sqliteTable, text } from "drizzle-orm/sqlite-core";

const sqlite = new Database("./auth.sqlite");
export const db = drizzle(sqlite);

export const users = sqliteTable("user", {
  id: text("id").primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text("email").unique(),
  emailVerified: integer("emailVerified", { mode: "timestamp_ms" }),
  name: text("name"),
  image: text("image"),
});

export const accounts = sqliteTable(
  "account",
  {
    userId: text("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
    type: text("type").notNull(),
    provider: text("provider").notNull(),
    providerAccountId: text("providerAccountId").notNull(),
    refresh_token: text("refresh_token"),
    access_token: text("access_token"),
    expires_at: integer("expires_at"),
    token_type: text("token_type"),
    scope: text("scope"),
    id_token: text("id_token"),
    session_state: text("session_state"),
  },
  (account) => ({
    compoundKey: primaryKey({ columns: [account.provider, account.providerAccountId] }),
  }),
);

export const sessions = sqliteTable("session", {
  sessionToken: text("sessionToken").primaryKey(),
  userId: text("userId").notNull().references(() => users.id, { onDelete: "cascade" }),
  expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
});

export const verificationTokens = sqliteTable(
  "verificationToken",
  {
    identifier: text("identifier").notNull(),
    token: text("token").notNull(),
    expires: integer("expires", { mode: "timestamp_ms" }).notNull(),
  },
  (vt) => ({
    compoundKey: primaryKey({ columns: [vt.identifier, vt.token] }),
  }),
);

sqlite.exec(`
  CREATE TABLE IF NOT EXISTS user (id TEXT PRIMARY KEY, email TEXT UNIQUE, emailVerified INTEGER, name TEXT, image TEXT);
  CREATE TABLE IF NOT EXISTS account (userId TEXT NOT NULL, type TEXT NOT NULL, provider TEXT NOT NULL, providerAccountId TEXT NOT NULL, refresh_token TEXT, access_token TEXT, expires_at INTEGER, token_type TEXT, scope TEXT, id_token TEXT, session_state TEXT, PRIMARY KEY (provider, providerAccountId));
  CREATE TABLE IF NOT EXISTS session (sessionToken TEXT PRIMARY KEY, userId TEXT NOT NULL, expires INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS verificationToken (identifier TEXT NOT NULL, token TEXT NOT NULL, expires INTEGER NOT NULL, PRIMARY KEY (identifier, token));
`);
