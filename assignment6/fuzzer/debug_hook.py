"""
Debug hook: re-run a crashing input under gdb to capture a backtrace.

This is only called when a trial's run_4x() result reports
crashed=True. It re-runs the exact same input under gdb in batch
mode, lets it crash, and saves gdb's backtrace output to a file for
later inspection.

Requires the binaries to be compiled with debug symbols (-g) for the
backtrace to show function names/line numbers rather than raw
addresses.
"""

import os
import subprocess
import tempfile

BACKTRACE_DIR = "backtraces"


def _save_backtrace(name, gdb_output):
    os.makedirs(BACKTRACE_DIR, exist_ok=True)
    path = os.path.join(BACKTRACE_DIR, f"{name}.txt")
    with open(path, "w") as f:
        f.write(gdb_output)
    return path


def capture_backtrace_4a(binary, offset, trial_number, timeout=5):
    """
    Re-run 4A/main under gdb with the given offset and capture a
    backtrace. Returns the path to the saved backtrace file.
    """
    cmd = [
        "gdb", "-batch",
        "-ex", f"run {offset}",
        "-ex", "bt",
        binary,
    ]

    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
    output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")

    name = f"4a_trial{trial_number}_offset{offset}"
    return _save_backtrace(name, output)


def capture_backtrace_4b(binary, payload_length, trial_number, timeout=5):
    """
    Re-run 4B/vuln under gdb, replaying the same prompt sequence used
    by run_4b(), and capture a backtrace when it crashes. Returns the
    path to the saved backtrace file.
    """
    payload = b"A" * payload_length

    # Same sequence of stdin lines as run_4b()
    stdin_lines = [
        b"admin",
        b"secure123",
        b"Fuzzer",
        b"Eng",
        b"ls",
        payload,
    ]
    stdin_data = b"\n".join(stdin_lines) + b"\n"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(stdin_data)
        tmp_path = tmp.name

    try:
        cmd = [
            "gdb", "-batch",
            "-ex", f"run < {tmp_path}",
            "-ex", "bt",
            binary,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        output = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
    finally:
        os.remove(tmp_path)

    name = f"4b_trial{trial_number}_len{payload_length}"
    return _save_backtrace(name, output)
