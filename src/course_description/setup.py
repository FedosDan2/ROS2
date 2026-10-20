from setuptools import find_packages, setup

package_name = 'course_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml']),
        (
            'share/' + package_name + '/urdf',
            ['urdf/vehicle.urdf.xacro'],
        ),
        (
            'share/' + package_name + '/launch',
            ['launch/state_publisher.launch.py'],
        ),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='FedosDan2',
    maintainer_email='f.danilov@g.nsu.ru',
    description='PR06: Ackerman robot',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
