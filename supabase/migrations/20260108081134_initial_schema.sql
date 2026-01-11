create extension if not exists "vector" with schema "public";


  create table "public"."chunks" (
    "id" uuid not null default gen_random_uuid(),
    "file_id" uuid not null,
    "chunk_index" integer not null,
    "content" text not null,
    "embedding" public.vector(768),
    "chunk_metadata" jsonb not null,
    "created_at" timestamp without time zone default now()
      );


alter table "public"."chunks" enable row level security;


  create table "public"."files" (
    "id" uuid not null default gen_random_uuid(),
    "file_path" text not null,
    "file_name" text not null,
    "file_size" bigint,
    "mime_type" text not null,
    "file_hash" text not null,
    "last_modified_at" timestamp without time zone not null,
    "uploaded_at" timestamp without time zone default now(),
    "processed_at" timestamp without time zone,
    "processing_status" text default 'pending'::text,
    "metadata" jsonb not null
      );


alter table "public"."files" enable row level security;

CREATE INDEX chunks_embedding_idx ON public.chunks USING ivfflat (embedding public.vector_cosine_ops);

CREATE UNIQUE INDEX chunks_file_id_chunk_index_key ON public.chunks USING btree (file_id, chunk_index);

CREATE UNIQUE INDEX chunks_pkey ON public.chunks USING btree (id);

CREATE UNIQUE INDEX files_file_hash_key ON public.files USING btree (file_hash);

CREATE UNIQUE INDEX files_pkey ON public.files USING btree (id);

CREATE INDEX idx_chunks_file_id ON public.chunks USING btree (file_id);

alter table "public"."chunks" add constraint "chunks_pkey" PRIMARY KEY using index "chunks_pkey";

alter table "public"."files" add constraint "files_pkey" PRIMARY KEY using index "files_pkey";

alter table "public"."chunks" add constraint "chunks_file_id_chunk_index_key" UNIQUE using index "chunks_file_id_chunk_index_key";

alter table "public"."chunks" add constraint "chunks_file_id_fkey" FOREIGN KEY (file_id) REFERENCES public.files(id) ON DELETE CASCADE not valid;

alter table "public"."chunks" validate constraint "chunks_file_id_fkey";

alter table "public"."files" add constraint "files_file_hash_key" UNIQUE using index "files_file_hash_key";

grant delete on table "public"."chunks" to "anon";

grant insert on table "public"."chunks" to "anon";

grant references on table "public"."chunks" to "anon";

grant select on table "public"."chunks" to "anon";

grant trigger on table "public"."chunks" to "anon";

grant truncate on table "public"."chunks" to "anon";

grant update on table "public"."chunks" to "anon";

grant delete on table "public"."chunks" to "authenticated";

grant insert on table "public"."chunks" to "authenticated";

grant references on table "public"."chunks" to "authenticated";

grant select on table "public"."chunks" to "authenticated";

grant trigger on table "public"."chunks" to "authenticated";

grant truncate on table "public"."chunks" to "authenticated";

grant update on table "public"."chunks" to "authenticated";

grant delete on table "public"."chunks" to "service_role";

grant insert on table "public"."chunks" to "service_role";

grant references on table "public"."chunks" to "service_role";

grant select on table "public"."chunks" to "service_role";

grant trigger on table "public"."chunks" to "service_role";

grant truncate on table "public"."chunks" to "service_role";

grant update on table "public"."chunks" to "service_role";

grant delete on table "public"."files" to "anon";

grant insert on table "public"."files" to "anon";

grant references on table "public"."files" to "anon";

grant select on table "public"."files" to "anon";

grant trigger on table "public"."files" to "anon";

grant truncate on table "public"."files" to "anon";

grant update on table "public"."files" to "anon";

grant delete on table "public"."files" to "authenticated";

grant insert on table "public"."files" to "authenticated";

grant references on table "public"."files" to "authenticated";

grant select on table "public"."files" to "authenticated";

grant trigger on table "public"."files" to "authenticated";

grant truncate on table "public"."files" to "authenticated";

grant update on table "public"."files" to "authenticated";

grant delete on table "public"."files" to "service_role";

grant insert on table "public"."files" to "service_role";

grant references on table "public"."files" to "service_role";

grant select on table "public"."files" to "service_role";

grant trigger on table "public"."files" to "service_role";

grant truncate on table "public"."files" to "service_role";

grant update on table "public"."files" to "service_role";

