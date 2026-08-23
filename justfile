# Libre DevOps Copilot agents task runner. Run `just` to list recipes.
#
# Unlike the Terraform module repos this one has no PowerShell engine and no cloud dependency, so
# the recipes stay on the default shell and everything runs offline. `uv` resolves the Python
# dependencies from the PEP 723 headers in tools/*.py, so there is no environment to create.
#
# Most recipes take a branding PROFILE as their first argument, defaulting to `default`:
#
#   just package                 # the Libre DevOps packages, into dist/
#   just package example         # the same agents branded as the example profile, into dist/example/
#
# Install just with either:
#   brew install just
#   uv tool add rust-just     # then call recipes as: uv run just <recipe>

# List available recipes.
default:
    just --list

# Compose agents into rendered/ (default profile) or build/<profile>/. Extra args pass through,
# for example: just render default terraform-author --with-embedded-knowledge
render profile="default" *args:
    uv run tools/render.py --profile {{profile}} {{args}}

# Validate a rendered tree against the vendored schema plus the semantics it cannot express.
lint profile="default" *args:
    uv run tools/lint.py --profile {{profile}} {{args}}

# Regenerate the app package icons in the profile's brand colour.
icons profile="default":
    uv run tools/make_icons.py --profile {{profile}}

# Build the uploadable app packages. dist/ for the default profile, dist/<profile>/ otherwise.
package profile="default":
    uv run tools/render.py --profile {{profile}} --package

# The full offline gate for the default profile, and exactly what CI runs.
validate:
    uv run tools/render.py --check
    uv run tools/lint.py

# Render and lint any other profile. --check does not apply: rendered/ belongs to the default
# profile, and everything else renders into gitignored build/.
check profile:
    uv run tools/render.py --profile {{profile}}
    uv run tools/lint.py --profile {{profile}}

# List the branding profiles this checkout can build.
profiles:
    @for f in profiles/*.yaml; do n=$(basename "$f" .yaml); printf '  %-12s %s\n' "$n" "$(grep -m1 'brand_name:' "$f" | cut -d: -f2- | xargs)"; done

# Create a branding profile. Asks for each value with a sensible default: press Enter to accept.
# The new file is gitignored, so an internal profile cannot reach a public repository by accident.
new-profile name:
    uv run tools/new_profile.py {{name}}

# Same, but take every default without asking. Useful in a script.
new-profile-quick name:
    uv run tools/new_profile.py {{name}} --defaults

# Refresh the knowledge packs agents upload into Agent Builder, from knowledge/sources.yaml.
update-knowledge:
    uv run tools/fetch_knowledge.py

# Refresh the vendored declarative agent schema from Microsoft, then re-lint against it.
update-schema:
    curl -sS -fL -o schema/declarative-agent-v1.8.schema.json \
        https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json
    uv run tools/lint.py

# Remove build output. rendered/ is committed, so it is deliberately left alone.
clean:
    rm -rf dist build
