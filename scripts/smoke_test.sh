#!/bin/bash
# HuntForge Smoke Test - Verifies a real scan works
# WARNING: This will actually scan testaspnet.vulnweb.com (safe target)

set -e

echo "========================================"
echo "  HuntForge Smoke Test"
echo "========================================"
echo ""
echo "This will run a quick scan against testaspnet.vulnweb.com"
echo "Expected time: 5-15 minutes"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

TARGET="testaspnet.vulnweb.com"
OUTPUT_DIR="output/smoke_test_$(date +%Y%m%d_%H%M%S)"

echo ""
echo "[*] Starting smoke test scan..."
echo "    Target: $TARGET"
echo "    Output: $OUTPUT_DIR"
echo ""

# Run quick scan (just phases 1-3)
if docker exec huntforge python3 huntforge.py scan "$TARGET" \
    --profile low \
    --methodology config/smoke_test_methodology.yaml 2>&1 | tee /tmp/smoke_test.log; then

    echo ""
    echo "========================================"
    echo "  Scan completed successfully!"
    echo "========================================"
    echo ""
    echo "Results:"
    echo "  Output dir: $OUTPUT_DIR"
    echo "  Findings:"
    if [ -f "$OUTPUT_DIR/processed/vulnerabilities.json" ]; then
        jq '. | length' "$OUTPUT_DIR/processed/vulnerabilities.json" 2>/dev/null || echo "  (unable to count)"
        jq -r '.[] | "    - [\(.severity)//"unknown"] \(.template//"custom") at \(.url//"unknown URL")"' "$OUTPUT_DIR/processed/vulnerabilities.json" 2>/dev/null | head -20 || true
    fi
    echo ""
    echo "To view full results:"
    echo "  jq '.' $OUTPUT_DIR/processed/vulnerabilities.json | less"
    echo ""
    echo "✓ Smoke test PASSED"
    exit 0
else
    echo ""
    echo "========================================"
    echo "  Scan FAILED"
    echo "========================================"
    echo ""
    echo "Check logs:"
    echo "  docker-compose logs huntforge | tail -100"
    echo "  cat /tmp/smoke_test.log"
    echo ""
    echo "✗ Smoke test FAILED"
    exit 1
fi
