#!/usr/bin/env sh
DUMP="mysqldump --defaults-file=db/config"

SCHEMAS=(
    sentinel
)

echo "Dumping schemas from $SCHEMAS into db/schema.sql"

$DUMP --no-data --databases "$SCHEMAS" \
    | sed 's/AUTO_INCREMENT=[0-9]* //g' \
    | sed '/Dump completed on/d' > db/schema.sql


TABLES=(
    hosts
    patterns
    roles
    role_hosts
)

echo "Dumping data from ${TABLES[@]} into db/data.sql"

$DUMP --no-create-info sentinel "${TABLES[@]}" \
    | sed '/Dump completed on/d' > db/data.sql
