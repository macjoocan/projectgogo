"""Install this folder as a Blender add-on, or import from tools in headless jobs."""
bl_info = {"name": "Levelscope Motion Remap", "author": "Levelscope",
           "version": (0, 2, 0), "blender": (5, 0, 0), "category": "Animation",
           "location": "3D View > Sidebar > Motion Remap",
           "description": "Independent preset-based skeleton retargeting on copied rigs"}


def register():
    from . import ui
    ui.register()


def unregister():
    from . import ui
    ui.unregister()
