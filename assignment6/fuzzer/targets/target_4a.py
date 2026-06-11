"""
Fuzzing wrapper for 4A/main (Exercise 4A buffer overflow).

main is invoked as `./main <offset>`, where <offset> is the byte
offset at which append_address() writes the address of
steal_password() into evil_str. This wrapper runs main with a given
offset and reports how it behaved.

NOTE: this assumes main.c is in the "pre-step-6" state, i.e. the call
    append_address(evil_str, address_start_byte, function_addr);
is active (NOT the hardcoded `append_address(evil_str, 0, 0xdeadbeef)`
debug version from step 6). If the hardcoded version is still in
place, the offset argument has no effect and every run behaves
identically — so the fuzzer won't find anything interesting.
"""

import subprocess
import signal

# Adjust this path to wherever the compiled 4A binary lives relative
# to wherever you run the fuzzer from.
BINARY = "./4A/main"


def run_4a(offset, timeout=2):
    """
    Run main with the given offset.

    Returns a dict describing the outcome:
        offset      - the offset that was tested
        returncode  - process exit code (negative N => killed by signal N)
        signal      - signal number if killed by a signal, else None
        crashed     - True if the process was killed by SIGSEGV
        hijacked    - True if steal_password() was successfully called
        output      - combined stdout+stderr, decoded as text
    """
    try:
        result = subprocess.run(
            [BINARY, str(offset)],
            capture_output=True,
            timeout=timeout,
        )
        rc = result.returncode
        raw_out = result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        rc = None
        raw_out = (exc.stdout or b"") + (exc.stderr or b"")

    sig = None
    crashed = False
    if rc is not None and rc < 0:
        sig = -rc
        crashed = (sig == signal.SIGSEGV)

    output = raw_out.decode(errors="replace")
    hijacked = "Malicious function Called" in output

    return {
        "offset": offset,
        "returncode": rc,
        "signal": sig,
        "crashed": crashed,
        "hijacked": hijacked,
        "output": output,
    }


if __name__ == "__main__":
    # Quick manual sanity check across a few known offsets from
    # Exercise 4 (24 should show hijacked=True; large offsets crash).
    for offset in (8, 24, 60, 128):
        print(run_4a(offset))
