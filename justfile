# Libre DevOps Copilot agents task runner. Run `just` to list recipes.
#
# Unlike the Terraform module repos this one has no PowerShell engine and no cloud dependency, so
# the recipes stay on the default shell and everything runs offline. `uv` resolves the Python
# dependencies from the PEP 723 headers in tools/*.py, so there is no environment to create.
#
# Install just with either:
#   brew install just
#   uv tool add rust-just     # then call recipes as: uv run just <recipe>

# List available recipes.
default:
    just --list

# Compose every agent into rendered/. Fails if any platform limit is breached.
render *args:
    uv run tools/render.py {{args}}

# Validate rendered/ against the vendored schema plus the semantics the schema cannot express.
lint *args:
    uv run tools/lint.py {{args}}

# Regenerate the app package icons from source.
icons:
    uv run tools/make_icons.py

# Build the uploadable app packages into dist/.
package:
    uv run tools/render.py --package

# The full offline gate, and exactly what CI runs. Run this before calling anything done.
validate:
    uv run tools/render.py --check
    uv run tools/lint.py

# Refresh the vendored declarative agent schema from Microsoft, then re-lint against it.
# Review the diff: a schema bump usually means the version constant in tools/render.py moves too.
update-schema:
    curl -sS -fL -o schema/declarative-agent-v1.8.schema.json \
        https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json
    uv run tools/lint.py

# Remove build output. rendered/ is committed, so it is deliberately left alone.
clean:
    rm -rf dist
