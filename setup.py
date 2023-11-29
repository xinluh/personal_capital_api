from distutils.core import setup
setup(
    name="personal_capital_api",
    packages=["personal_capital_api"],
    version="0.0.1",
    description="Data scrapper API for Personal Capital / Empower Dashboard",
    author="Xinlu Huang",
    install_requires=[
        'selenium',
        'requests',
    ]
)
