### Role: 
    You are now the "Lead Governance Architect" for the Stock-PEG project.
### Context: 
    The project consists of a Vue frontend, FastAPI backend, and a Feishu Bot. All governance logic is stored in the .harness/ directory.

### Objective: 
    Upgrade the current monolithic governance into a Multi-Agent Federated Model to ensure cross-stack consistency and physical environment isolation.

### Execution Steps (Execute sequentially and provide previews for each):
1. Define the Federated Constitution (AGENTS.md)
 * Implement Physical Isolation: Define three distinct nodes: Backend-Node (Python 3.13/UV), Frontend-Node (Vue 3/Vite), and Bot-Node (Feishu SDK).
 * Hard Rule: Prohibit Backend-Node from modifying the /frontend directory and vice versa.
 * Protocol: Any cross-stack changes MUST be mediated via a "Contract" file.
2. Establish the Cross-Stack Contract (Bezos Type-1 Decision)
* Add D044: Multi-Agent Synergy Protocol to decisions.md.
* Create .harness/reference/project-specific/api-contract.md.
* Enforcement: Backend changes to API schemas MUST update this contract first. Frontend agents MUST generate types based on this contract.
3. Upgrade the Automated Auditor (check-harness.py)

* Refactor the Python audit script to include Munger’s Inversion Logic (check for what shouldn't happen):

* Identity Check: Ensure every entry in progress.md has an Executed By: [Agent_ID] tag.

* Boundary Check: Throw a [FAIL] if a Backend-Node task modified frontend files.

* Evidence Link: Verify that changes to the PEG algorithm are accompanied by a physical test log in test/temp/.

4. Refactor the Public Ledger (progress.md)

* Update the completion template to require:

* Agent: [Node ID]

Contract: [Link to API Contract MD5]

* Evidence: [Path to physical log/snapshot]

### Constraint: All modifications must comply with the maintenance standards in .harness\skills\utils\maintenance\SKILL.md. Eliminate any redundant documentation identified during the transition.

