"""Tabletop scene: Franka arm, three colored blocks and a tray."""
import numpy as np
import genesis as gs

BLOCK_SIZE = 0.04
BLOCKS = {
    "red block": {"pos": (0.55, -0.20, BLOCK_SIZE / 2), "color": (0.85, 0.10, 0.10)},
    "green block": {"pos": (0.62, 0.00, BLOCK_SIZE / 2), "color": (0.10, 0.70, 0.20)},
    "blue block": {"pos": (0.50, 0.12, BLOCK_SIZE / 2), "color": (0.10, 0.25, 0.85)},
    "yellow block": {"pos": (0.50, -0.05, BLOCK_SIZE / 2), "color": (0.95, 0.80, 0.30)},
        
}
TRAY_CENTER = (0.35, 0.40)
TRAY_INNER = 0.16
TRAY_WALL_H = 0.04
TRAY_WALL_T = 0.01

# Places inside the tray, used in order so that blocks do not land on top of each other.
TRAY_SLOTS = [(-0.04, -0.04), (0.04, 0.04), (-0.04, 0.04), (0.04, -0.04)]


def in_tray(pos, margin=0.0):
    """True if an (x, y, ...) position lies inside the tray's inner area."""
    half = TRAY_INNER / 2 - margin
    return abs(pos[0] - TRAY_CENTER[0]) < half and abs(pos[1] - TRAY_CENTER[1]) < half


HOME_QPOS = np.array([0.0, -0.3, 0.0, -2.2, 0.0, 2.0, 0.79, 0.04, 0.04])
KP = np.array([4500, 4500, 3500, 3500, 2000, 2000, 2000, 100, 100])
# KP = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])
KV = np.array([450, 450, 350, 350, 200, 200, 200, 10, 10])


def _add_tray(scene):
    cx, cy = TRAY_CENTER
    half = TRAY_INNER / 2 + TRAY_WALL_T / 2
    span = TRAY_INNER + 2 * TRAY_WALL_T
    color = gs.surfaces.Default(color=(0.75, 0.60, 0.40))
    walls = [
        ((cx + half, cy, TRAY_WALL_H / 2), (TRAY_WALL_T, span, TRAY_WALL_H)),
        ((cx - half, cy, TRAY_WALL_H / 2), (TRAY_WALL_T, span, TRAY_WALL_H)),
        ((cx, cy + half, TRAY_WALL_H / 2), (span, TRAY_WALL_T, TRAY_WALL_H)),
        ((cx, cy - half, TRAY_WALL_H / 2), (span, TRAY_WALL_T, TRAY_WALL_H)),
    ]
    for pos, size in walls:
        scene.add_entity(gs.morphs.Box(pos=pos, size=size, fixed=True), surface=color)

def random_positions(names, rng, x_range=(0.45, 0.65), y_range=(-0.25, 0.20), min_dist=0.08):
    """Pick a random (x, y) for each block, keeping blocks at least min_dist apart."""
    placed = {}
    for name in names:
        while True:
            p = (rng.uniform(*x_range), rng.uniform(*y_range))
            if all(np.hypot(p[0] - q[0], p[1] - q[1]) >= min_dist for q in placed.values()):
                placed[name] = p
                break
    return placed


# def build_scene(backend=gs.gpu, video_res=(1280, 720)):
def build_scene(backend=gs.gpu, video_res=(1280, 720), positions=None):
    """Create the scene and return (scene, franka, blocks, eye_cam, video_cam)."""
    gs.init(backend=backend, logging_level="warning")
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        show_viewer=False,
    )
    scene.add_entity(gs.morphs.Plane())
    franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))
    blocks = {}

    for name, spec in BLOCKS.items():
        pos = spec["pos"] if positions is None else (*positions[name], BLOCK_SIZE / 2)
        blocks[name] = scene.add_entity(
            gs.morphs.Box(pos=pos, size=(BLOCK_SIZE,) * 3),
            surface=gs.surfaces.Default(color=spec["color"]),
        )
        
    _add_tray(scene)
    # Camera used by the AI to look at the table (perception).
    eye_cam = scene.add_camera(res=(640, 480), pos=(1.05, 0.05, 0.85), lookat=(0.48, 0.1, 0.0), fov=50, GUI=False)
    # Camera used only for the submitted video.
    video_cam = scene.add_camera(res=video_res, pos=(1.45, -0.95, 0.85), lookat=(0.35, 0.10, 0.25), fov=45, GUI=False)
    scene.build()

    franka.set_dofs_kp(KP)
    franka.set_dofs_kv(KV)
    franka.set_dofs_position(HOME_QPOS)
    return scene, franka, blocks, eye_cam, video_cam
