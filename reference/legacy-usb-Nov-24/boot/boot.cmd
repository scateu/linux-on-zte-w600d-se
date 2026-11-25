echo "== Stage 2: Mainline U-Boot (Injecting True Laptop eDP Driver Map) =="

# 1. 正常加载内核与原厂设备树
load usb 0:1 0x02100000 /boot/vmlinuz-6.18.45-current-arm64
load usb 0:1 0x0a000000 /boot/rk3568-evb1-v10.dtb

# 2. 激活内存中的 DTB 基址
fdt addr 0x0a000000

# 3. 【彻底关闭错误的原厂 MIPI 屏】
fdt set /dsi@fe060000 status "disabled"
fdt set /dsi@fe060000/panel@0 status "disabled"

# 4. 【强行开启笔记本原生 eDP 通道与 PHY 物理层】
fdt set /edp@fe0c0000 status "okay"
fdt set /edp-phy@fdcb0000 status "okay"

# 5. 【修正 VOP2 视频输出接口：告诉内核将信号切给 eDP 供电桥】
fdt set /vop@fe040000/ports/port@0/endpoint@2 status "disabled"  /* 关闭 MIPI 端口端点 */
fdt set /vop@fe040000/ports/port@1/endpoint@4 status "okay"      /* 强制激活 eDP 路由端点 */

# 6. 【修正屏幕供电：强行锁定背光一直有电】
fdt set /regulator-vcc3v3-lcd0-n regulator-always-on
fdt set /regulator-vcc3v3-lcd0-n regulator-boot-on

# 7. 内核标准启动参数（移除没用的 simplefb，改用原生控制台亮屏）
setenv bootargs "earlycon=uart8250,mmio32,0xfe660000 console=tty0 root=/dev/ram0 rw rootwait ignore_loglevel clk_ignore_unused"

# 8. 彻底关闭容易超时的 U-Boot USB 驱动并跳转
usb stop
booti 0x02100000 - 0x0a000000

