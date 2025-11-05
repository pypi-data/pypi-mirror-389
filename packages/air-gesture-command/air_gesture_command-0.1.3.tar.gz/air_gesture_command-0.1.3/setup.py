from setuptools import setup, find_packages
import os

# Read README.md safely
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path) and os.path.getsize(readme_path) > 0:
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = 'Control media players like Youtube, VLC, and Spotify using hand gestures.'

setup(
    name='air-gesture-command',  # Package name on PyPI
    version='0.1.3',
    description='Control media players like Youtube, VLC, and Spotify using hand gestures.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Akshit',
    author_email='akshitprajapati24@gmail.com',
    url='https://github.com/akshit0942b/air-gesture-command',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'mediapipe',
        'pyautogui'
    ],
    classifiers=[
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: MIT License',
    'Operating System :: MacOS',
    'Operating System :: MacOS :: MacOS X',
    ],
    python_requires='>=3.7,<3.13',
    entry_points={
    'console_scripts': [
        'air-command=air_command.main:main',  # adjust based on your actual file and function
    ],
},
)
