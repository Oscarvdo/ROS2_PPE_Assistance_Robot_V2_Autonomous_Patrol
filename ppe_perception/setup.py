from setuptools import find_packages, setup

package_name = "ppe_perception"
setup(
    name=package_name, version="0.1.0", packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"], zip_safe=True,
    maintainer="Oscar I. Valenzuela", maintainer_email="osckar.vdo@gmail.com",
    description="PPE perception pipeline and ROS node.", license="Apache-2.0",
    entry_points={"console_scripts": [
        "perception_node = ppe_perception.node:main",
        "mock_camera = ppe_perception.mock_camera_node:main",
    ]},
)
