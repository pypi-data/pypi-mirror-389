import os
import sys
import subprocess

def _run_with_extra_arg(extra_arg=None):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(current_dir, "autowzry", "autowzry.exe")

    if not os.path.exists(exe_path):
        print(f"autowzry.exe not found: {exe_path}", file=sys.stderr)
        sys.exit(1)

    cmd = [exe_path]
    if extra_arg:
        cmd.append(extra_arg)
    cmd += sys.argv[1:]
    subprocess.run(cmd)


def main():
    """默认入口：正常运行"""
    _run_with_extra_arg()


def main_wzyd():
    """仅执行营地礼包逻辑"""
    _run_with_extra_arg("wzyd")


def main_tiyanfu():
    """仅执行体验服更新逻辑"""
    _run_with_extra_arg("tiyanfu")


if __name__ == "__main__":
    main()