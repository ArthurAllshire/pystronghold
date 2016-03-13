#!/usr/bin/env python3

import wpilib
import magicbot

from components.chassis import Chassis, BlankPIDOutput, constrain_angle
from components.vision import Vision
from components.bno055 import BNO055
from components.range_finder import RangeFinder
from components.shooter import Shooter
from components import shooter
from components.intake import Intake
from components.defeater import Defeater

from networktables import NetworkTable

import logging
import math

class StrongholdRobot(magicbot.MagicRobot):
    chassis = Chassis
    intake = Intake
    shooter = Shooter
    defeater = Defeater

    def createObjects(self):
        self.logger = logging.getLogger("robot")
        self.sd = NetworkTable.getTable('SmartDashboard')
        self.intake_motor = wpilib.CANTalon(11)
        self.shooter_motor = wpilib.CANTalon(12)
        self.defeater_motor = wpilib.CANTalon(1)
        self.joystick = wpilib.Joystick(0)
        self.gamepad = wpilib.Joystick(1)
        self.pressed_buttons_js = set()
        self.pressed_buttons_gp = set()
        # needs to be created here so we can pass it in to the PIDController
        self.bno055 = BNO055()
        self.vision = Vision()
        self.range_finder = RangeFinder(0)
        self.heading_hold_pid_output = BlankPIDOutput()
        Tu = 1.6
        Ku = 0.6
        Kp = Ku * 0.2
        self.heading_hold_pid = wpilib.PIDController(0.38,
                                                     2.0 * Kp / Tu * 0.07,
                                                     1.0 * Kp * Tu / 20.0 * 0,
                                                     self.bno055, self.heading_hold_pid_output)
        self.heading_hold_pid.setTolerance(3.0)
        self.heading_hold_pid.setContinuous(True)
        self.heading_hold_pid.setInputRange(-math.pi, math.pi)
        self.heading_hold_pid.setOutputRange(-1.0, 1.0)
        self.intake_motor.setFeedbackDevice(wpilib.CANTalon.FeedbackDevice.QuadEncoder)
        self.intake_motor.reverseSensor(True)

    def putData(self):
        self.sd.putDouble("range_finder", self.range_finder.getDistance())
        self.sd.putDouble("gyro", self.bno055.getHeading())
        vision_array = self.vision.get()
        vision_x = None
        vision_w = None
        vision_h = None
        if not vision_array:
            vision_x = -2
            vision_w = -2
            vision_h = -2
        else:
            vision_x = vision_array[0]
            vision_w = vision_array[2]
            vision_h = vision_array[3]
        self.sd.putDouble("vision_pid_get", self.vision.pidGet())
        self.sd.putDouble("vision_x", vision_x)
        self.sd.putDouble("vision_w", vision_w)
        self.sd.putDouble("vision_h", vision_h)
        self.sd.putDouble("vx", self.chassis.vx)
        self.sd.putDouble("vy", self.chassis.vy)
        self.sd.putDouble("vz", self.chassis.vz)
        self.sd.putDouble("input_twist", self.chassis.inputs[2])
        self.sd.putDouble("field_oriented", self.chassis.field_oriented)
        self.sd.putDouble("raw_yaw", self.bno055.getRawHeading())
        self.sd.putDouble("raw_pitch", self.bno055.getPitch())
        self.sd.putDouble("raw_roll", self.bno055.getRoll())
        self.sd.putDouble("shooter_speed", -self.shooter._speed) # minus sign here so +ve is shooting
        self.sd.putDouble("heading_pid_output", self.heading_hold_pid_output.output)
        self.sd.putDouble("heading_hold_pid_setpoint", self.heading_hold_pid.getSetpoint())
        self.sd.putDouble("intake_state", self.intake.state)
        self.sd.putDouble("intake_speed", self.intake._speed)
        self.sd.putDouble("distance_pid_output", self.chassis.distance_pid_output.output)
        self.sd.putBoolean("track_vision", self.chassis.track_vision)
        self.sd.putDouble("pov", self.joystick.getPOV())
        self.sd.putDouble("gyro_z_rate", self.bno055.getHeadingRate())
        self.sd.putDouble("heading_hold_error", self.heading_hold_pid.getSetpoint()-self.bno055.getAngle())
        self.sd.putDouble("defeater_current", self.defeater_motor.getOutputCurrent())
        self.sd.putDouble("defeater_speed", self.defeater_motor.get())
        self.sd.putDouble("joystick_throttle", self.joystick.getThrottle())
        self.sd.putDouble("range_pid_get", self.range_finder.pidGet())
        self.sd.putDouble("encoder_a", self.chassis.encoder_a.get())
        self.sd.putDouble("encoder_b", self.chassis.encoder_b.get())


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
                enabled = self.heading_hold_pid.isEnable()
                self.heading_hold_pid.disable()
                self.bno055.resetHeading()
                self.heading_hold_pid.setSetpoint(constrain_angle(self.bno055.getAngle()))
                if enabled:
                    self.heading_hold_pid.enable()
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
                if self.shooter.state == shooter.States.off:
                    self.shooter.start_shoot()
                else:
                    self.shooter.toggle()
                self.intake.fire()
        except:
            self.onException()

        try:
            if self.debounce(9):
                self.chassis.toggle_heading_hold()
        except:
            self.onException()

        try:
            if self.debounce(4):
                self.defeater.up()
        except:
            self.onException()

        try:
            if self.debounce(5):
                self.shooter.stop()
                self.intake.stop()
        except:
            self.onException()

        try:
            if self.debounce(3):

                self.chassis.track_vision = True
                self.chassis.range_setpoint = 2.0
                self.chassis.distance_pid.enable()
                # self.shooter.start_shoot()
        except:
            self.onException()

        try:
            if self.debounce(6):
                self.defeater.down()
        except:
            self.onException()

        try:
            if self.debounce(10):
                self.shooter.backdrive()
                self.intake.backdrive()
        except:
            self.onException()

        try:
            if self.joystick.getPOV() != -1:
                self.chassis.heading_hold = True
                direction = 0.0
                if self.joystick.getPOV() == 0:
                    # shooter centre goal
                    direction = math.pi
                elif self.joystick.getPOV() == 90:
                    # shooter right goal
                    direction = math.pi/3.0+math.pi
                elif self.joystick.getPOV() == 270:
                    # shooter left goal
                    direction = -math.pi/3.0+math.pi
                elif self.joystick.getPOV() == 180:
                    direction = 0.0
                self.chassis.set_heading_setpoint(direction)
        except:
            self.onException()

        try:
            if self.gamepad.getRawButton(3):
                self.intake.backdrive_slow()
        except:
            self.onException()

        try:
            if self.debounce(1, gamepad=True):
                self.chassis.zero_encoders()
                self.chassis.distance_pid.setSetpoint(1.2)
                self.chassis.distance_pid.enable()
        except:
            self.onException()

        self.chassis.inputs = [-rescale_js(self.joystick.getY(), deadzone=0.05, exponential=1.2),
                            - rescale_js(self.joystick.getX(), deadzone=0.05, exponential=1.2),
                            - rescale_js(self.joystick.getZ(), deadzone=0.2, exponential=5.0, rate=0.6),
                            (self.joystick.getThrottle() - 1.0) / -2.0
                            ]
        for input in self.chassis.inputs[0:3]:
            if input != 0.0:
                # Break out of auto if we move the stick
                self.chassis.distance_pid.disable()
                self.chassis.range_setpoint = None
                self.chassis.track_vision = False
                self.chassis.field_oriented = True
        self.putData()


    def testPeriodic(self):
        """This function is called periodically during test mode."""
        wpilib.LiveWindow.run()

    def debounce(self, button, gamepad = False):
        device = None
        if gamepad:
            pressed_buttons = self.pressed_buttons_gp
            device = self.gamepad
        else:
            pressed_buttons = self.pressed_buttons_js
            device = self.joystick
        if device.getRawButton(button):
            if button in pressed_buttons:
                return False
            else:
                pressed_buttons.add(button)
                return True
        else:
            pressed_buttons.discard(button)
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
