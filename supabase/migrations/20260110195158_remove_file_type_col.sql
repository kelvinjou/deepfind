drop index if exists "public"."idx_files_type";

alter table "public"."files" drop column "file_type";


