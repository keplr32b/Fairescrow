## FairEscrow — AI-Arbitrated Freelance Escrow

Freelance platforms take weeks to resolve payment disputes, and the person
resolving them is often just a support agent with no real way to judge
"is this deliverable actually good." FairEscrow replaces that with GenLayer's
AI validators: they read the actual submitted work, compare it against the
original brief, and reach decentralized consensus on a fair outcome —
release, refund, or a partial split — with real GEN held in on-chain
custody and released automatically, no manual payout step.

** Live contract (GenLayer Studio):** '0xF25847399017C2e3bE0278dd29E55bE947989b90'

** Authorized participant accounts used in the live demo:**
- **Client:** `0xCa44BB8223A7d15e1B3777Bac319f03f9aEC9D91`
- **Freelancer:** `0xab39292830d54A3d1B26E81bA3A06eA0ea0c1F14`

## How it works

1. **Deploy** — a job is created with the client address, freelancer address,a natural-language brief, and an agreed escrow amount.

2. **Fund** — the client calls fund_escrow() (a payable method) and deposits the exact agreed amount in GEN. The contract now holds that value in custody; nothing moves until resolution.

3. **Submit** — the freelancer submits a public URL to their deliverable.

4. **Resolve** — either party triggers resolution. Multiple AI validators independently fetch the deliverable's live content, compare it against the brief, and vote. Consensus is reached via GenLayer's prompt_non_comparative equivalence principle — validators agree on the verdict, not on identical wording, which is what makes consensus possible for a subjective judgment call.

5. **Settle** — based on the agreed release_percent, the contract calls gl.get_contract_at(...).emit_transfer(...) to actually pay the freelancer and/or refund the client, in the same transaction. The verdict's reasoning is stored on-chain, fully transparent to both parties.

## Why this needs GenLayer

A traditional smart contract can check "did X wei move from A to B." It cannot check "does this deliverable meet the brief." That requires judgment,live web access, and a way for decentralized validators to agree on something subjective — which is exactly what GenLayer's Intelligent Contracts add on
top of a normal EVM-style chain, while still handling the actual value transfer deterministically in code.

## Project structure Code

```
fairescrow/
├── contracts/
│   └── freelance_escrow.py     # the Intelligent Contract (Python, GenVM)
└── index.html                  # standalone frontend (no build step needed)
```

## How to run the frontend

Open `index.html` in a browser — it imports `genlayer-js` directly from a CDN via ES modules, so no npm install or build step is required. It's already wired to the deployed contract address above. This repo's live demo is hosted via GitHub Pages.

The frontend generates and persists a throwaway private key in the browser's `localStorage` on first "Connect Wallet" — in this deployment that generated address is the **freelancer** account listed above, so `submit_work` and `resolve` can be called directly from the frontend.`fund_escrow` is client-only and was executed from the client account via GenLayer Studio, since that account isn't the one persisted in this browser session — both are real, independently controlled authorized participant accounts, matching the configuration documented above.

If you're forking this and pointing it at your own deployment, edit the `CONTRACT_ADDRESS` constant near the top of the `<script>` block in `index.html'.

## Known scope limitations (being upfront about this)

- The contract is deployed per job (constructor args set the client, freelancer, brief, and amount at deploy time). There is no on-chain "create job" factory yet — that would be the natural next step for a real multi-job marketplace.

- Deliverable content is fetched live at resolution time — if a freelancer edits the page between submission and resolution, that's a known timing edge case. Production version would pin submissions via IPFS/commit hash.

## Testing it end-to-end

1. Deploy `contracts/freelance_escrow.py` in GenLayer Studio with the client, freelancer, brief, and amount (in wei-equivalent units).

2. Call `fund_escrow` from the client address, sending exactly the agreed amount as the transaction value.

3. Call `submit_work` from the freelancer address with any public URL.

4. Call `resolve` from either party. This fetches the deliverable, gets an AI verdict, and actually transfers GEN according to that verdict.

5. Call `get_status` / `get_verdict` / `get_balance` to see the outcome, the AI's reasoning, and the contract's remaining balance (should drop to 0 after a full release or refund).

This was tested with a deliverable that clearly does **not** match the brief (a generic "Hello World" README against a "write a 500-word blog post about AI" brief).

The AI correctly returned a `refund` verdict with accurate reasoning, and the contract transferred the full escrowed amount back to the client — proving both the judgment and the settlement are genuine, not a rubber stamp.