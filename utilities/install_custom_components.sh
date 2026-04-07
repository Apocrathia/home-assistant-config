#!/bin/bash

set -euo pipefail

# To be run from the root of the config folder
echo "Working out of $PWD"

# Make custom_components folder
mkdir -pv custom_components

# Enter custom_components folder
echo "Entering custom_components directory."
cd custom_components

install_custom_components() {
  local repo_url="$1"
  local repo_name
  local clone_dir
  local component_name
  local components

  repo_name="${repo_url##*/}"
  repo_name="${repo_name%.git}"
  clone_dir="${repo_name}_repo"

  git clone "$repo_url" "$clone_dir"

  # Infer integration domain from custom_components directory contents.
  mapfile -t components < <(ls -1d "${clone_dir}"/custom_components/*/ 2>/dev/null || true)
  if [[ "${#components[@]}" -ne 1 ]]; then
    echo "ERROR: Expected exactly one integration in '${clone_dir}/custom_components'"
    exit 1
  fi

  component_name="$(basename "${components[0]}")"
  rm -rf "$component_name"
  mv "${clone_dir}/custom_components/${component_name}" "$component_name"
  rm -rfv "$clone_dir"
}

# Install custom components
install_custom_components "https://github.com/Pirate-Weather/pirate-weather-ha"
install_custom_components "https://github.com/andrew-codechimp/HA-Battery-Notes"
install_custom_components "https://github.com/palfrey/ban_allowlist"
