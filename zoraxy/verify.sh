#!/usr/bin/env bash
# Verify the packaging contract of the built image.
#
# This checks that the app and the upstream binary still agree with each other.
# It does not check that Zoraxy works — only that what we ship is coherent:
# the wrapper passes flags the binary accepts, the image has the shape the s6
# service needs, and the schema, the startup script and the translations all
# describe the same set of options.
#
# Usage: verify.sh <image-ref>
set -euo pipefail

IMAGE="${1:?usage: verify.sh <image-ref>}"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"

RUN_SCRIPT="${APP_DIR}/rootfs/etc/services.d/zoraxy/run"
CONFIG="${APP_DIR}/config.yaml"
TRANSLATIONS="${APP_DIR}/translations/en.yaml"
UNEXPOSED="${APP_DIR}/unexposed-flags.txt"

failures=0

fail() {
    printf '  FAIL  %s\n' "$1"
    failures=$((failures + 1))
}

pass() {
    printf '  ok    %s\n' "$1"
}

# A check that silently sees nothing is worse than no check: it reports success
# for a parse that broke. Every extraction below is guarded by a plausible
# minimum, so a change in file shape fails loudly instead of passing vacuously.
expect_at_least() {
    local count="$1" minimum="$2" what="$3"
    if [ "${count}" -lt "${minimum}" ]; then
        fail "extraction of ${what} returned ${count}, expected at least ${minimum} — the parser is broken, not the app"
        return 1
    fi
    return 0
}

in_image() {
    docker run --rm --entrypoint /bin/sh "${IMAGE}" -c "$1"
}

echo "==> Image structure"

# The s6 service header is '#!/usr/bin/with-contenv bashio'. If the base image
# ever drops it the service never starts, and nothing else here would notice.
if in_image 'test -e /usr/bin/with-contenv' 2>/dev/null; then
    pass "/usr/bin/with-contenv is present"
else
    fail "/usr/bin/with-contenv is missing — the s6 service header cannot resolve"
fi

for f in run finish; do
    if in_image "test -x /etc/services.d/zoraxy/${f}" 2>/dev/null; then
        pass "/etc/services.d/zoraxy/${f} is present and executable"
    else
        fail "/etc/services.d/zoraxy/${f} is missing or not executable"
    fi
done

echo
echo "==> Flag contract"

# What the binary accepts, straight from its own usage output. Go's flag package
# exits 2 on an unknown flag after printing usage, which is what we want to read.
binary_flags="$(
    docker run --rm --entrypoint /usr/local/bin/zoraxy "${IMAGE}" -h 2>&1 |
        grep -oE '^[[:space:]]+-[a-z0-9_]+' | sed 's/[^a-z0-9_]//g' | sort -u || true
)"

# What the wrapper passes. Taken from the startup script itself rather than
# restated here, so the two cannot drift apart: adding a flag to the script is
# what puts it under test. Note the script invokes the binary more than once —
# the GeoIP update runs it separately from the exec line — so this reads every
# '-flag=' in the file. Long options are excluded by the character class: the
# second dash of '--foo=' does not match [a-z0-9_].
wrapper_flags="$(
    grep -oE '(^|[[:space:]])-[a-z0-9_]+=' "${RUN_SCRIPT}" |
        sed 's/[^a-z0-9_]//g' | sort -u || true
)"

n_binary="$(printf '%s\n' "${binary_flags}" | grep -c . || true)"
n_wrapper="$(printf '%s\n' "${wrapper_flags}" | grep -c . || true)"

if expect_at_least "${n_binary}" 20 "the binary's flags" &&
   expect_at_least "${n_wrapper}" 10 "the wrapper's flags"; then

    # The failure this exists for: the wrapper passing a flag the binary does
    # not define. The service then crash-loops on start with 'flag provided but
    # not defined', which is only visible once it is installed.
    unknown="$(comm -23 <(printf '%s\n' "${wrapper_flags}") <(printf '%s\n' "${binary_flags}"))"
    if [ -z "${unknown}" ]; then
        pass "all ${n_wrapper} flags the wrapper passes are defined by the binary"
    else
        fail "the wrapper passes flags this binary does not define:"
        printf '          %s\n' ${unknown}
        printf '        the app would crash-loop on start. Either the upstream version\n'
        printf '        in the Dockerfile is older than the wrapper expects, or a flag\n'
        printf '        was removed upstream.\n'
    fi

    # The other direction is a signal rather than a defect: upstream added flags
    # we have not looked at yet. Every flag must be either passed by the wrapper
    # or listed as a deliberate omission, so a new upstream release cannot land
    # unnoticed. This cannot fire on its own — the Dockerfile pins the upstream
    # tag, so the binary's flag set only changes when we change it.
    if [ -f "${UNEXPOSED}" ]; then
        declined="$(grep -vE '^[[:space:]]*(#|$)' "${UNEXPOSED}" | sed 's/[^a-z0-9_]//g' | sort -u)"
    else
        declined=""
    fi
    untriaged="$(
        comm -13 <(printf '%s\n' "${wrapper_flags}") <(printf '%s\n' "${binary_flags}") |
            comm -23 - <(printf '%s\n' "${declined}")
    )"
    if [ -z "${untriaged}" ]; then
        pass "every flag the binary defines is either passed or declined on purpose"
    else
        fail "the binary defines flags that are neither passed nor declined:"
        printf '          %s\n' ${untriaged}
        printf '        upstream added these. Expose them, or record why not in\n'
        printf '        %s\n' "${UNEXPOSED#"${APP_DIR}/"}"
    fi
fi

echo
echo "==> Options are described consistently"

# config.yaml, the startup script and the translations each hold their own list
# of option names. Any two of them drifting apart is invisible until a user hits
# it: an option with no description, or one that is configurable but never read.
schema_keys="$(
    sed -n '/^schema:/,/^[a-z]/p' "${CONFIG}" |
        grep -oE '^  [a-z0-9_]+:' | sed 's/[^a-z0-9_]//g' | sort -u || true
)"
translation_keys="$(
    sed -n '/^configuration:/,$p' "${TRANSLATIONS}" |
        grep -oE '^  [a-z0-9_]+:' | sed 's/[^a-z0-9_]//g' | sort -u || true
)"
# Both helpers read options by name: bashio::config 'key' and config_get 'key'.
script_keys="$(
    grep -oE "(bashio::config|config_get) '[a-z0-9_]+'" "${RUN_SCRIPT}" |
        grep -oE "'[a-z0-9_]+'" | sed 's/[^a-z0-9_]//g' | sort -u || true
)"

n_schema="$(printf '%s\n' "${schema_keys}" | grep -c . || true)"

if expect_at_least "${n_schema}" 10 "the schema's options"; then
    missing_translation="$(comm -23 <(printf '%s\n' "${schema_keys}") <(printf '%s\n' "${translation_keys}"))"
    orphan_translation="$(comm -13 <(printf '%s\n' "${schema_keys}") <(printf '%s\n' "${translation_keys}"))"
    unread_option="$(comm -23 <(printf '%s\n' "${schema_keys}") <(printf '%s\n' "${script_keys}"))"
    unschemad_read="$(comm -13 <(printf '%s\n' "${schema_keys}") <(printf '%s\n' "${script_keys}"))"

    if [ -z "${missing_translation}" ]; then
        pass "all ${n_schema} options in the schema have a description"
    else
        fail "options in the schema with no entry in translations/en.yaml:"
        printf '          %s\n' ${missing_translation}
    fi

    if [ -z "${orphan_translation}" ]; then
        pass "no description refers to an option that no longer exists"
    else
        fail "translations/en.yaml describes options that are not in the schema:"
        printf '          %s\n' ${orphan_translation}
    fi

    if [ -z "${unread_option}" ]; then
        pass "every option in the schema is read by the startup script"
    else
        fail "options in the schema that the startup script never reads:"
        printf '          %s\n' ${unread_option}
        printf '        they appear in the UI and do nothing.\n'
    fi

    if [ -z "${unschemad_read}" ]; then
        pass "the startup script reads no option that is missing from the schema"
    else
        fail "the startup script reads options that are not in the schema:"
        printf '          %s\n' ${unschemad_read}
        printf '        they can never be set, so the fallback is always used.\n'
    fi
fi

echo
if [ "${failures}" -eq 0 ]; then
    echo "==> Packaging contract holds."
    exit 0
fi
echo "==> ${failures} check(s) failed."
exit 1
