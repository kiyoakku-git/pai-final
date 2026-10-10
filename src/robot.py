"""Simple pick-and-place skills for the Franka arm using inverse kinematics."""
import numpy as np

from util import to_np

ARM_DOFS = np.arange(7)
FINGER_DOFS = np.arange(7, 9)
DOWN_QUAT = np.array([0.0, 1.0, 0.0, 0.0])  # gripper pointing straight down (w, x, y, z)
HAND_TO_GRASP = 0.11  # distance from the 'hand' link to the grasp point between the fingertips
APPROACH = 0.15  # height above the grasp point used for approach / retreat


class Arm:
    def __init__(self, scene, franka):
        self.scene = scene
        self.franka = franka
        self.hand = franka.get_link("hand")
        self.finger_cmd = ("pos", np.array([0.04, 0.04]))

    def step(self, n=1):
        for _ in range(n):
            kind, value = self.finger_cmd
            if kind == "pos":
                self.franka.control_dofs_position(value, FINGER_DOFS)
            else:
                self.franka.control_dofs_force(value, FINGER_DOFS)
            self.scene.step()

    def _arm_q(self):
        return to_np(self.franka.get_dofs_position(ARM_DOFS))

    def move_to(self, grasp_pos, steps=100, yaw=0.0):
        """Move the grasp point to grasp_pos (world frame) with the gripper pointing down."""
        target = np.asarray(grasp_pos, dtype=float) + np.array([0.0, 0.0, HAND_TO_GRASP])
        quat = DOWN_QUAT
        if yaw:
            c, s = np.cos(yaw / 2), np.sin(yaw / 2)
            quat = np.array([0.0, c, s, 0.0])
        q_goal = to_np(self.franka.inverse_kinematics(link=self.hand, pos=target, quat=quat))[: len(ARM_DOFS)]
        q_start = self._arm_q()
        for i in range(1, steps + 1):
            a = i / steps
            a = a * a * (3 - 2 * a)  # smoothstep: slow start and stop
            self.franka.control_dofs_position(q_start + a * (q_goal - q_start), ARM_DOFS)
            self.step()
        self.step(20)  # let the PD controller settle

    def open(self, steps=40):
        self.finger_cmd = ("pos", np.array([0.04, 0.04]))
        self.step(steps)

    def close(self, steps=60):
        self.finger_cmd = ("force", np.array([-1.0, -1.0]))
        self.step(steps)

    def grasp_point(self):
        return to_np(self.hand.get_pos()) - np.array([0.0, 0.0, HAND_TO_GRASP])

    def pick(self, obj_pos):
        obj_pos = np.asarray(obj_pos, dtype=float)
        self.open()
        self.move_to(obj_pos + [0, 0, APPROACH], steps=120)
        self.move_to(obj_pos, steps=80)
        self.close()
        self.move_to(obj_pos + [0, 0, APPROACH + 0.05], steps=100)

    def place(self, place_pos):
        place_pos = np.asarray(place_pos, dtype=float)
        self.move_to(place_pos + [0, 0, APPROACH + 0.05], steps=150)
        self.move_to(place_pos + [0, 0, 0.03], steps=80)
        self.open()
        self.move_to(place_pos + [0, 0, APPROACH + 0.05], steps=80)
