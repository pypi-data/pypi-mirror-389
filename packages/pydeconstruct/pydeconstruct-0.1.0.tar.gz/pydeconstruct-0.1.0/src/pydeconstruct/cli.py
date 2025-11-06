"""Simple CLI wrapper."""

import argparse
from .deconstruct import deconstruct_file, ToolMissing
import sys
from pathlib import Path
import textwrap


def main(argv=None):
    p = argparse.ArgumentParser(prog="pydeconstruct", description="Deconstruct a .py file into C, assembly, and machine code")
    p.add_argument("script", help="Python script to deconstruct (.py)")
    p.add_argument("--out", "-o", help="Output directory (default: <scriptname>_deconstruct)")
    p.add_argument("--no-keep-temp", action="store_true", help="Don't keep temporary files (default: keep)")
    p.add_argument("--show-c", action="store_true", help="Print generated C to stdout")
    p.add_argument("--show-asm", action="store_true", help="Print generated assembly to stdout")
    p.add_argument("--show-disasm", action="store_true", help="Print objdump disassembly to stdout")
    args = p.parse_args(argv)

    try:
        results = deconstruct_file(args.script, out_dir=args.out, keep_temp=not args.no_keep_temp)
    except ToolMissing as e:
        print("Tool missing:", e, file=sys.stderr)
        print("Make sure you have installed: cython, gcc (and optionally objdump/xxd).", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(3)

    print("Outputs written to:", results.get("out_dir"))
    print("- C file:", results.get("c_path"))
    print("- Assembly:", results.get("asm_path"))
    print("- Object:", results.get("obj_path"))
    print()

    if args.show_c and results.get("c_text"):
        print("==== Generated C ====")
        print(results["c_text"][:100000])  # limit
    if args.show_asm and results.get("asm_text"):
        print("==== Generated Assembly (.s) ====")
        print(results["asm_text"][:200000])
    if args.show_disasm and results.get("disassembly"):
        print("==== objdump disassembly ====")
        print(results["disassembly"][:200000])
    if args.show_disasm and results.get("bytes_hexdump"):
        print("==== machine bytes (xxd) ====")
        print(results["bytes_hexdump"][:200000])

    # Helpful tips:
    print(textwrap.dedent("""
    Notes:
      - Cython must be installed (pip install cython).
      - You need a C toolchain (gcc, make, Python dev headers).
      - The C produced by Cython relies on the Python C API; the object file may not be a standalone native executable.
      - For pure translation of small functions to native code, consider writing Cython cdef functions or using tools like Nuitka.
    """))


if __name__ == "__main__":
    main()
