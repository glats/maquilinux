#!/usr/bin/env bash
# Server-side script: Update index.json for maquiroot.glats.org
# This runs on the web server, not the developer machine

set -euo pipefail

BASE_DIR="${1:-/var/www/maquiroot}"
INDEX_FILE="$BASE_DIR/index.json"

cd "$BASE_DIR" || exit 1

# Generate index
echo '{' > "$INDEX_FILE.tmp"
echo "  \"generated_at\": \"$(date -Iseconds)\"," >> "$INDEX_FILE.tmp"
echo '  "backups": [' >> "$INDEX_FILE.tmp"

FIRST=true
# Find all tar.xz files
for file in $(find . -name '*.tar.xz' -type f | sort); do
    [[ "$file" == ./index.json* ]] && continue
    
    filepath="${file#./}"
    dir="$(dirname "$filepath")"
    filename="$(basename "$filepath")"
    
    # Get metadata if available
    meta_file="${file%.tar.xz}.meta"
    if [[ -f "$meta_file" ]]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo 0)
        mtime=$(stat -c%Y "$file" 2>/dev/null || stat -f%m "$file" 2>/dev/null || echo 0)
        mtime_iso=$(date -d "@$mtime" -Iseconds 2>/dev/null || date -r "$mtime" -Iseconds 2>/dev/null || echo "unknown")
    else
        size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        mtime_iso="$(date -r "$file" -Iseconds 2>/dev/null || echo 'unknown')"
    fi
    
    # Add comma separator
    if ! $FIRST; then
        echo ',' >> "$INDEX_FILE.tmp"
    fi
    FIRST=false
    
    # Output entry
    cat >> "$INDEX_FILE.tmp" << ENTRY
    {
      "path": "$filepath",
      "directory": "$dir",
      "filename": "$filename",
      "size_bytes": $size,
      "modified": "$mtime_iso"
    }
ENTRY
done

echo '' >> "$INDEX_FILE.tmp"
echo '  ]' >> "$INDEX_FILE.tmp"
echo '}' >> "$INDEX_FILE.tmp"

# Atomic move
mv "$INDEX_FILE.tmp" "$INDEX_FILE"

echo "Index updated: $INDEX_FILE"
