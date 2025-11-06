# setup.py
from setuptools import setup

setup(
    name="flagsolver123",      # PyPI에 올라갈 패키지 이름 (유니크하게!)
    version="0.0.1",
    py_modules=["solver"],     # solver.py 등록
    entry_points={
        "console_scripts": [
            # pip install 후에 'flag-solve'라는 커맨드로 실행 가능
            "flag-solve=solver:main",
        ],
    },
)