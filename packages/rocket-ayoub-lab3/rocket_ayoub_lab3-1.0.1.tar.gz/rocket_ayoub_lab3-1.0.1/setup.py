from setuptools import setup, find_packages

setup(
    name='rocket_ayoub_lab3',              # ✅ Unique name — keep this
    version='1.0.1',                       # ✅ Increment version each upload
    author='aziba_ayoub',
    author_email='ma.aziba@esi-sba.dz',
    packages=find_packages(),              # ✅ Automatically detects your package
    url='https://test.pypi.org/project/rocket_ayoub_lab3/',
    license='MIT',
    description='A simple educational rocket simulation package using OOP concepts',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[],                   # ✅ Remove 'rocket' — it’s your own module!
    python_requires='>=3.7',
)
