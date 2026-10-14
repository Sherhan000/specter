import fs from 'fs'
import path from 'path'

let run, close

const schema = `
create table if not exists files (
  id text primary key,
  owner_id int,
  mime text not null,
  size int not null,
  data bytea not null,
  created_at timestamptz default now()
);
create table if not exists users (
  id serial primary key,
  kind text not null default 'user',
  email text unique,
  google_id text unique,
  name text not null,
  username text unique,
  avatar text,
  bio text default '',
  adult boolean default false,
  banned boolean default false,
  created_at timestamptz default now(),
  last_seen timestamptz default now()
);
create table if not exists chats (
  id serial primary key,
  type text not null,
  title text,
  avatar text,
  owner_id int references users(id) on delete set null,
  dm_key text unique,
  invite text unique,
  settings jsonb not null default '{}',
  created_at timestamptz default now()
);
create table if not exists members (
  chat_id int references chats(id) on delete cascade,
  user_id int references users(id) on delete cascade,
  role text not null default 'member',
  muted_until timestamptz,
  last_read int default 0,
  joined_at timestamptz default now(),
  primary key (chat_id, user_id)
);
create table if not exists bans (
  chat_id int references chats(id) on delete cascade,
  user_id int references users(id) on delete cascade,
  primary key (chat_id, user_id)
);
create table if not exists messages (
  id serial primary key,
  chat_id int references chats(id) on delete cascade,
  user_id int references users(id) on delete cascade,
  kind text not null default 'text',
  body text default '',
  meta jsonb not null default '{}',
  reply_to int,
  edited boolean default false,
  created_at timestamptz default now()
);
create index if not exists messages_chat on messages(chat_id, id desc);
create table if not exists packs (
  id serial primary key,
  owner_id int references users(id) on delete cascade,
  title text not null,
  created_at timestamptz default now()
);
create table if not exists stickers (
  id serial primary key,
  pack_id int references packs(id) on delete cascade,
  file_id text not null,
  emoji text default ''
);
create table if not exists saved_packs (
  user_id int references users(id) on delete cascade,
  pack_id int references packs(id) on delete cascade,
  primary key (user_id, pack_id)
);
create table if not exists codes (
  email text primary key,
  hash text not null,
  expires timestamptz not null,
  tries int default 0
);
create table if not exists ai_samples (
  id serial primary key,
  text text not null,
  created_at timestamptz default now()
);
create table if not exists kv (
  k text primary key,
  v jsonb not null
);
`

export async function initDb() {
  if (process.env.DATABASE_URL) {
    const { default: pg } = await import('pg')
    const pool = new pg.Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_URL.includes('localhost') ? false : { rejectUnauthorized: false },
      max: 10
    })
    run = (s, p) => pool.query(s, p)
    close = () => pool.end()
    await pool.query(schema)
  } else {
    const { PGlite } = await import('@electric-sql/pglite')
    const dir = path.resolve('data/pg')
    fs.mkdirSync(dir, { recursive: true })
    const db = new PGlite(dir)
    run = (s, p) => db.query(s, p)
    close = () => db.close()
    await db.exec(schema)
    console.log('local db: data/pg')
  }
}

export const q = async (s, p = []) => (await run(s, p)).rows
export const one = async (s, p = []) => (await run(s, p)).rows[0]
export const shut = () => close?.()

export async function getKv(k, def) {
  const r = await one('select v from kv where k=$1', [k])
  return r ? r.v : def
}

export async function setKv(k, v) {
  await q('insert into kv(k,v) values($1,$2) on conflict (k) do update set v=$2', [k, JSON.stringify(v)])
}
