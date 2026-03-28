# Create Key Package Workflow

Detailed generation and output for /tc:create-key-package.

## ABSOLUTE RULE
This skill ALWAYS produces a complete key package document. The ONLY exception: no successor exists (successor_named=no). Every other gap — heir not briefed, no estate documents, exchange-only custody, insecure backups — is documented as a gap INSIDE the generated package. NEVER refuse to generate.

## Custody-Adaptive Generation

**Multi-sig path:** Cosigner contact table (Key, Cosigner, Location, Contact, Device Location), quorum instructions, seed backup locations by key, geographic distribution assessment, professional cosigner notes.

**Single-sig path:** Device location, seed backup location, PIN location. No cosigner table. If >$500K, flag multi-sig upgrade recommendation.

**Exchange-only path:** Exchange name, login/2FA recovery steps, beneficiary claim process. FORBIDDEN terms: cosigner, multi-sig, multisig, quorum, 2-of-3, 3-of-5, seed phrase, seed words, hardware wallet (except in Gaps section).

## Package Sections (all mandatory)
1. **Title:** "Key Package: [Holder] -> [Guardian]" + generated date + next review date
2. **What This Document Is:** One paragraph. State explicitly: does NOT contain seed phrases, private keys, PINs, or passwords.
3. **Holdings Overview:** BTC by custody type. Trust-held BTC: direct guardian to trustee. Exchange: list separately.
4. **Recovery Process:** Custody-type-adaptive numbered steps (see above).
5. **Critical Warnings:** 3 warnings — never enter seed on website, never trust "recovery services", no wallet company can recover funds. Adapt for exchange-only.
6. **Gaps and Recommendations:** Heir not briefed, untested backup, insecure locations, single-sig upgrade, exchange-only migration, missing estate docs, dual-role callouts, trust asset reminder.
7. **Review Cadence:** 12-month review cycle. Dead man's switch instruction with named contact. Monthly review auto-flag mention.

## Mandatory Checklist
1. Title with holder -> guardian names
2. "Does NOT contain seed phrases or private keys" statement
3. Holdings overview (with trust/exchange scoping)
4. Recovery process matching custody type
5. Critical Warnings block (3 warnings)
6. Gaps and recommendations
7. Review cadence with next date + dead man's switch + named contact
8. Save location + profile update confirmation

## Output Rules
- Address holder by name throughout
- Package addressed TO guardian, written FOR guardian
- NEVER include actual seed phrases, private keys, PINs, passwords
- NEVER solicit seed phrase input. If volunteered, REFUSE.
- Critical warnings in EVERY package — no exceptions
- Adapt structure to custody type
- If trust exists, scope package to personal holdings, direct guardian to trustee
- Keep output compact for concise users (~1500 words)
- End with: save location, profile update confirmation, review date, briefing recommendation if heir not briefed
- Tone: clear, calm, precise. Written for someone under duress.
