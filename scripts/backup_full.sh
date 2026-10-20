#!/bin/bash
# Full Bosly backup — code, data, database, config

BACKUP_DIR="/home/bosly_accord/backups/full"
DATE=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting full backup..."

# 1. Backup code
tar -czf "$BACKUP_DIR/code-$DATE.tar.gz" \
  --exclude="node_modules" \
  --exclude=".next" \
  --exclude=".git" \
  --exclude="*.log" \
  -C /home/bosly_accord/bosly-1.0 .

# 2. Backup data — only what cannot be regenerated: uploads (client
# files) and copilot-knowledge (state). Exclude logs and agent-sessions,
# which were 370 MB of noise per day.
tar -czf "$BACKUP_DIR/data-$DATE.tar.gz" \
  --exclude="*node_modules*" \
  --exclude="*_snapshots*" \
  --exclude="*test-results*" \
  --exclude="*test-training.jsonl" \
  --exclude="*logs*" \
  --exclude="*agent-sessions*" \
  --exclude="*audit-2026*" \
  --exclude="*.log" \
  --exclude="*.log.alerts" \
  --exclude="*gov-interactions.jsonl" \
  -C /mnt/bosly/bosly-data .

# 3. Backup environment
cp /home/bosly_accord/bosly-1.0/.env.production "$BACKUP_DIR/env-$DATE.production" 2>/dev/null || true

# 4. Backup database (SQLite for Keep, dump for Bosly)
cp /home/bosly_accord/bosly-keep/prisma/dev.db "$BACKUP_DIR/keep-dev-$DATE.db" 2>/dev/null || true
# The bosly_accord role has peer auth, so this works under cron with
# no password. No "|| true": an empty dump must fail loudly.
pg_dump -d bosly | gzip > "$BACKUP_DIR/bosly-db-$DATE.sql.gz"
if [ ! -s "$BACKUP_DIR/bosly-db-$DATE.sql.gz" ] || [ "$(stat -c%s "$BACKUP_DIR/bosly-db-$DATE.sql.gz")" -lt 1024 ]; then
  echo "[$(date)] FAIL: database dump is empty or under 1 KB" >&2
  exit 1
fi

# 5. Keep only last 7 days of backups
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "[$(date)] Full backup complete"
ls -lh "$BACKUP_DIR/"
