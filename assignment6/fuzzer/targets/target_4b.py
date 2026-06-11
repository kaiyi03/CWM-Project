"""
Fuzzing wrapper for 4B/vuln (Exercise 4B buffer overflow / gets()).

vuln.c walks through several prompts before reaching the vulnerable
gets() call at "Enter response data:". This wrapper automates the
earlier prompts with fixed, valid values (matching exploit.py) and
sends a payload of variable length to the vulnerable prompt.
"""

import signal
from pwn import process, context, PTY

context.update(arch='amd64', os='linux', log_level='error')

# Adjust this path to wherever the compiled 4B binary lives relative
# to wherever you run the fuzzer from.
BINARY = "./4B/src/vuln"


def run_4b(payload_length, timeout=2):
    """
    Run vuln, replaying the fixed prompt sequence, then send a
    payload of `payload_length` bytes ('A' * payload_length) to the
    vulnerable "Enter response data" prompt.

    Returns a dict describing the outcome:
        payload_length - the input length that was tested
        returncode      - process exit code (negative N => killed by signal N)
        signal          - signal number if killed by a signal, else None
        crashed         - True if the process was killed by SIGSEGV
        output          - captured stdout, decoded as text
    """
    payload = b"A" * payload_length

    p = process(BINARY, stdin=PTY)

    try:
        p.sendlineafter(b"Username: ", b"admin")
        p.sendlineafter(b"Password: ", b"secure123")
        p.sendlineafter(b"Enter your name: ", b"Fuzzer")
        p.sendlineafter(b"Enter your department: ", b"Eng")
        p.sendlineafter(b"Enter system command to process: ", b"ls")
        p.sendlineafter(b"Enter response data: ", payload)
        raw_out = p.recvall(timeout=timeout)
    except EOFError:
        raw_out = b""

    p.wait()
    rc = p.poll()

    sig = None
    crashed = False
    if rc is not None and rc < 0:
        sig = -rc
        crashed = (sig == signal.SIGSEGV)

    return {
        "payload_length": payload_length,
        "returncode": rc,
        "signal": sig,
        "crashed": crashed,
        "output": raw_out.decode(errors="replace"),
    }


if __name__ == "__main__":
    # Quick manual sanity check across a few lengths spanning the
    # known segfault threshold from Exercise 4.
    for length in (10, 264, 300):
        print(run_4b(length))
