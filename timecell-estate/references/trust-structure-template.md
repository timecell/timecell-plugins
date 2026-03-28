# Trust Structure (Template)
layer: pack
type: legal-entity

## Identity
- name: [Trust name — e.g., "Meridian Family Bitcoin Trust"]
- type: [revocable living trust, irrevocable trust, dynasty trust, purpose trust, etc.]
- jurisdiction: [where the trust is established — state/country]
- date_established: [date]
- governing_law: [which jurisdiction's trust law applies]

## Parties
- settlor: [who created the trust — typically the Bitcoin holder]
- trustee: [who manages the trust]
  - primary_trustee: [name, type: individual / corporate / professional]
  - successor_trustee: [who takes over if primary trustee can't serve]
  - crypto_advisor: [optional — technical advisor who assists trustee with crypto operations]
- beneficiaries:
  - [name, relationship, share/allocation, conditions]
  - [name, relationship, share/allocation, conditions]
- protector: [optional — person who can change trustees, veto distributions, etc.]

## Trust Terms
- distribution_schedule: [immediate, staged, discretionary, or per staged-inheritance strategy]
- conditions: [age gates, capability gates, hardship provisions, education requirements]
- discretionary_power: [what the trustee can decide independently vs what requires beneficiary consent]
- termination: [when/how the trust terminates — age of youngest beneficiary, fixed date, etc.]
- amendment: [can the settlor amend? Under what conditions? Revocable vs irrevocable.]

## Crypto-Specific Instructions
- custody_model: [how the trust holds Bitcoin — multisig, custodial service, hardware wallet]
- key_custody: [who holds keys on behalf of the trust]
  - key_1: [holder — e.g., "trustee's hardware wallet in trust's safety deposit box"]
  - key_2: [holder — e.g., "crypto advisor holds backup key"]
  - key_3: [holder — e.g., "Casa holds third key for inheritance protocol"]
- transaction_authority: [who can authorize Bitcoin transactions from the trust]
  - routine: [trustee alone for distributions under $X]
  - significant: [trustee + protector for distributions over $X]
  - emergency: [pre-authorized emergency fund accessible by trustee alone]
- wallet_addresses: [list of trust-owned wallet identifiers — NOT actual addresses, just references to entity files]
- security_protocol: [how the trust's crypto is secured — cold storage, multisig threshold, etc.]

## Succession Within Trust
- trustee_succession: [who becomes trustee if current trustee dies/resigns]
- key_rotation_on_trustee_change: [protocol for rotating keys when trustees change — CRITICAL for crypto trusts]
- beneficiary_death: [what happens to a beneficiary's share if they die before distribution]
- trust_failure: [what happens if the trust can't operate — fallback to direct inheritance?]

## Document References
- trust_deed: [location of trust document]
- schedule_of_assets: [location of asset list — updated when crypto moves in/out]
- letter_of_wishes: [link to letter-of-wishes entity that accompanies this trust]
- last_updated: [date of most recent trust amendment or review]
- review_frequency: [how often trust terms should be reviewed — default annual]

## Tax and Legal
- tax_id: [trust's tax identification number if applicable]
- tax_jurisdiction: [where the trust files taxes]
- annual_reporting: [what tax/legal filings are required]
- legal_counsel: [name and contact of lawyer who drafted/manages the trust]

## Verification
- last_reviewed: [date — when trust terms were last reviewed with legal counsel]
- last_asset_reconciliation: [date — when trust assets were last verified against schedule]
- next_review_due: [date]

## Notes
[Special circumstances, pending amendments, known issues with trust structure, interaction with other trusts or legal entities, cross-border considerations.]
