"""
Core functions to deconstruct a Python file into C (via Cython),
then assembly and machine code (via gcc/objdump/xxd).
"""

from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from typing import Optional


class ToolMissing(Exception):
    pass


def _which_or_raise(name: str):
    path = shutil.which(name)
    if not path:
        raise ToolMissing(f"Required tool '{name}' not found in PATH. Please install it.")
    return path


def run_cmd(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def deconstruct_file(py_path: str, out_dir: Optional[str] = None, keep_temp: bool = True):
    """
    Deconstruct a Python file into:
      - C source (via Cython)
      - Assembly (.s) via gcc -S
      - Object file (.o) via gcc -c
      - Disassembly & machine bytes via objdump / xxd

    Returns a dict with paths and text outputs for convenience.
    """
    py_path = Path(py_path)
    if not py_path.exists():
        raise FileNotFoundError(py_path)

    # Ensure tools exist
    cython = _which_or_raise("cython")
    gcc = _which_or_raise("gcc")
    objdump = shutil.which("objdump")  # may not exist on windows toolchains
    xxd = shutil.which("xxd")

    out_dir = Path(out_dir) if out_dir else Path.cwd() / f"{py_path.stem}_deconstruct"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    tempdir = tempfile.TemporaryDirectory()
    try:
        # 1) Generate C with cython
        c_path = out_dir / f"{py_path.stem}.c"
        cmd = [cython, "--embed", "-3", str(py_path), "-o", str(c_path)]
        code, out, err = run_cmd(cmd)
        results["cython_returncode"] = code
        results["cython_stdout"] = out
        results["cython_stderr"] = err
        if code != 0:
            # try without --embed as fallback
            cmd2 = [cython, "-3", str(py_path), "-o", str(c_path)]
            code2, out2, err2 = run_cmd(cmd2)
            results["cython_returncode_fallback"] = code2
            results["cython_stdout_fallback"] = out2
            results["cython_stderr_fallback"] = err2
            if code2 != 0:
                raise RuntimeError(f"Cython failed:\n{err}\n{err2}")

        results["c_path"] = str(c_path)

        # 2) Emit assembly (-S). Need include flags so that generated C (which imports Python headers) can compile.
        # Gather Python include flags from sysconfig
        cfg = sysconfig.get_config_vars()
        include_dirs = cfg.get("INCLUDEPY") or cfg.get("INCLUDEPY3") or sysconfig.get_path("include")
        cflags = []
        if include_dirs:
            cflags += ["-I", include_dirs]

        asm_path = out_dir / f"{py_path.stem}.s"
        cmd = [gcc, "-S", str(c_path), "-o", str(asm_path)] + cflags
        code, out, err = run_cmd(cmd)
        results["gcc_S_returncode"] = code
        results["gcc_S_stdout"] = out
        results["gcc_S_stderr"] = err
        if code != 0:
            # still try without include flags
            cmd2 = [gcc, "-S", str(c_path), "-o", str(asm_path)]
            code2, out2, err2 = run_cmd(cmd2)
            results["gcc_S_returncode_fallback"] = code2
            results["gcc_S_stdout_fallback"] = out2
            results["gcc_S_stderr_fallback"] = err2
            if code2 != 0:
                raise RuntimeError(f"gcc -S failed:\n{err}\n{err2}")

        results["asm_path"] = str(asm_path)

        # 3) Compile to object file
        obj_path = out_dir / f"{py_path.stem}.o"
        cmd = [gcc, "-c", str(c_path), "-o", str(obj_path)] + cflags
        code, out, err = run_cmd(cmd)
        results["gcc_c_returncode"] = code
        results["gcc_c_stdout"] = out
        results["gcc_c_stderr"] = err
        if code != 0:
            cmd2 = [gcc, "-c", str(c_path), "-o", str(obj_path)]
            code2, out2, err2 = run_cmd(cmd2)
            results["gcc_c_returncode_fallback"] = code2
            results["gcc_c_stdout_fallback"] = out2
            results["gcc_c_stderr_fallback"] = err2
            if code2 != 0:
                raise RuntimeError(f"gcc -c failed:\n{err}\n{err2}")

        results["obj_path"] = str(obj_path)

        # 4) Disassembly + bytes
        disasm_text = ""
        bytes_text = ""
        if objdump:
            cmd = [objdump, "-d", str(obj_path)]
            code, out, err = run_cmd(cmd)
            results["objdump_returncode"] = code
            results["objdump_stdout"] = out
            results["objdump_stderr"] = err
            disasm_text = out + ("\nERR:\n" + err if err else "")
        else:
            results["objdump_missing"] = True

        if xxd:
            cmd = [xxd, "-g", "1", str(obj_path)]
            code, out, err = run_cmd(cmd)
            results["xxd_returncode"] = code
            results["xxd_stdout"] = out
            results["xxd_stderr"] = err
            bytes_text = out + ("\nERR:\n" + err if err else "")
        else:
            results["xxd_missing"] = True

        results["disassembly"] = disasm_text
        results["bytes_hexdump"] = bytes_text

        # 5) Save any outputs (assembly, c already saved)
        # read & return the assembly and C text
        try:
            results["c_text"] = c_path.read_text(encoding="utf-8")
        except Exception:
            results["c_text"] = None
        try:
            results["asm_text"] = asm_path.read_text(encoding="utf-8")
        except Exception:
            results["asm_text"] = None

        results["out_dir"] = str(out_dir)

        return results

    finally:
        if not keep_temp:
            tempdir.cleanup()
