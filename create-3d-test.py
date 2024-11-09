from scene import Simple3dScene


def main():
    scene3d = Simple3dScene()
    mat = scene3d.create_simple_material((0.9, 0.9, 0.9))

    scene3d.add_box((0, 0, 0), (100, 50, 70), mat)
    scene3d.add_box((50, 50, 50), (70, 100, 70), mat)
    scene3d.write('test.dae')


if __name__ == '__main__':
    main()
