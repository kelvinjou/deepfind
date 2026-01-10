
  create policy "since local, give all perms"
  on "public"."chunks"
  as permissive
  for all
  to public
using (true)
with check (true);



  create policy "since local, give all perms"
  on "public"."files"
  as permissive
  for all
  to public
using (true)
with check (true);



