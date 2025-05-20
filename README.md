# Raspberry Pi Pico Fan RPM Controller

本项目基于 MicroPython 和 Raspberry Pi Pico，利用 PIO 实现风扇转速精确检测，并支持通过 USB 串口控制 PWM 占空比调速。同时包含板载 LED 呼吸灯、系统信息显示、引脚图输出等功能。

## 功能特色

- 🌪️ **风扇转速检测（RPM）**：使用 PIO 检测负脉冲宽度，滤除干扰信号，最小脉宽可调。
- ⚙️ **PWM 控制风扇速度**：通过 `fan_pwm.txt` 或 USB 指令设置占空比，PWM频率可调。
- 🌡️ **温度采集**：读取 Pico 内部温度传感器，适合用于机箱温度显示。
- 💡 **呼吸灯效果**：板载 LED 显示状态。
- 🛡️ **WDT 看门狗保护**：异常自动重启，支持维护模式。
- 🧾 **状态报告脚本**：显示系统信息和精美引脚图。

## 使用方法

### 1. 启动脚本

将以下文件烧录到 Raspberry Pi Pico：

- `main.py` - 主控制程序
- `status.py` - 状态查看工具

### 2. 设置 PWM 占空比

通过 USB 串口发送指令（支持 `screen` / `minicom` 等工具）：

```
PWM=75
```

设置风扇占空比为 75%。设置后会保存至 `fan_pwm.txt` 以便下次启动自动加载。

### 3. 维护模式（禁用 WDT）

创建 `no_wdt` 文件，防止意外重启：（Ctrl+C结束程序时也会自动创建，狗咬重连后看门狗将禁能）

```python
with open("no_wdt", "w") as f:
    f.write("maintenance")
```

删除该文件以恢复 WDT：

```python
import os
os.remove("no_wdt")
```

### 4. 查看系统状态与引脚图

运行：

```python
import status
status.run()
```

```
...
--- PINOUT ---
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           Raspberry Pi Pico Pinout                                          │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ Func1    │ Func2    │ Func3    │ GPIO     │ Pin      │ Pin      │ GPIO     │ Func1    │ Func2    │ Func3    │
├──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ UART0 TX │ I2C0 SDA │ SPI0 RX  │ GP0      │  1       │ 40       │ VBUS     │          │          │          │
│ UART0 RX │ I2C0 SCL │ SPI0 CSn │ GP1      │  2       │ 39       │ VSYS     │          │          │          │
│          │          │          │ GND      │  3       │ 38       │ GND      │          │          │          │
│          │ I2C1 SDA │ SPI0 SCK │ GP2      │  4       │ 37       │ 3V3_EN   │          │          │          │
│          │ I2C1 SCL │ SPI0 TX  │ GP3      │  5       │ 36       │ 3V3(OUT) │          │          │          │
│ UART1 TX │ I2C0 SDA │ SPI0 RX  │ GP4      │  6       │ 35       │          │ ADC_VREF │          │          │
│ UART1 RX │ I2C0 SCL │ SPI0 CSn │ GP5      │  7       │ 34       │ GP28     │ ADC2     │          │          │
│          │          │          │ GND      │  8       │ 33       │ GND      │ AGND     │          │          │
│ SPI0 RX  │ I2C1 SDA │ SPI0 SCK │ GP6      │  9       │ 32       │ GP27     │ ADC1     │ I2C1 SCL │          │
│ SPI0 CSn │ I2C1 SCL │ SPI0 TX  │ GP7      │ 10       │ 31       │ GP26     │ ADC0     │ I2C1 SDA │          │
│ UART1 TX │ I2C0 SDA │ SPI0 RX  │ GP8      │ 11       │ 30       │ RUN      │          │          │          │
│ UART1 RX │ I2C0 SCL │ SPI0 CSn │ GP9      │ 12       │ 29       │ GP22     │          │          │          │
│          │          │          │ GND      │ 13       │ 28       │ GND      │          │          │          │
│          │ I2C1 SDA │ SPI1 SCK │ GP10     │ 14       │ 27       │ GP21     │          │ I2C0 SCL │          │
│          │ I2C1 SCL │ SPI1 TX  │ GP11     │ 15       │ 26       │ GP20     │          │ I2C0 SDA │          │
│ UART0 TX │ I2C0 SDA │ SPI1 RX  │ GP12     │ 16       │ 25       │ GP19     │ SPI1 TX  │ I2C1 SCL │          │
│ UART0 RX │ I2C0 SCL │ SPI1 CSn │ GP13     │ 17       │ 24       │ GP18     │ SPI1 SCK │ I2C1 SDA │          │
│          │          │          │ GND      │ 18       │ 23       │ GND      │          │          │          │
│          │ I2C1 SDA │ SPI1 SCK │ GP14     │ 19       │ 22       │ GP17     │ SPI1 CSn │ I2C0 SCL │ UART0 RX │
│          │ I2C1 SCL │ SPI1 TX  │ GP15     │ 20       │ 21       │ GP16     │ SPI1 RX  │ I2C0 SDA │ UART0 TX │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
...
```

## 依赖环境

- MicroPython for RP2040 (推荐使用官方构建版本)
- Raspberry Pi Pico 板卡

## 示例输出

```
Fan RPM: 1320.0 TEMP: 34.5
✅ PWM updated: 75.0%
```

## 参考资料

- [RP2040 Python SDK Datasheet](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf)
- [MicroPython PIO Reference](https://github.com/raspberrypi/pico-micropython-examples)
