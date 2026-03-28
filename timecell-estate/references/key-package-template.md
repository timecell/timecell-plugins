# Key Package (Template)
layer: pack
type: access-bundle

## Identity
- name: [Descriptive name — e.g., "Primary Coldcard Recovery Package"]
- for_entity: [which wallet/exchange entity this package unlocks — by entity name]
- package_type: [full-recovery, partial-key-share, login-credentials, multisig-component]

## What's in the Package
A key package is everything a successor needs to access a specific wallet or account. Document each component:

### Component 1: Device/Access Point
- type: [hardware wallet, software wallet, exchange login, custodial service]
- location: [where the physical device is]
- access_requirement: [PIN, biometric, physical key, none]
- PIN_location: [where the PIN is stored — NOT the PIN itself]

### Component 2: Seed Phrase / Private Key
- storage_format: [24-word BIP39, SLIP-39 Shamir shares, hex private key, encrypted file]
- location: [where it's stored — "steel plate in fireproof safe", "split across 3 Shamir shares"]
- if_shamir: [how many shares needed, total shares, who holds which share]
- encryption: [is the seed/key encrypted? If so, where is the decryption key?]

### Component 3: Passphrase (if applicable)
- has_passphrase: [yes/no]
- passphrase_location: [where it's stored — separate from seed phrase for security]
- passphrase_hint: [optional — a hint that would help the successor but not an attacker]

### Component 4: Recovery Instructions
- format: [printed document, digital file, video walkthrough]
- location: [where instructions are stored]
- reading_level: [what crypto literacy is needed to follow — basic/intermediate/advanced]
- includes_step_by_step: [yes/no]
- includes_verification: [yes/no — does it explain how to verify successful recovery?]

### Component 5: Supporting Materials (if applicable)
- firmware_version: [last known firmware — some recoveries are firmware-specific]
- software_needed: [what software to download — Sparrow Wallet, Electrum, exchange app, etc.]
- network_details: [mainnet/testnet, derivation path if non-standard]
- additional_auth: [2FA backup codes, authenticator recovery, email access needed for exchange]

## Access Path
Step-by-step sequence a successor would follow:
1. [First step — e.g., "Retrieve hardware wallet from home safe"]
2. [Second step — e.g., "Get PIN from sealed envelope in safety deposit box B"]
3. [Third step — e.g., "Connect device to computer, enter PIN"]
4. [Fourth step — e.g., "Enter passphrase (stored in lawyer's sealed file)"]
5. [Fifth step — e.g., "Verify address matches entity file records"]
6. [Final step — e.g., "Transfer to successor's wallet per letter of wishes instructions"]

## Linked Parties
- primary_successor: [who this package is intended for]
- backup_successor: [who gets access if primary can't act]
- knows_about_package: [list of people who know this package exists]

## Verification
- last_verified: [date — when someone last confirmed all components are present and accessible]
- verified_by: [who verified — holder, successor, or both]
- verification_method: [physical check of all locations, test recovery on testnet, or full fire drill]
- next_verification_due: [date]
- issues_found: [any problems found during last verification]

## Security Notes
- separation: [are seed and passphrase stored in different locations? They should be.]
- tamper_evidence: [are storage methods tamper-evident? Sealed envelopes, security bags, etc.]
- geographic_distribution: [are components in different geographic locations?]
- digital_backup: [any encrypted digital copies? Where stored? What encryption?]

## Notes
[Setup history, incidents, special considerations, cross-references to other key packages if part of a multisig spanning multiple packages.]
