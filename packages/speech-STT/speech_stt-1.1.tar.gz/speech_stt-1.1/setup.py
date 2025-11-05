from setuptools import setup, find_packages

setup(
    name='speech--STT',  # Package name (PyPI pe yeh se milega)
    version='1.01',
    author='Smoker_X',
    author_email='gauravchauhan@639710@gmail.com',
    description='This is speech to text package created by Smoker. If you speak, it will capture that voice and save the speaking text into a file.',
    packages=find_packages(),  # dak-STT folder ko package banayega
    install_requires=[
        'selenium',
        'webdriver-manager'
    ],  # Dependencies - yeh auto install honge
    python_requires='>=3.8',  # Selenium ke liye
)