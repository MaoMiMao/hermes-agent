#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
app_dir=${KNOWLEDGE_BASE_SOURCE_DIR:-/opt/app/llm-wiki-explorer}
image=${HERMES_WORKSPACE_IMAGE:-ds-hermes-workspace:20260822-chatfix}
base_image=${HERMES_BASE_IMAGE:-ds-hermes-agent:20260818}
artifact_context=$(mktemp -d)
trap 'rm -rf "$artifact_context"' EXIT

for required in package.json package-lock.json server.mjs; do
    if [[ ! -f "$app_dir/$required" ]]; then
        echo "Missing knowledge-base source file: $app_dir/$required" >&2
        exit 1
    fi
done

echo "Building knowledge-base frontend from $app_dir"
npm --prefix "$app_dir" run build

if [[ ! -s "$app_dir/dist/index.html" ]]; then
    echo "Frontend build did not create $app_dir/dist/index.html" >&2
    exit 1
fi

mkdir -p "$artifact_context/dist"
cp -a "$app_dir/dist/." "$artifact_context/dist/"
cp "$app_dir/server.mjs" "$artifact_context/server.mjs"

echo "Building $image from $base_image"
docker buildx build \
    --load \
    --build-context "knowledge_base_app=$artifact_context" \
    --build-arg "HERMES_BASE_IMAGE=$base_image" \
    --file "$repo_dir/Dockerfile.knowledge-base" \
    --tag "$image" \
    "$repo_dir"

docker run --rm --entrypoint sh "$image" -ec '
    test -s /opt/knowledge-base/server.mjs
    test -s /opt/knowledge-base/dist/index.html
    node --check /opt/knowledge-base/server.mjs
'

trap - EXIT
rm -rf "$artifact_context"
echo "Built self-contained image: $image"
