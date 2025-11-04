# Derivative of github: Mohamed-512's tab bar component

import os
import streamlit.components.v1 as components
from dataclasses import dataclass
from typing import List
import subprocess

IS_RELEASE = True

# Build frontend if build directory doesn't exist
absolute_path = os.path.dirname(os.path.abspath(__file__))
build_path = os.path.join(absolute_path, "frontend/build")

# Check if build is needed (only if build directory doesn't exist)
if not os.path.exists(build_path):
    try:
        # Run build script from the project root (one level up from custom_component)
        project_root = os.path.dirname(absolute_path)
        build_script_path = os.path.join(project_root, "build_frontend.sh")
        if os.path.exists(build_script_path):
            print("Building custom component frontend...")
            subprocess.run([build_script_path], check=True, cwd=project_root)
            print("Custom component build completed.")
        else:
            print(f"Warning: Build script not found at: {build_script_path}")
            print("Custom component may not work properly.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to build frontend: {e}")
        print("Custom component may not work properly.")

if IS_RELEASE:
    _component_func = components.declare_component("tab_bar", path=build_path)
else:
    _component_func = components.declare_component("tab_bar", url="http://localhost:3000")


@dataclass(frozen=True, order=True, unsafe_hash=True)
class TabBarItemData:
    id: int
    title: str
    description: str

    def to_dict(self):
        return {"id": self.id, "title": self.title, "description": self.description}


def tab_bar(data: List[TabBarItemData], default=None, return_type=str, key=None):
    data = list(map(lambda item: item.to_dict(), data))
    component_value = _component_func(data=data, selectedId=default, key=key, default=default)

    try:
        if return_type == str:
            return str(component_value)
        elif return_type == int:
            return int(component_value)
        elif return_type == float:
            return float(component_value)
    except:
        return component_value