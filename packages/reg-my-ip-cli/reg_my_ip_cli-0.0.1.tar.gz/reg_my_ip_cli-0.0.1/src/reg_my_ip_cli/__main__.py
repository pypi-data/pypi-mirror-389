import os
if os.getenv("DEV") is not None:
    import sys
    p=os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, p)

from reg_my_ip_cli._cmd import run
if __name__ == "__main__":
    run.main()