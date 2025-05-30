from machine import Pin, PWM, WDT, ADC
import rp2
import time
import math
import _thread
import os
import sys
import select

# -------------------------------
# 参数定义（可修改）
# -------------------------------

# 常量
PWM_FREQ = 25000               # FAN PWM 控制频率（Hz）
FILTER_US = 1000               # 低电平脉冲最小宽度（μs）
SAMPLE_PERIOD_S = 2.0          # RPM 采样周期（秒）
PULSES_PER_REV = 2             # 每转脉冲数（风扇规格）

LED_PWM_FREQ = 1000            # LED PWM 控制频率（Hz）
LED_MAX_BRIGHT = 0.5           # LED 最大亮度 0-1.0

# 全局状态变量
pulse_count = 0
pulse_start = 0
pulse_end = 0
current_rpm = 0
_last_sample_time = 0
fan_pwm = None
PWM_DUTY_PERCENT = 0
wdt = None

# -------------------------------
# 读取温度（ADC4）
# -------------------------------

def temperature():
    voltage = ADC(4).read_u16() * 3.3 / 65535
    return 27 - (voltage - 0.706) / 0.001721

# -------------------------------
# PWM 设置读写
# -------------------------------

# 从fan_pwm.txt读取PWM
def load_pwm_setting():
    try:
        with open("fan_pwm.txt") as f:
            return float(f.read().strip())
    except:
        return 50.0  # 默认值

# 保存PWM到fan_pwm.txt
def save_pwm_setting(value):
    try:
        with open("fan_pwm.txt", "w") as f:
            f.write(f"{value:.1f}")
    except:
        print("⚠️ 写入 fan_pwm.txt 失败")

# -------------------------------
# 从USB CDC读取解析FAN PWM 格式 "PWM=100\r\n"
# -------------------------------

def handle_serial_command():
    global PWM_DUTY_PERCENT
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        if line.startswith("PWM="):
            try:
                value = float(line[4:])
                value = max(0.0, min(100.0, value))  # 限制范围
                PWM_DUTY_PERCENT = value
                fan_pwm.duty_u16(int(PWM_DUTY_PERCENT / 100 * 65535))
                save_pwm_setting(PWM_DUTY_PERCENT)
                print(f"✅ PWM updated: {PWM_DUTY_PERCENT:.1f}%")
            except ValueError:
                print("⚠️ 无效数值，格式应为 PWM=xx")

# -------------------------------
# PIO 程序：检测低电平 负脉冲宽度≥ FILTER_US
# -------------------------------

@rp2.asm_pio()
def tach_filtered_neg():
    pull(block)             # 从主机 TX FIFO 拉取一个值到 OSR（只执行一次），设定脉冲宽度阈值（单位：us）
    # pull(block)           # 测试，多次拉取

    wrap_target()           # 标记程序开始的循环点
    mov(x, osr)             # 将 OSR 的值（脉宽阈值）赋给 X 寄存器，作为倒计时器

    # mov(y, x)               # 测试
    # jmp("skip")             # 测试，set(x, N)有限制N<31，但pull mov push无此限制，最大32bit，超出截断

    wait(0, pin, 0)         # 等待引脚为低电平，即负脉冲开始
    set(y, 0)               # 设置 Y = 0，表示默认丢弃该脉冲（初始化）

    label("loop")           # 进入计数循环
    jmp(pin, "skip")        # 如果引脚变成高电平（脉冲太短），跳过后续，丢弃脉冲
    jmp(x_dec, "loop")      # 如果 X 仍大于 0，则减一并继续循环（每次循环延迟 1us）
    set(y, 1)               # 成功完成倒计，说明脉冲持续时间 ≥ 阈值，标记为有效

    label("skip")           # 跳转标签：进入这里说明脉冲结束，或计时完成
    mov(isr, y)             # 将 Y（0 或 1）转移到 ISR
    push(block)             # 将 ISR 推送到 RX FIFO，让主控读取 Y 值
    irq(block, 0)           # 向主机发出中断信号（IRQ 0），通知状态变化
    wait(1, pin, 0)         # 等待引脚恢复为高电平，准备下一次检测

    wrap()                  # 标记程序循环结尾，回到 wrap_target

# 无脉宽过滤版本，大部分风扇有窄脉宽干扰，无法使用
# @rp2.asm_pio()
# def tach_filtered_neg():
#     wrap_target()
#     wait(0, pin, 0)       # 等待低电平（下降沿）
#     irq(block, 0)         # 触发中断
#     wait(1, pin, 0)       # 等待高电平恢复
#     wrap()

def irq_handler(sm):
    global pulse_count
    flags = sm.irq().flags()
    # print("flags: ", flags)
    if flags & 1:
        #  print("sm.rx_fifo()", sm.rx_fifo())
        #  print("sm.tx_fifo()", sm.tx_fifo())
         if sm.rx_fifo():
            result = sm.get()  # 读取 y 值
            # print(f"result = 0x{result:08X}")
            if result == 1:
                pulse_count += 1

# -------------------------------
# 后台线程 core1
# -------------------------------

_last_sample_time = 0
current_rpm = 0
pulse_start = 0
pulse_end = 0
def background_thread():
    global current_rpm, pulse_start, pulse_end, _last_sample_time, LED_MAX_BRIGHT
    led_pwm = PWM(Pin(25))
    led_pwm.freq(LED_PWM_FREQ)
    phase = 0.0

    while True:
        # 呼吸灯更新
        duty = int((1 - math.cos(phase)) * 32767.5 * LED_MAX_BRIGHT)
        led_pwm.duty_u16(duty)
        phase += math.pi / 200
        if phase >= 2 * math.pi:
            phase = 0

        # RPM 更新（按周期）
        now = time.ticks_ms()
        if time.ticks_diff(now, _last_sample_time) >= int(SAMPLE_PERIOD_S * 1000):
            _last_sample_time = now
            pulse_end = pulse_count
            delta = pulse_end - pulse_start
            current_rpm = (delta / PULSES_PER_REV) * (60 / SAMPLE_PERIOD_S)
            pulse_start = pulse_end  # 更新起点

        time.sleep(0.01)

# -------------------------------
# 主程序入口
# -------------------------------
def main():
    global fan_pwm, PWM_DUTY_PERCENT, wdt

    # 维护
    # 移除 main.py
    # os.remove("main.py")

    # 维护
    # with open("no_wdt", "w") as f:
        # f.write("maintenance")

    # 维护
    # os.remove("no_wdt")

    # 判断是否启用 WDT
    ENABLE_WDT = "no_wdt" not in os.listdir()
    if ENABLE_WDT:
        wdt = WDT(timeout=5000)
        print("✅ WDT 已启用")
    else:
        wdt = None
        print("⚠️ WDT 未启用（维护模式）")
        

    # 初始化 PWM
    PWM_DUTY_PERCENT = load_pwm_setting()
    PWM_DUTY_PERCENT = max(0.0, min(100.0, PWM_DUTY_PERCENT))
    fan_pwm = PWM(Pin(0))
    fan_pwm.freq(PWM_FREQ)
    duty_val = int(PWM_DUTY_PERCENT / 100 * 65535)
    # print("duty_val = ", duty_val)
    fan_pwm.duty_u16(duty_val)

    # 初始化 PIO
    tach_pin = Pin(1, Pin.IN, Pin.PULL_UP)
    sm = rp2.StateMachine(
        0, 
        tach_filtered_neg,           # pio函数 
        freq=1_000_000,              # 状态机运行速度1Mhz, 1step = 1us
        in_base=Pin(1),              # 设定基础地址为 GP1
        jmp_pin=1                    # 设置 jmp 也关联 GP1
    )
    sm.irq(handler=irq_handler)
    sm.active(1)                     # 使能状态机
    # sm.put(0xaaaa_bbbb_abcd_abcd)  # 测试，截断，多次拉取
    sm.put(FILTER_US)                # 初始设置脉宽阈值为 1000us

    # 启动后台线程
    _thread.start_new_thread(background_thread, ())

    # 主循环：每 SAMPLE_PERIOD_S 秒打印 RPM
    try:
        while True:
            handle_serial_command()
            print(f"Fan RPM:{current_rpm:7.1f} Pico TEMP:{temperature():5.1f}")
            if wdt:
                wdt.feed()  # 喂狗，防止重启
            time.sleep(2)  # 控制打印频率
    except KeyboardInterrupt:
        print("🛑 用户按下 Ctrl+C，准备退出，看门狗已禁用")
        raise
    finally:
        with open("no_wdt", "w") as f:
                f.write("maintenance")
            

# -------------------------------
# 启动
# -------------------------------
if __name__ == '__main__':
    main()
