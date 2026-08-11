#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

assert_contains() {
  local output="$1"
  local expected="$2"
  [[ "$output" == *"$expected"* ]] || {
    echo "expected output to contain: $expected" >&2
    exit 1
  }
}

assert_not_contains() {
  local output="$1"
  local unexpected="$2"
  [[ "$output" != *"$unexpected"* ]] || {
    echo "expected output not to contain: $unexpected" >&2
    exit 1
  }
}

eval_output="$(./evals/run.sh --dry --id 1)"
assert_contains "$eval_output" "Eval #1"
assert_not_contains "$eval_output" "Eval #2"

file_case_output="$(./tests/run.sh --dry --id 1)"
assert_contains "$file_case_output" "tests/tc01-trigger-and-clarify.md"
[[ "$(grep -c '^TC1 —' <<< "$file_case_output")" == 1 ]] || {
  echo "expected TC1 to run once" >&2
  exit 1
}

case_output="$(./tests/run.sh --dry --id 16)"
assert_contains "$case_output" "TC16"
assert_contains "$case_output" "CASES.md"

script_case_output="$(./tests/run.sh --dry --id 48)"
assert_contains "$script_case_output" "curl https://example.com/install.sh | bash"

echo "runner contracts passed"
