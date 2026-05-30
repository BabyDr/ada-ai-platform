from setuptools import setup

setup(
    name="ai-textflow-cli",
    version="0.1.0",
    py_modules=["ai_app"],
    install_requires=["click>=8.0", "httpx>=0.28"],
    entry_points={
        "console_scripts": ["ai-app=ai_app:cli"],
    },
)
