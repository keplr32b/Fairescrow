# FairEscrow — AI-Arbitrated Freelance Escrow

Freelance platforms take weeks to resolve payment disputes, and the person
resolving them is often just a support agent with no real way to judge
"is this deliverable actually good." FairEscrow replaces that with GenLayer's
AI validators: they read the actual submitted work, compare it against the
original brief, and reach decentralized consensus on a fair outcome —
release, refund, or a partial split — in seconds, not weeks.

**Live contract (GenLayer Studio):** `0x51bEE7797DF86D827c426e65B52f8f74531FC25D`

## How it works

1. **Deploy** — a job is created with a client address, freelancer address,
   a natural-language brief, and an escrowed amount.
2. **Submit** — the freelancer submits a public URL to their deliverable.
3. **Resolve** — either party triggers resolution. Multiple AI validators
   independently fetch the deliverable's live content, compare it against
   the brief, and vote. Consensus is reached via GenLayer's
   `prompt_non_comparative` equivalence principle — validators agree on the
   *verdict*, not on identical wording, which is what makes consensus
   possible for a subjective judgment call.
4. **Verdict** — the contract stores the AI's reasoning on-chain, fully
   transparent to both parties.

## Why this needs GenLayer

A traditional smart contract can check "did X wei move from A to B." It
cannot check "does this deliverable meet the brief." That requires judgment,
live web access, and a way for decentralized validators to agree on something
subjective — which is exactly what GenLayer's Intelligent Contracts add on
top of a normal EVM-style chain.

## Project structure

```
fairescrow/
├── contracts/
│   └── freelance_escrow.py     # the Intelligent Contract (Python, GenVM)
└── index.html                  # standalone frontend (no build step needed)
```

## How to run the frontend

Open `index.html` in a browser — it imports `genlayer-js` directly from a
CDN via ES modules, so no `npm install` or build step is required. It's
already wired to the deployed contract address above. This repo's live demo
is hosted via GitHub Pages.

If you're forking this and pointing it at your own deployment, edit the
`CONTRACT_ADDRESS` constant near the top of the `<script>` block in
`index.html`.

## Notes on wallet handling

For demo speed, this frontend generates and persists a throwaway private key
in the browser's `localStorage` (the same pattern GenLayer's own project
boilerplate uses) rather than requiring MetaMask setup. This is fine for a
hackathon demo but should be swapped for real wallet connection
(`window.ethereum`) before any real funds are involved — the contract itself
doesn't care how the transaction is signed.

## Known scope limitations (being upfront about this)

- The contract is deployed **per job** (constructor args set the client,
  freelancer, brief, and amount at deploy time). There is no on-chain
  "create job" factory yet — that would be the natural next step for a real
  multi-job marketplace.
- No actual GEN/token transfer is wired up in `resolve()` yet — the state
  machine (`released` / `refunded` / `disputed`) is fully correct and
  verified on-chain, but production use would add `gl.transfer(...)` calls
  gated on the verdict.
- Deliverable content is fetched live at resolution time — if a freelancer
  edits the page between submission and resolution, that's a known timing
  edge case. Production version would pin submissions via IPFS/commit hash.

## Testing it end-to-end

1. Deploy `contracts/freelance_escrow.py` in GenLayer Studio.
2. Call `submit_work` from the freelancer address with any public URL.
3. Call `resolve` from either party.
4. Call `get_status` / `get_verdict` to see the outcome and the AI's
   reasoning.

This was tested with a deliverable that clearly does **not** match the
brief (a generic "Hello World" README against a "write a 500-word blog
post about AI" brief), and the AI correctly returned a `refund` verdict
with accurate reasoning — proving the judgment is genuine, not a rubber
stamp.