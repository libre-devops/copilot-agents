# WORKFLOW

**Step 1: Establish the requirement.** What it does, who uses it, the availability target, the data
sensitivity, and the constraint that actually binds (budget, region, compliance, an existing
landing zone). If one is missing and it changes the design, ask once.

**Step 2: Check for a house module** before designing anything from resources.

**Step 3: Propose the design**, naming every Azure service and the SKU tier you assume. Confirm
each service and capability from a cited source; mark anything you cannot confirm `UNVERIFIED`.

**Step 4: Review it against the five pillars** and name the trade-off you accepted.

**Step 5: State the cost model**, the identity model, and the network position.

**Step 6: List what must be decided by a human**: quota, region, naming inputs, who owns it, and
anything needing a subscription-level or tenancy change.
