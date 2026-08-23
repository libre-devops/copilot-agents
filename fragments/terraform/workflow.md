# WORKFLOW

Follow these steps in order when asked to write or change Terraform.

**Step 1: Establish scope.** Decide whether the request is a reusable module or a workspace root.
If the request does not say and the answer changes the file layout, ask once.

**Step 2: Confirm the resource surface.** Use `WebSearch` against the registry and provider
documentation to confirm every resource type and argument you intend to use exists in the pinned
provider version. Do not emit an argument you have not confirmed.

**Step 3: Emit the files.** Produce each required file in full, in the file split above, in the
argument order above. State the provider versions you pinned and why.

**Step 4: State the gates.** List the commands the user must run: `terraform fmt -recursive`,
`terraform validate`, `tflint`, `terraform test`, and a `trivy config` scan. Say plainly that you
have not run them.
