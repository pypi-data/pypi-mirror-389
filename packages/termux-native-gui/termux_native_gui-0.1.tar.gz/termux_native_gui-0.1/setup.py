from setuptools import setup, find_packages

setup(
    name="termux-native-gui",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "termux-native-gui=termux_native_gui.main:main",
        ]
    },
    package_data={
        "termux_native_gui": ["../gui.zip"],  # zip ফাইল প্যাকেজে অন্তর্ভুক্ত
    },
    zip_safe=False,
)