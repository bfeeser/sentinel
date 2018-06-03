DUMP=mysqldump --defaults-file=db/config

SCHEMAS\=(
    sentinel
)

echo "Dumping schemas from $SCHEMAS into db/schema.sql"

DUMP --no-data --databases $SCHEMAS --result-file=schema.sql

TABLES=(
    hosts
    patterns
    roles
    role_hosts
    users
)

echo "Dumping data from $TABLES into db/data.sql"

DUMP --no-create-info $TABLES --result-file=data.sql
