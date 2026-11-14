#!/usr/bin/env python3
"""
Vault and encryption invariants — four checks, each from a bug that
happened on 14 November, not from a design that might.

1. gov.accord_vault_state_resets_at_boot
   VaultProvider.boot() clears every per-user field before reading the
   new user's. Without it, backupState "yes" from one account leaked to
   the next and told a link user their keys needed reloading.

2. gov.accord_key_backup_read_is_one_place
   The read of /api/auth/key-backup lives in VaultProvider (and the
   founder-only ceremony page, which writes). A component that fetches
   the same server fact holds a second copy that outlives the user.

3. gov.accord_a_failed_check_is_not_a_no
   No gate on a destructive action may be computed from a non-ok
   response. The key-backup 401 was read as "no backup" and offered the
   prompt that would overwrite the key it was meant to restore.

4. gov.accord_encryption_prompt_is_founder_only
   Every component that names encryption or recovery reads isFounder.
   The ceremony is the founder's; the product does not prompt for it.
"""
import os
import re
import sys
from pathlib import Path

ACCORD = Path(os.environ.get("ACCORD_ROOT", "/home/bosly_accord/bosly-1.0"))
COMP = ACCORD / "components"
failures = []

# 1. VaultProvider resets per-user state at the top of boot()
vp = COMP / "VaultProvider.tsx"
if vp.exists():
    t = vp.read_text(encoding="utf-8", errors="ignore")
    boot_at = t.find("const boot = useCallback")
    if boot_at == -1:
        failures.append("1. VaultProvider has no boot()")
    else:
        head = t[boot_at:boot_at + 900]
        for field, setter in [
            ("aesKey", 'setAesKey(null)'),
            ("hasKeys", 'setHasKeys(false)'),
            ("backupState", 'setBackupState("unknown")'),
            ("userId", 'setUserId(null)'),
        ]:
            if setter not in head:
                failures.append(f"1. boot() does not reset {field} ({setter})")
else:
    failures.append("1. VaultProvider.tsx missing")

# 2. key-backup reads live in VaultProvider only
ALLOWED = {"components/VaultProvider.tsx"}
for p in COMP.rglob("*.tsx"):
    rel = str(p.relative_to(ACCORD))
    text = p.read_text(encoding="utf-8", errors="ignore")
    if "/api/auth/key-backup" in text and rel not in ALLOWED:
        failures.append(f"2. {rel} fetches key-backup outside VaultProvider")

# 3. no destructive gate set from a non-ok response
for p in COMP.rglob("*.tsx"):
    text = p.read_text(encoding="utf-8", errors="ignore")
    # a fetch whose .ok is not checked, immediately followed by a set*
    for m in re.finditer(r"const (\w+) = await fetch\((.{0,200}?)key-backup", text, re.S):
        name = m.group(1)
        window = text[m.start():m.start() + 600]
        if f"{name}.ok" not in window and f"{name}?.ok" not in window:
            failures.append(
                f"3. {p.relative_to(ACCORD)}: fetch {name} of key-backup "
                f"does not check .ok before deciding"
            )

# 4. components naming encryption/recovery read isFounder
# Only components that PROMPT about encryption or recovery are in scope.
# A pill that calls encrypt() on user data is using the vault, not
# prompting about it, and must not be founder-gated.
NAMES = re.compile(
    r"Encryption keys need reloading"
    r"|Your data isn't encrypted yet"
    r"|Restore your keys"
    r"|Complete your encryption"
    r"|needsRecovery\b"
    r"|recoverFromBackup\b"
)
for p in COMP.rglob("*.tsx"):
    text = p.read_text(encoding="utf-8", errors="ignore")
    if NAMES.search(text) and "isFounder" not in text and "VaultProvider" not in str(p):
        failures.append(f"4. {p.relative_to(ACCORD)} names encryption but not isFounder")

if failures:
    print("FAIL gov.accord_vault_and_encryption_invariants")
    for f in failures:
        print("  " + f)
    sys.exit(1)

print("PASS gov.accord_vault_and_encryption_invariants")
print("  boot resets per-user state")
print("  key-backup read is one place")
print("  no destructive gate from a non-ok response")
print("  encryption components are founder-gated")
