#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
image=${HERMES_WORKSPACE_IMAGE:-ds-hermes-workspace:20260822-chatfix}
output=${1:-"$(pwd)/ds-hermes-workspace-20260822-chatfix-linux-amd64.tar.gz"}
output_dir=$(dirname "$output")
output_name=$(basename "$output")

docker image inspect "$image" >/dev/null
mkdir -p "$output_dir"

tmp_output="$output.part"
trap 'rm -f "$tmp_output"' EXIT

echo "Exporting $image to $output"
docker save "$image" | gzip -1 >"$tmp_output"
mv "$tmp_output" "$output"
(cd "$output_dir" && sha256sum "$output_name" >"$output_name.sha256")

copy_release_file() {
    local source=$1
    local target=$2
    if [[ ! -e "$target" ]] || ! cmp -s "$source" "$target"; then
        cp "$source" "$target"
    fi
}

copy_release_file "$repo_dir/docker-compose.yml" "$output_dir/docker-compose.yml"
copy_release_file "$repo_dir/DEPLOYMENT.knowledge-base.zh-CN.md" "$output_dir/DEPLOYMENT.zh-CN.md"
copy_release_file "$repo_dir/knowledge-base.env.example" "$output_dir/.env.example"
trap - EXIT

echo "Exported image bundle: $output"
echo "Checksum: $output.sha256"
echo "Deployment files: $output_dir/docker-compose.yml, $output_dir/.env.example"
