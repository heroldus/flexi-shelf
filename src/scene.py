from typing import Tuple

import numpy as np
from collada import Collada
from collada.geometry import Geometry
from collada.material import Material, Effect
from collada.scene import MaterialNode, GeometryNode, Node, Scene
from collada.source import FloatSource, InputList


CUBOID_NORMALS = np.array([0, 0, 1, 0, 1, 0, 0, -1, 0, -1, 0, 0, 1, 0, 0, 0, 0, -1])
CUBOID_TRIANGLE_INDICES = np.array([0, 0, 2, 0, 3, 0, 0, 0, 3, 0, 1, 0, 0, 1, 1, 1, 5, 1,
                                    0, 1, 5, 1, 4, 1, 6, 2, 7, 2, 3, 2, 6, 2, 3, 2, 2, 2,
                                    0, 3, 4, 3, 6, 3, 0, 3, 6, 3, 2, 3, 3, 4, 7, 4, 5, 4,
                                    3, 4, 5, 4, 1, 4, 5, 5, 7, 5, 6, 5, 5, 5, 6, 5, 4, 5])


class Simple3dScene:

    def __init__(self):
        self.mesh = Collada()
        self.scene = Scene("scene", [])

        self.mesh.scenes.append(self.scene)
        self.mesh.scene = self.scene
        self.node_counter = 0

    def create_simple_material(self, color: Tuple[float, float, float]) -> Material:
        effect = Effect("effect0", [], "phong", diffuse=color, specular=(0.2, 0.8, 0.2))
        material = Material("material0", "mymaterial", effect)

        self.mesh.materials.append(material)
        self.mesh.effects.append(effect)

        return material

    def add_box(self, start: Tuple[float, float, float], dimensions: Tuple[float, float, float], material: Material):
        node_id = f"cuboid_{self.node_counter}"

        end = (start[0] + dimensions[0], start[1] + dimensions[1], start[2] + dimensions[2])
        vert_floats = [start[0], end[1], end[2],
                       end[0], end[1], end[2],
                       start[0], start[1], end[2],
                       end[0], start[1], end[2],
                       start[0], end[1], start[2],
                       end[0], end[1], start[2],
                       start[0], start[1], start[2],
                       end[0], start[1], start[2]
                       ]

        vertices_source = FloatSource(f"{node_id}_vertices", np.array(vert_floats), ('X', 'Y', 'Z'))
        normal_source = FloatSource(f"{node_id}_normals", CUBOID_NORMALS, ('X', 'Y', 'Z'))

        geometry = Geometry(self.mesh, f"{node_id}_geometry", node_id, [vertices_source, normal_source])

        input_list = InputList()
        input_list.addInput(0, 'VERTEX', f"#{vertices_source.id}")
        input_list.addInput(1, 'NORMAL', f"#{normal_source.id}")

        material_node = MaterialNode(f"{node_id}_material", material, inputs=[])
        triangle_set = geometry.createTriangleSet(CUBOID_TRIANGLE_INDICES, input_list, material_node.symbol)
        geometry.primitives.append(triangle_set)
        self.mesh.geometries.append(geometry)

        geometry_node = GeometryNode(geometry, [material_node])
        node = Node(node_id, children=[geometry_node])

        self.scene.nodes.append(node)

        self.node_counter += 1

    def write(self, file_path: str):
        self.mesh.write(file_path)


