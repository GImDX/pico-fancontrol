# status.py - Raspberry Pi Pico 状态检查脚本

import os
import time
import math
import _thread
from machine import Pin, PWM, ADC, freq

def run():
    print("\n\n=== MicroPython 状态工具 ===\n")
    print("使用 help() 查看内建命令\nhelp():")
    help()
    print("\n--- 清屏指令 --- \nprint(\"\\x1b[2J\\x1b[H\")")

    # 系统信息
    print("\n--- 系统信息 ---")
    print(os.uname())

    # 当前时间
    print("\n--- 系统运行毫秒数 ---")
    print("time.ticks_ms():", time.ticks_ms(), "ms")

    # 文件列表
    print("\n--- 内部文件系统 ---")
    print("文件列表:")
    print(os.listdir())

    # 文件系统空间（单位: KB）
    stat = os.statvfs('/')
    total_kb = stat[0] * stat[2] // 1024
    free_kb = stat[0] * stat[3] // 1024
    print("总空间:\n {} KB".format(total_kb))
    print("剩余空间:\n {} KB".format(free_kb))

    # 当前主频（单位: MHz）
    cpu_mhz = freq() // 1_000_000
    print("\n--- 当前主频 ---")
    print("CPU Frequency:\n", cpu_mhz, "MHz")

    # 芯片温度
    print("\n--- 芯片温度传感器 ---")
    sensor_temp = ADC(4)
    conversion_factor = 3.3 / 65535
    reading = sensor_temp.read_u16()
    voltage = reading * conversion_factor
    temperature_c = 27 - (voltage - 0.706)/0.001721
    print("温度:\n", round(temperature_c, 2), "°C")

    # 引脚功能
    print_pico_pinout_full()

# 板载 LED 呼吸灯（无限循环）
def led_breath():
    print("\n--- 板载 LED 呼吸灯启动中（Ctrl+C 停止） ---\n")
    led_pwm = PWM(Pin(25))
    led_pwm.freq(1000)
    while True:
        for i in range(100):
            duty = int((1 - math.cos(math.pi * i / 100)) * 32767.5)
            led_pwm.duty_u16(duty)
            time.sleep(0.01)
        for i in range(100):
            duty = int((1 - math.cos(math.pi * (100 - i) / 100)) * 32767.5)
            led_pwm.duty_u16(duty)
            time.sleep(0.01)

def print_pico_pinout_full():
    left = [
        ["UART0 TX", "I2C0 SDA", "SPI0 RX",  "GP0",  " 1"],
        ["UART0 RX", "I2C0 SCL", "SPI0 CSn", "GP1",  " 2"],
        ["",         "",         "",         "GND",  " 3"],
        ["",         "I2C1 SDA", "SPI0 SCK", "GP2",  " 4"],
        ["",         "I2C1 SCL", "SPI0 TX",  "GP3",  " 5"],
        ["UART1 TX", "I2C0 SDA", "SPI0 RX",  "GP4",  " 6"],
        ["UART1 RX", "I2C0 SCL", "SPI0 CSn", "GP5",  " 7"],
        ["",         "",         "",         "GND",  " 8"],
        ["SPI0 RX",  "I2C1 SDA", "SPI0 SCK", "GP6",  " 9"],
        ["SPI0 CSn", "I2C1 SCL", "SPI0 TX",  "GP7",  "10"],
        ["UART1 TX", "I2C0 SDA", "SPI0 RX",  "GP8",  "11"],
        ["UART1 RX", "I2C0 SCL", "SPI0 CSn", "GP9",  "12"],
        ["",         "",         "",         "GND",  "13"],
        ["",         "I2C1 SDA", "SPI1 SCK", "GP10", "14"],
        ["",         "I2C1 SCL", "SPI1 TX",  "GP11", "15"],
        ["UART0 TX", "I2C0 SDA", "SPI1 RX",  "GP12", "16"],
        ["UART0 RX", "I2C0 SCL", "SPI1 CSn", "GP13", "17"],
        ["",         "",         "",         "GND",  "18"],
        ["",         "I2C1 SDA", "SPI1 SCK", "GP14", "19"],
        ["",         "I2C1 SCL", "SPI1 TX",  "GP15", "20"]
    ]

    right = [
        ["",         "",         "",         "VBUS",     "40"],
        ["",         "",         "",         "VSYS",     "39"],
        ["",         "",         "",         "GND",      "38"],
        ["",         "",         "",         "3V3_EN",   "37"],
        ["",         "",         "",         "3V3(OUT)", "36"],
        ["",         "",         "ADC_VREF", "",         "35"],
        ["",         "",         "ADC2",     "GP28",     "34"],
        ["",         "",         "AGND",     "GND",      "33"],
        ["",         "I2C1 SCL", "ADC1",     "GP27",     "32"],
        ["",         "I2C1 SDA", "ADC0",     "GP26",     "31"],
        ["",         "",         "",         "RUN",      "30"],
        ["",         "",         "",         "GP22",     "29"],
        ["",         "",         "",         "GND",      "28"],
        ["",         "I2C0 SCL", "",         "GP21",     "27"],
        ["",         "I2C0 SDA", "",         "GP20",     "26"],
        ["",         "I2C1 SCL", "SPI1 TX",  "GP19",     "25"],
        ["",         "I2C1 SDA", "SPI1 SCK", "GP18",     "24"],
        ["",         "",         "",         "GND",      "23"],
        ["UART0 RX", "I2C0 SCL", "SPI1 CSn", "GP17",     "22"],
        ["UART0 TX", "I2C0 SDA", "SPI1 RX",  "GP16",     "21"],
    ]

    print("\n--- PINOUT ---")
    print("┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                                           Raspberry Pi Pico Pinout                                          │")
    print("├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤")
    print("│ Func1    │ Func2    │ Func3    │ GPIO     │ Pin      │ Pin      │ GPIO     │ Func1    │ Func2    │ Func3    │")
    print("├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤")

    for l, r in zip(left, right):
        print("│ {0:<8} │ {1:<8} │ {2:<8} │ {3:<8} │ {4:<8} │ {5:<8} │ {6:<8} │ {7:<8} │ {8:<8} │ {9:<8} │".format(
            l[0], l[1], l[2], l[3], l[4],
            r[4], r[3], r[2], r[1], r[0]
        ))

    print("└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘")

# 仅在直接运行本文件时执行
if __name__ == "__main__":
    run()
    # 启动 LED 呼吸灯线程
    _thread.start_new_thread(led_breath, ())
    while(1):
        time.sleep(1)
