docker exec -it bookinghub-db-1 \
pg_dump -U booking -d bookinghub -Fc \
-f /tmp/bookinghub.dump