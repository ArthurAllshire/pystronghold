
from wpilib import CANTalon

class Defeater:

    defeater_motor = CANTalon

    def up(self):
        self.defeater_motor.set(1.0)

    def down(self):
        self.defeater_motor.set(-1.0)

    def execute(self):
        current = self.defeater_motor.getOutputCurrent()

        if current > 30.0:
            self.defeater_motor.set(0.0)



