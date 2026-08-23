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

# Scaffold a new branding profile from the example, with its own app id namespace. The new file is
# gitignored by default, so an internal profile cannot reach a public repository by accident.
new-profile name:
    @test ! -e profiles/{{name}}.yaml || (echo "profiles/{{name}}.yaml already exists"; exit 1)
    @ns=$(python3 -c "import uuid,sys; print(uuid.uuid5(uuid.NAMESPACE_DNS, sys.argv[1]))" "{{name}}.copilot-agents"); \
      sed -e "s/^id: example$/id: {{name}}/" -e "s/^app_id_namespace: .*/app_id_namespace: $ns/" \
          profiles/example.yaml > profiles/{{name}}.yaml; \
      echo "Created profiles/{{name}}.yaml with app id namespace $ns"; \
      echo "Edit its tokens and publisher block, then run: just package {{name}}"; \
      echo "It is gitignored. To publish it, add an exception to .gitignore deliberately."

# Refresh the vendored declarative agent schema from Microsoft, then re-lint against it.
update-schema:
    curl -sS -fL -o schema/declarative-agent-v1.8.schema.json \
        https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json
    uv run tools/lint.py

# Remove build output. rendered/ is committed, so it is deliberately left alone.
clean:
    rm -rf dist build
