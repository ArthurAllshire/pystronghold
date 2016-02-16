#!/usr/bin/env python3

import wpilib
import magicbot

from components.chassis import Chassis, BlankPIDOutput
from components.vision import Vision
from components.bno055 import BNO055
from components.range_finder import RangeFinder
from components.shooter import Shooter
from components.intake import Intake

from networktables import NetworkTable

import logging
import math

class StrongholdRobot(magicbot.MagicRobot):
    chassis = Chassis
    intake = Intake
    shooter = Shooter
    range_finder = RangeFinder
    vision = Vision

    def createObjects(self):
        self.logger = logging.getLogger("robot")
        self.sd = NetworkTable.getTable('SmartDashboard')
        self.intake_motor = wpilib.CANTalon(7)
        self.shooter_motor = wpilib.CANTalon(12)
        self.range_finder_counter = wpilib.Counter(0)
        self.range_finder_counter.setSemiPeriodMode(highSemiPeriod=True)
        self.joystick = wpilib.Joystick(0)
        self.gamepad = wpilib.Joystick(1)
        self.pressed_buttons = set()
        # needs to be created here so we can pass it in to the PIDController
        self.bno055 = BNO055()
        self.heading_hold_pid_output = BlankPIDOutput()
        self.heading_hold_pid = wpilib.PIDController(0.5, 0.0, 0.0, self.bno055, self.heading_hold_pid_output)
        self.heading_hold_pid.PercentageTolerance_onTarget(3.0)
        self.heading_hold_pid.setContinuous(True)
        self.heading_hold_pid.setInputRange(-math.pi, math.pi)

    def putData(self):
        self.sd.putDouble("range_finder", self.range_finder.getDistance())
        self.sd.putDouble("gyro", self.bno055.getHeading())
        vision_array = self.vision.get()
        vision_x = None
        if not vision_array:
            vision_x = -2
        else:
            vision_x = vision_array[0]
        self.sd.putDouble("vision_x", vision_x)
        self.sd.putDouble("vx", self.chassis.vx)
        self.sd.putDouble("vy", self.chassis.vy)
        self.sd.putDouble("vz", self.chassis.vz)
        self.sd.putDouble("field_oriented", self.chassis.field_oriented)
        self.sd.putDouble("raw_yaw", self.bno055.getRawHeading())
        self.sd.putDouble("raw_pitch", self.bno055.getPitch())
        self.sd.putDouble("raw_roll", self.bno055.getRoll())
        self.sd.putDouble("shooter_speed", self.shooter._speed)
        self.sd.putDouble("heading_pid_output", self.heading_hold_pid_output.output)
        self.sd.putDouble("heading_hold_pid_setpoint", self.heading_hold_pid.getSetpoint())
        self.sd.putDouble("intake_state", self.intake.state)
        self.sd.putDouble("vision_pid_output", self.chassis.vision_pid_output.output)
        self.sd.putBoolean("track_vision", self.chassis.track_vision)


    def disabledInit(self):
        pass

    def disabledPeriodic(self):
        """This function is called periodically when disabled."""
        self.putData()

    def teleopInit(self):
        pass

    def teleopPeriodic(self):
        """This function is called periodically during operator control."""
        try:
            if self.debounce(2):
                self.intake.toggle()
        except:
            self.onException()

        try:
            if self.debounce(7):
                self.chassis.toggle_field_oriented()
        except:
            self.onException()

        try:
            if self.debounce(8):
                self.bno055.resetHeading()
        except:
            self.onException()

        try:
            if self.debounce(11):
                self.chassis.toggle_vision_tracking()
        except:
            self.onException()

        try:
            if self.debounce(12):
                self.chassis.toggle_range_holding(2.0)  # 2m range
        except:
            self.onException()

        try:
            if self.debounce(1):
                self.shooter.toggle()
                self.intake.fire()
        except:
            self.onException()

        try:
            if self.debounce(5):
                self.chassis.toggle_heading_hold()
        except:
            self.onException()

        try:
            if self.joystick.getPOV() != -1:
                self.chassis.heading_hold = True
                direction = 0.0
                if self.joystick.getPOV() == 180:
                    direction = math.pi # face to shoot to middle goal
                elif self.joystick.getPOV() == 225:
                    direction = math.pi - math.pi/3.0
                elif self.joystick.getPOV() == 135:
                    direction = math.pi + math.pi/3.0
                else:
                    direction = -self.joystick.getPOV()
                self.chassis.heading_hold_pid.set_heading_setpoint(direction)
        except:
            self.onException()
        self.chassis.inputs = [-rescale_js(self.joystick.getY(), deadzone=0.05),
                            - rescale_js(self.joystick.getX(), deadzone=0.05),
                            - rescale_js(self.joystick.getZ(), deadzone=0.4, exponential=0.3),
                            (self.joystick.getThrottle() - 1.0) / -2.0
                            ]
        self.putData()


    def testPeriodic(self):
        """This function is called periodically during test mode."""
        wpilib.LiveWindow.run()

    def debounce(self, button):
        if self.joystick.getRawButton(button):
            if button in self.pressed_buttons:
                return False
            else:
                self.pressed_buttons.add(button)
                return True
        else:
            self.pressed_buttons.discard(button)
            return False

def rescale_js(value, deadzone=0.0, exponential=0.0, rate=1.0):
    value_negative = 1.0
    if value < 0:
        value_negative = -1.0
        value = -value
    # Cap to be +/-1
    if abs(value) > 1.0:
        value /= abs(value)
    # Apply deadzone
    if abs(value) < deadzone:
        return 0.0
    elif exponential == 0.0:
        value = (value-deadzone)/(1-deadzone)
    else:
        a = math.log(exponential+1)/(1-deadzone)
        value = (math.exp(a*(value - deadzone))-1)/exponential
    return value*value_negative*rate


if __name__ == "__main__":
    wpilib.run(StrongholdRobot)
