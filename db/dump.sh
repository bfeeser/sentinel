#!/usr/bin/env sh
DUMP="mysqldump --defaults-file=db/config"

SCHEMAS=(
    sentinel
)

echo "Dumping schemas from $SCHEMAS into db/schema.sql"

$DUMP --no-data --databases "$SCHEMAS" --result-file=db/schema.sql

# remove AUTO_INCREMENT
sed -i '' 's/ AUTO_INCREMENT=[0-9]*\b//g' db/schema.sql

TABLES=(
    hosts
    patterns
    roles
    role_hosts
)

echo "Dumping data from ${TABLES[@]} into db/data.sql"

$DUMP --no-create-info sentinel "${TABLES[@]}" --result-file=db/data.sql
