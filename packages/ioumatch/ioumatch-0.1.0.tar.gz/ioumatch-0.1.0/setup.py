# setup.py
from setuptools import setup, find_packages

setup(
    name='ioumatch',
    version='0.1.0',
    description='A lightweight Python library for evaluating segmentation masks using IoU and matching algorithms',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Alexis Yehadji',
    author_email='yehadjialexis@gmail.com',
    url='https://github.com/al-alec/ioumatch',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20',
        'opencv-python>=4.7',  # Optional, if you want cv2 support
        'scipy>=1.10',  # Optional, for Hungarian matching
        'scikit-image>=0.22',  # Optional, for component labeling
        'imageio>=2.33',  # Optional, fallback if OpenCV is not available
        'matplotlib',  # Optional, for IoU matrix visualization
    ],
    extras_require={
        'io': ['opencv-python', 'imageio', 'Pillow'],
        'hungarian': ['scipy'],
        'skimage': ['scikit-image'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
