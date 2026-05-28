docker exec -it bookinghub-db-1 \
pg_restore -U booking -d bookinghub \
--clean --if-exists /tmp/bookinghub.dump