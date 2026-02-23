#!/usr/bin/env bash
set -euo pipefail

# Verify seed nodes are connected and serving models.
# Usage: ./scripts/verify-seed-network.sh [server-url]
# Example: ./scripts/verify-seed-network.sh https://api.idleclaw.com

SERVER="${1:-https://api.idleclaw.com}"
FAILED=0

echo "=== IdleClaw Seed Network Verification ==="
echo "Server: ${SERVER}"
echo ""

# --- 1. Health check ---
echo "--- Health Check ---"
HEALTH=$(curl -sf "${SERVER}/health" 2>/dev/null) || {
  echo "FAIL: Cannot reach ${SERVER}/health"
  exit 1
}

NODE_COUNT=$(echo "${HEALTH}" | python3 -c "import sys,json; print(json.load(sys.stdin)['node_count'])")
echo "Node count: ${NODE_COUNT}"

if [ "${NODE_COUNT}" -eq 0 ]; then
  echo "FAIL: 0 nodes connected"
  exit 1
fi
echo "OK: ${NODE_COUNT} node(s) connected"
echo ""

# --- 2. Models check ---
echo "--- Available Models ---"
MODELS=$(curl -sf "${SERVER}/api/models" 2>/dev/null) || {
  echo "FAIL: Cannot reach ${SERVER}/api/models"
  exit 1
}

MODEL_LIST=$(echo "${MODELS}" | python3 -c "import sys,json; [print(f'  - {m}') for m in json.load(sys.stdin)['models']]")
if [ -z "${MODEL_LIST}" ]; then
  echo "FAIL: No models available"
  FAILED=1
else
  echo "${MODEL_LIST}"
  echo "OK: Models available"
fi
echo ""

# --- 3. Test inference ---
echo "--- Test Inference ---"
FIRST_MODEL=$(echo "${MODELS}" | python3 -c "import sys,json; ms=json.load(sys.stdin)['models']; print(ms[0] if ms else '')")

if [ -z "${FIRST_MODEL}" ]; then
  echo "SKIP: No models to test"
  FAILED=1
else
  echo "Testing with model: ${FIRST_MODEL}"

  RESPONSE=$(curl -sf --max-time 30 \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"${FIRST_MODEL}\", \"messages\": [{\"role\": \"user\", \"content\": \"Say hello in one sentence.\"}]}" \
    "${SERVER}/api/chat" 2>/dev/null) || {
    echo "FAIL: Inference request failed or timed out"
    FAILED=1
  }

  if [ ${FAILED} -eq 0 ]; then
    # Extract text from SSE stream (data: {"choices":[{"delta":{"content":"..."}}]})
    PREVIEW=$(echo "${RESPONSE}" | head -5 | python3 -c "
import sys, json
tokens = []
for line in sys.stdin:
    line = line.strip()
    if line.startswith('data: ') and line != 'data: [DONE]':
        try:
            d = json.loads(line[6:])
            c = d.get('choices', [{}])[0].get('delta', {}).get('content', '')
            if c: tokens.append(c)
        except: pass
print(''.join(tokens)[:80] or '(empty response)')
" 2>/dev/null || echo "(could not parse response)")
    echo "Response preview: ${PREVIEW}"
    echo "OK: Inference working"
  fi
fi
echo ""

# --- Summary ---
if [ ${FAILED} -ne 0 ]; then
  echo "=== Verification FAILED ==="
  echo "Some checks failed. Review output above."
  exit 1
fi

echo "=== Verification PASSED ==="
echo "All checks passed."
exit 0
