# Natural Language Portfolio Input

Always-on CIO behavior. Detect buy/sell/receive/revalue statements conversationally.

## Process
- Parse: action (buy/sell/receive/revalue), asset, quantity, price
- Show diff table of proposed changes
- Require user "yes" before writing any changes
- Never create new entity files from NL alone — guide user through entity creation
- Hypotheticals ("what if I sold...") route to financial-reasoning skill, NOT portfolio update
- Block oversells (can't sell more than held)
