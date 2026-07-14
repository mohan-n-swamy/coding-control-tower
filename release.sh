#!/usr/bin/env bash
# release.sh — cut a release and (if this project ships via Homebrew) bump its
# formula in the personal tap, in one step. Generic: drops into any repo unchanged —
# repo name, GitHub owner, and formula path are derived from `git remote origin`.
#
#   ./release.sh v0.2.0            tag, push; bump tap formula if one exists
#   ./release.sh v0.2.0 --dry-run  show what would happen, change nothing
#
# Tap clone location: $TAP_DIR, default ~/code workshop/homebrew-tap, else
# sibling dir ../homebrew-tap. No formula for this repo in the tap -> tag-only
# release (brew shipping starts when you add Formula/<repo>.rb to the tap).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

ORIGIN="$(git remote get-url origin)"
# git@github.com:owner/repo.git OR https://github.com/owner/repo(.git)
OWNER_REPO="$(printf '%s' "$ORIGIN" | sed -E 's#^(git@github\.com:|https://github\.com/)##; s#\.git$##')"
OWNER="${OWNER_REPO%%/*}"
REPO="${OWNER_REPO##*/}"
[ -n "$OWNER" ] && [ -n "$REPO" ] || { echo "cannot parse origin: $ORIGIN"; exit 1; }

for cand in "${TAP_DIR:-}" "$HOME/code workshop/homebrew-tap" "$REPO_DIR/../homebrew-tap"; do
  [ -n "$cand" ] && [ -d "$cand/Formula" ] && TAP="$cand" && break
done
FORMULA="${TAP:-/nonexistent}/Formula/$REPO.rb"

VERSION="${1:-}"
DRY=0
[ "${2:-}" = "--dry-run" ] && DRY=1
[[ "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "usage: ./release.sh vX.Y.Z [--dry-run]"; exit 2; }

[ -z "$(git status --porcelain)" ] || { echo "working tree dirty — commit or stash first"; exit 1; }
BRANCH="$(git branch --show-current)"
[ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ] || { echo "not on main/master"; exit 1; }
git fetch -q origin "$BRANCH"
[ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$BRANCH")" ] || { echo "local $BRANCH != origin — push first"; exit 1; }
git rev-parse "$VERSION" >/dev/null 2>&1 && { echo "tag $VERSION already exists"; exit 1; }

if [ "$DRY" = 1 ]; then
  echo "[dry-run] repo: $OWNER/$REPO @ $(git rev-parse --short HEAD)"
  echo "[dry-run] would tag $VERSION + push"
  if [ -f "$FORMULA" ]; then
    echo "[dry-run] would bump url+sha256 in $FORMULA and push the tap"
  else
    echo "[dry-run] no tap formula ($FORMULA) — tag-only release"
  fi
  exit 0
fi

echo "==> tagging $VERSION"
git tag "$VERSION"
git push -q origin "$VERSION"

if [ ! -f "$FORMULA" ]; then
  echo "SUCCESS · release=$VERSION (tag-only; no tap formula for $REPO)"
  echo "To ship via brew: add Formula/$REPO.rb to the tap, then re-run future releases."
  exit 0
fi

echo "==> fetching tarball sha256"
SHA=$(curl -sL --fail "https://github.com/$OWNER/$REPO/archive/refs/tags/$VERSION.tar.gz" | shasum -a 256 | cut -d' ' -f1)
[ -n "$SHA" ] || { echo "tarball fetch failed"; exit 1; }
echo "    $SHA"

echo "==> bumping formula"
cd "$TAP"
git pull -q
perl -pi -e "s|/refs/tags/v[0-9.]+\.tar\.gz|/refs/tags/$VERSION.tar.gz|; s|^(\s*sha256 \").*(\")|\${1}$SHA\${2}|" "$FORMULA"
grep -q "$VERSION" "$FORMULA" && grep -q "$SHA" "$FORMULA" || { echo "formula bump failed — inspect $FORMULA"; exit 1; }
git add "$FORMULA"
git commit -q -m "$REPO $VERSION"
git push -q

echo "SUCCESS · release=$VERSION sha256=$SHA"
echo "Users get it via: brew update && brew upgrade $REPO"
