# CIO on Your Phone — Cowork Dispatch

Dispatch lets you message your CIO from your phone. The message goes to Cowork on your desktop, the CIO processes it, and the response appears on your phone.

## How It Works

1. Open the Cowork mobile app (or web interface) on your phone
2. Type your question — same as you would on desktop
3. Your desktop Cowork processes the request using your local data
4. The response appears on your phone within seconds

**Requirement:** Your desktop must be running Cowork. Dispatch routes mobile messages to the desktop app. If your laptop is closed or Cowork is quit, messages wait until it is reopened.

## Best Prompts for Mobile

Short, direct questions work best. The CIO adapts its output to be phone-readable.

| Good Mobile Prompt | What You Get |
|---|---|
| "How am I doing?" | Net worth, top allocation, worst guardrail — 3 lines |
| "Am I safe?" | Zone status for all guardrails — compact list |
| "Runway?" | Months of runway + burn rate — single number with context |
| "What changed this week?" | Key movements since last session — bullet points |
| "Should I add 10K to equities?" | Quick framework verdict + one risk flag |

## Limitations

- **No React dashboards.** Visual artifacts do not render on mobile Dispatch. The CIO uses text tables and lists instead.
- **Desktop must be on.** If Cowork is not running, requests queue until next desktop session.
- **Same data, shorter output.** Computations are identical — only the formatting adapts for phone screens.
- **File uploads not supported.** Use desktop for uploading statements or CSVs.

## Tips

- You do not need slash commands. "How am I doing?" routes to the same check as /tc:start.
- If you want the full dashboard with charts, save it for desktop. Mobile gives you the verdict.
- Dispatch works for any TimeCell command — daily check, stress test, what-if questions.
