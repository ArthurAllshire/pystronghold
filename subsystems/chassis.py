
from wpilib.command import Subsystem


class Chassis(Subsystem):

    def __init__(self):
        # we want to create four swervemodules here
        # the numbers here need to be replaced with constants from robotmap
        #  A - D
        #  |   |
        #  B - C
        _modules = [SwerveModule(1,2), SwerveModule(3,4), SwerveModule(5,6), SwerveModule(7,8)]


    #Put methods for controlling this subsystem here.
    # Call these from Commands.

    def initDefaultCommand(self):
        #Set the default command for a subsystem here.
        #setDefaultCommand(ExampleCommand())
        pass

    def drive(vX, vY, vZ, throttle):
        pass

    def zero_module_directions():
        pass


class SwerveModule():
    def __init__(self, driveCanTalonId, steerCanTalonId, absoluteEncoder = True):
        # Initialise private motor controllers
        self._drive = None
        self._steer = None
        # Set up the motor controllers
        # Different depending on whether we are using absolute encoders or not
        if absoluteEncoder:
            pass
        else:
            pass

        # Private members to store the setpoints
        self._speed = 0.0
        self._direction = 0.0
        # Always in radians. Right hand rule applies - Z is up!
        # Rescale values to the range [0, 2*pi)

    def steer(self, direction, speed = 0):
        # Set the speed and direction of the swerve module
        # Always choose the direction that minimises movement,
        # even if this means reversing the drive motor
        pass

    def getSpeed(self):
        return self._speed

    def getDirection(self):
        return self._direction
