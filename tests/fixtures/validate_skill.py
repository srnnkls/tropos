# /// script
# dependencies = [
#   "skills-ref @ git+https://github.com/agentskills/agentskills#subdirectory=skills-ref"
# ]
# ///
import subprocess
import sys

def main():
    args = sys.argv[1:]
    result = subprocess.run(["skills-ref"] + args, capture_output=True, text=True)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
