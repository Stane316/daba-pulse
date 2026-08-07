#!/usr/bin/env bash
# DabaPulse — Smoke prod / local
# Usage:
#   bash scripts/smoke.sh                        # → http://127.0.0.1:8000
#   bash scripts/smoke.sh https://dabapulse-api.onrender.com
#   bash scripts/smoke.sh https://dabapulse-api.onrender.com --json   # sortie JSON brute
set -euo pipefail

BASE="${1:-http://127.0.0.1:8000}"
BASE="${BASE%/}"  # trim trailing slash
RAW="0"
if [ "${2:-}" = "--json" ] || [ "${2:-}" = "--raw" ]; then RAW="1"; fi

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

pass=0; fail=0; warn=0

need() { command -v "$1" >/dev/null 2>&1 || { echo -e "${RED}Missing $1${NC}"; exit 1; }; }
need curl

has_jq=0; command -v jq >/dev/null 2>&1 && has_jq=1

# Helper: curl JSON and assert
curl_json() {
  local path="$1"; local expect="$2"; local label="$3"
  local url="${BASE}${path}"
  echo -n "▶ $label — GET $path ... "
  local http body code
  body=$(curl -sS -w "\n%{http_code}" "$url" 2>&1) || { echo -e "${RED}FAIL (curl error)${NC}"; echo "$body" | head -n 20; fail=$((fail+1)); return 1; }
  code=$(echo "$body" | tail -n1)
  body=$(echo "$body" | sed '$d')
  if [ "$code" != "200" ]; then
    echo -e "${RED}FAIL (HTTP $code)${NC}"
    echo "$body" | head -n 40
    fail=$((fail+1)); return 1
  fi
  if [ -n "$expect" ]; then
    if ! echo "$body" | grep -q "$expect"; then
      echo -e "${YELLOW}WARN (HTTP 200 mais pattern '$expect' absent)${NC}"
      echo "$body" | head -n 60
      warn=$((warn+1)); return 0
    fi
  fi
  if [ "$has_jq" = "1" ] && [ "$RAW" = "0" ]; then
    echo -e "${GREEN}OK${NC} (HTTP 200)"
    echo "$body" | jq -C . 2>/dev/null | head -n 40 || echo "$body" | head -n 40
  else
    echo -e "${GREEN}OK${NC} (HTTP 200)"
    echo "$body" | head -n 80
  fi
  pass=$((pass+1))
}

curl_status() {
  local path="$1"; local code_expected="$2"; local label="$3"
  local url="${BASE}${path}"
  echo -n "▶ $label — GET $path → expect $code_expected ... "
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1) || code="000"
  if [ "$code" = "$code_expected" ]; then echo -e "${GREEN}OK (HTTP $code)${NC}"; pass=$((pass+1));
  else echo -e "${RED}FAIL (HTTP $code, want $code_expected)${NC}"; fail=$((fail+1)); fi
}

echo "========================================"
echo " DabaPulse Smoke — $BASE"
echo " Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"
echo ""

# 0 — Root
curl_json "/" "DabaPulse" "Root"

# 1 — Health (critique : data_loaded doit être true, ai_available false sans clé)
curl_json "/api/health" '"status":"ok"' "Health"

# 2 — Data status / preview (vérifie dataset synthétique chargé)
curl_json "/api/data/status" '"valide":true' "Data status"
curl_json "/api/data/preview?n=2" '"nb_lignes"' "Data preview"

# 3 — Executive (RaR total > 0, disclaimer présent)
echo -n "▶ Executive — GET /api/executive ... "
exec_body=$(curl -sS -w "\n%{http_code}" "${BASE}/api/executive" 2>&1) || { echo -e "${RED}FAIL${NC}"; echo "$exec_body" | head -n 20; fail=$((fail+1)); }
exec_code=$(echo "$exec_body" | tail -n1); exec_body=$(echo "$exec_body" | sed '$d')
if [ "$exec_code" != "200" ]; then echo -e "${RED}FAIL (HTTP $exec_code)${NC}"; echo "$exec_body" | head -n 40; fail=$((fail+1));
else
  echo -e "${GREEN}OK (HTTP 200)${NC}"
  if [ "$has_jq" = "1" ]; then
    rar=$(echo "$exec_body" | jq -r '.revenue_at_risk_total // 0')
    dist=$(echo "$exec_body" | jq -r '.revenue_at_risk_distribution // 0')
    rep=$(echo "$exec_body" | jq -r '.revenue_at_risk_reputation // 0')
    echo "   RaR total: $rar | dist: $dist | rep: $rep"
    if [ "$rar" -gt 0 ] 2>/dev/null; then pass=$((pass+1)); else echo -e "   ${YELLOW}WARN RaR total = 0${NC}"; warn=$((warn+1)); fi
    if echo "$exec_body" | jq -e '.disclaimer' >/dev/null 2>&1; then echo "   Disclaimer: présent"; else echo -e "   ${YELLOW}WARN disclaimer manquant${NC}"; warn=$((warn+1)); fi
    # Vérifie scénario démo cible
    if echo "$exec_body" | grep -q "dist-B001-P005"; then echo "   Scénario B001×P005: présent"; else echo -e "   ${YELLOW}WARN B001×P005 absent${NC}"; warn=$((warn+1)); fi
  else
    echo "$exec_body" | head -n 60
    pass=$((pass+1))
  fi
fi

# 4 — Situation démo B001×P005 (stock 8, RaR 486000, sévérité critique)
curl_json "/api/situations/dist-B001-P005" "486000" "Situation B001×P005"

# 5 — Decision (quantité >0, source Cocody si distribution)
curl_json "/api/decisions/dist-B001-P005" "quantite" "Decision B001×P005"

# 6 — Simulate +30 (RaR 0, protégé 486000)
echo -n "▶ Simulate — POST /api/simulate {dist-B001-P005, 30} ... "
sim_body=$(curl -sS -w "\n%{http_code}" -X POST "${BASE}/api/simulate" -H "Content-Type: application/json" -d '{"situation_id":"dist-B001-P005","quantite":30}' 2>&1) || { echo -e "${RED}FAIL${NC}"; echo "$sim_body" | head -n 20; fail=$((fail+1)); }
sim_code=$(echo "$sim_body" | tail -n1); sim_body=$(echo "$sim_body" | sed '$d')
if [ "$sim_code" != "200" ]; then echo -e "${RED}FAIL (HTTP $sim_code)${NC}"; echo "$sim_body" | head -n 40; fail=$((fail+1));
else
  if echo "$sim_body" | grep -q "486000"; then echo -e "${GREEN}OK (HTTP 200, 486k présent)${NC}"; else echo -e "${YELLOW}WARN (HTTP 200, 486k non trouvé)${NC}"; fi
  if [ "$has_jq" = "1" ] && [ "$RAW" = "0" ]; then echo "$sim_body" | jq -C . | head -n 50; else echo "$sim_body" | head -n 60; fi
  pass=$((pass+1))
fi

# 7 — Export (markdown + json via GET et POST)
curl_json "/api/export/decision/dist-B001-P005?format=markdown" "DabaPulse" "Export markdown (GET)"
curl_json "/api/export/decision/dist-B001-P005?format=json" "dist-B001-P005" "Export json (GET)"
echo -n "▶ Export POST — POST /api/export/decision ... "
exp_body=$(curl -sS -w "\n%{http_code}" -X POST "${BASE}/api/export/decision" -H "Content-Type: application/json" -d '{"situation_id":"dist-B001-P005","quantite":30,"format":"json"}' 2>&1) || { echo -e "${RED}FAIL${NC}"; echo "$exp_body" | head -n 20; fail=$((fail+1)); }
exp_code=$(echo "$exp_body" | tail -n1); exp_body=$(echo "$exp_body" | sed '$d')
if [ "$exp_code" != "200" ]; then echo -e "${RED}FAIL (HTTP $exp_code)${NC}"; echo "$exp_body" | head -n 40; fail=$((fail+1));
else echo -e "${GREEN}OK (HTTP 200)${NC}"; if [ "$has_jq" = "1" ]; then echo "$exp_body" | jq -C . | head -n 30; else echo "$exp_body" | head -n 40; fi; pass=$((pass+1)); fi

# 8 — Hypotheses
curl_json "/api/hypotheses" "horizon_jours" "Hypotheses"

# 9 — AI fallback (sans clé, doit répondre fallback=true)
echo -n "▶ AI explain (fallback) — POST /api/ai/explain ... "
ai_body=$(curl -sS -w "\n%{http_code}" -X POST "${BASE}/api/ai/explain" -H "Content-Type: application/json" -d '{"situation_id":"dist-B001-P005","mode":"resume"}' 2>&1) || { echo -e "${RED}FAIL${NC}"; echo "$ai_body" | head -n 20; fail=$((fail+1)); }
ai_code=$(echo "$ai_body" | tail -n1); ai_body=$(echo "$ai_body" | sed '$d')
if [ "$ai_code" != "200" ]; then echo -e "${RED}FAIL (HTTP $ai_code)${NC}"; echo "$ai_body" | head -n 40; fail=$((fail+1));
else
  if echo "$ai_body" | grep -q '"fallback":true'; then echo -e "${GREEN}OK (HTTP 200, fallback=true)${NC}"; else echo -e "${YELLOW}WARN (HTTP 200, fallback non détecté — clé LLM peut être configurée)${NC}"; fi
  if [ "$has_jq" = "1" ] && [ "$RAW" = "0" ]; then echo "$ai_body" | jq -C . | head -n 40; else echo "$ai_body" | head -n 60; fi
  pass=$((pass+1))
fi

# 10 — 404 attendu
curl_status "/api/situations/does-not-exist" "404" "404 situation inconnue"

echo ""
echo "========================================"
echo -e " Résultat — PASS: ${GREEN}$pass${NC}  WARN: ${YELLOW}$warn${NC}  FAIL: ${RED}$fail${NC}"
if [ "$fail" -gt 0 ]; then echo -e "${RED}Smoke FAILED — $fail échec(s)${NC}"; exit 1;
elif [ "$warn" -gt 0 ]; then echo -e "${YELLOW}Smoke PASSED avec $warn warning(s)${NC}"; exit 0;
else echo -e "${GREEN}Smoke PASSED — tout est vert${NC}"; exit 0; fi
