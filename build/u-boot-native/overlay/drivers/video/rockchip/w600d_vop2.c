#include <clk.h>
#include <display.h>
#include <dm.h>
#include <panel.h>
#include <reset.h>
#include <video.h>
#include <asm/cache.h>
#include <asm/io.h>
#include <dm/device-internal.h>
#include <dm/uclass-internal.h>
#include <linux/delay.h>
#include <linux/iopoll.h>

#define VOP_CFG_DONE		0x000
#define VOP_AUTO_GATING		0x008
#define VOP_DSP_IF_EN		0x028
#define VOP_DSP_IF_POL		0x030
#define VOP_VP1_INT_CLR		0x0b4
#define VOP_VP1_INT_RAW		0x0bc
#define VOP_OVL_CTRL		0x600
#define VOP_LAYER_SEL		0x604
#define VOP_PORT_SEL		0x608
#define VOP_VP1_BG_MIX		0x6e4
#define VOP_CLUSTER_DLY		0x6f0
#define VOP_SMART_DLY		0x6f8
#define VOP_VP1			0xd00
#define VOP_SMART0		0x1c00
#define VP_STANDBY		BIT(31)
#define VP_FRAME_START		BIT(5)
#define CRU_CLKSEL(offset)	(0x100 + (offset) * 4)
#define CRU_CLKGATE(offset)	(0x300 + (offset) * 4)
#define PMU_CLKGATE(offset)	(0x100 + (offset) * 4)
#define PANEL_WIDTH		1920
#define PANEL_HEIGHT		1080
#define PANEL_EDID_CLOCK	141020000
#define PANEL_DCLK		141000000
#define PANEL_VPLL		(PANEL_DCLK * 4)

struct w600d_vop2_priv {
	void *vop;
	void *cru;
	void *pmucru;
	void *pmu;
	void *iommu[2];
	struct reset_ctl_bulk resets;
};

static void w600d_update(void *base, u32 offset, u32 mask, u32 value)
{
	writel((mask << 16) | (value & mask), base + offset);
}

static int w600d_display_power(struct w600d_vop2_priv *priv)
{
	u32 status;
	int ret;

	w600d_update(priv->pmu, 0xa0, BIT(7), 0);
	ret = readl_poll_timeout(priv->pmu + 0x98, status,
				!(status & BIT(7)), 100000);
	if (ret)
		return ret;
	w600d_update(priv->pmu, 0x50, BIT(4), 0);
	ret = readl_poll_timeout(priv->pmu + 0x60, status,
				!(status & BIT(4)), 100000);
	if (ret)
		return ret;
	ret = readl_poll_timeout(priv->pmu + 0x68, status,
				!(status & BIT(4)), 100000);
	if (ret)
		return ret;
	w600d_update(priv->cru, CRU_CLKSEL(37), 0xff03, 0x2200);
	w600d_update(priv->cru, CRU_CLKSEL(38), 0x300, 0);
	w600d_update(priv->cru, CRU_CLKGATE(20), 0x0b47, 0);
	w600d_update(priv->cru, CRU_CLKGATE(21), 0x0300, 0);
	w600d_update(priv->cru, CRU_CLKGATE(31), 0x6000, 0);
	w600d_update(priv->cru, CRU_CLKGATE(34), 0x4000, 0);
	w600d_update(priv->pmucru, PMU_CLKGATE(2), 0x8000, 0);
	printf("W600D VOP2: VO powered/unidled; display/PWM gates enabled\n");
	return 0;
}

static int w600d_display_clocks(struct udevice *dev)
{
	struct w600d_vop2_priv *priv = dev_get_priv(dev);
	struct clk vpll, dclk, aclk;
	ulong rate, vpll_rate, aclk_rate;
	int ret;

	ret = clk_get_by_name(dev, "vpll", &vpll);
	if (ret)
		return ret;
	ret = clk_get_by_name(dev, "dclk", &dclk);
	if (ret)
		return ret;
	ret = clk_get_by_name(dev, "aclk", &aclk);
	if (ret)
		return ret;
	rate = clk_set_rate(&vpll, PANEL_VPLL);
	if (IS_ERR_VALUE(rate))
		return (int)rate;
	ret = clk_set_parent(&dclk, &vpll);
	if (ret)
		return ret;
	w600d_update(priv->cru, CRU_CLKSEL(40), 0x0cff, 0x0403);
	rate = clk_set_rate(&aclk, 300000000);
	if (IS_ERR_VALUE(rate))
		return (int)rate;
	rate = clk_get_rate(&dclk);
	if (IS_ERR_VALUE(rate))
		return (int)rate;
	vpll_rate = clk_get_rate(&vpll);
	aclk_rate = clk_get_rate(&aclk);
	printf("W600D clocks: VPLL=%lu DCLK_VOP1=%lu ACLK=%lu\n",
	       vpll_rate, rate, aclk_rate);
	printf("W600D VPLL raw: con0=%08x con1=%08x con2=%08x mode=%08x\n",
	       readl(priv->cru + 0xa0), readl(priv->cru + 0xa4),
	       readl(priv->cru + 0xa8), readl(priv->cru + 0xc0));
	if (vpll_rate != PANEL_VPLL || rate != PANEL_DCLK ||
	    aclk_rate != 300000000)
		return -ERANGE;
	return 0;
}

static int w600d_vop2_reset(struct w600d_vop2_priv *priv)
{
	static const u32 windows[] = { 0x1000, 0x1200, 0x1810,
				      0x1a10, 0x1c10, 0x1e10 };
	u32 enabled = 0, status;
	unsigned int index;
	int ret;

	ret = reset_assert_bulk(&priv->resets);
	if (ret)
		return ret;
	udelay(100);
	ret = reset_deassert_bulk(&priv->resets);
	if (ret)
		return ret;
	udelay(100);
	for (index = 0; index < ARRAY_SIZE(windows); index++) {
		if (readl(priv->vop + windows[index]) & BIT(0))
			enabled |= BIT(index);
	}
	printf("W600D VOP2: reset verified, inherited window mask=%02x\n",
	       enabled);
	if (enabled)
		return -EIO;
	for (index = 0; index < ARRAY_SIZE(priv->iommu); index++) {
		writel(6, priv->iommu[index] + 0x08);
		ret = readl_poll_timeout(priv->iommu[index] + 0x04, status,
					!(status & (BIT(0) | BIT(2))), 100000);
		if (ret)
			return ret;
	}
	writel(VP_STANDBY, priv->vop + 0xc00);
	writel(VP_STANDBY, priv->vop + 0xd00);
	writel(VP_STANDBY, priv->vop + 0xe00);
	writel(0, priv->vop + VOP_DSP_IF_EN);
	writel(BIT(15), priv->vop + VOP_CFG_DONE);
	writel(0, priv->vop + VOP_AUTO_GATING);
	return 0;
}

static void w600d_vop2_mode(struct w600d_vop2_priv *priv,
			   const struct display_timing *timing, ulong framebuffer)
{
	u32 width = timing->hactive.typ, height = timing->vactive.typ;
	u32 hsync = timing->hsync_len.typ, vsync = timing->vsync_len.typ;
	u32 hstart = hsync + timing->hback_porch.typ;
	u32 vstart = vsync + timing->vback_porch.typ;
	u32 htotal = hstart + width + timing->hfront_porch.typ;
	u32 vtotal = vstart + height + timing->vfront_porch.typ;
	u32 area = (height - 1) << 16 | (width - 1);
	void *vp = priv->vop + VOP_VP1;
	void *win = priv->vop + VOP_SMART0;

	writel(0, win + 0x00);
	writel((1 << 4) | (2 << 12), win + 0x04);
	writel(framebuffer, win + 0x14);
	writel(0, win + 0x18);
	writel(width, win + 0x1c);
	writel(area, win + 0x20);
	writel(area, win + 0x24);
	writel(0, win + 0x28);
	writel(0, win + 0x30);
	writel(0x10001000, win + 0x34);
	writel(0, win + 0x40);
	writel(0, win + 0x70);
	writel(0, win + 0xa0);
	writel(0, win + 0xd0);
	writel(BIT(0), win + 0x10);
	writel(BIT(28), priv->vop + VOP_OVL_CTRL);
	writel(0x00762103, priv->vop + VOP_LAYER_SEL);
	writel(0x10000808, priv->vop + VOP_PORT_SEL);
	writel(0, priv->vop + VOP_CLUSTER_DLY);
	writel(20 << 16, priv->vop + VOP_SMART_DLY);
	writel(40U << 24, priv->vop + VOP_VP1_BG_MIX);
	writel(0, vp + 0x04);
	writel(0, vp + 0x08);
	writel(0, vp + 0x10);
	writel(0, vp + 0x2c);
	writel((40 + (width >> 1) - 1) << 16 | hsync, vp + 0x30);
	writel(hstart << 16 | (hstart + width), vp + 0x34);
	writel(vstart << 16 | (vstart + height), vp + 0x38);
	writel(0x10001000, vp + 0x3c);
	writel(0, vp + 0x40);
	writel(htotal << 16 | hsync, vp + 0x48);
	writel(hstart << 16 | (hstart + width), vp + 0x4c);
	writel(vtotal << 16 | vsync, vp + 0x50);
	writel(vstart << 16 | (vstart + height), vp + 0x54);
	writel(0, vp + 0x60);
	writel(BIT(3) | (1 << 14), priv->vop + VOP_DSP_IF_EN);
	writel(BIT(28), priv->vop + VOP_DSP_IF_POL);
	writel((VP_FRAME_START << 16) | VP_FRAME_START,
	       priv->vop + VOP_VP1_INT_CLR);
	writel(BIT(15) | BIT(1) | BIT(17), priv->vop + VOP_CFG_DONE);
	writel(0, vp);
	printf("W600D VOP2: Smart0 -> VP1 -> eDP, %ux%u, fb=%08lx\n",
	       width, height, framebuffer);
}

static int w600d_vop2_bind(struct udevice *dev)
{
	struct video_uc_plat *plat = dev_get_uclass_plat(dev);

	plat->size = PANEL_WIDTH * PANEL_HEIGHT * 4;
	plat->align = 1 << 20;
	return 0;
}

static int w600d_vop2_probe(struct udevice *dev)
{
	struct w600d_vop2_priv *priv = dev_get_priv(dev);
	struct video_uc_plat *plat = dev_get_uclass_plat(dev);
	struct video_priv *video = dev_get_uclass_priv(dev);
	struct display_plat *display_plat;
	struct display_timing timing;
	struct udevice *panel, *display;
	u32 *pixels = (void *)plat->base;
	u32 status;
	unsigned int index;
	int ret;

	priv->vop = dev_read_addr_index_ptr(dev, 0);
	priv->cru = dev_read_addr_index_ptr(dev, 1);
	priv->pmucru = dev_read_addr_index_ptr(dev, 2);
	priv->pmu = dev_read_addr_index_ptr(dev, 3);
	priv->iommu[0] = dev_read_addr_index_ptr(dev, 4);
	priv->iommu[1] = dev_read_addr_index_ptr(dev, 5);
	if (!priv->vop || !priv->cru || !priv->pmucru || !priv->pmu ||
	    !priv->iommu[0] || !priv->iommu[1] || plat->base > 0xffffffffUL)
		return -EINVAL;
	ret = reset_get_bulk(dev, &priv->resets);
	if (ret)
		return ret;
	ret = w600d_display_power(priv);
	if (ret)
		goto fail;
	ret = uclass_get_device_by_phandle(UCLASS_PANEL, dev,
					 "rockchip,panel", &panel);
	if (ret)
		goto fail;
	ret = panel_get_display_timing(panel, &timing);
	if (ret)
		goto fail;
	if (timing.hactive.typ != PANEL_WIDTH ||
	    timing.vactive.typ != PANEL_HEIGHT ||
	    timing.pixelclock.typ != PANEL_EDID_CLOCK) {
		ret = -EINVAL;
		goto fail;
	}
	ret = w600d_display_clocks(dev);
	if (ret)
		goto fail;
	ret = w600d_vop2_reset(priv);
	if (ret)
		goto fail;
	ret = uclass_find_device_by_ofnode(UCLASS_DISPLAY,
			ofnode_parse_phandle(dev_ofnode(dev), "rockchip,edp", 0),
			&display);
	if (ret)
		goto fail;
	display_plat = dev_get_uclass_plat(display);
	display_plat->source_id = 1;
	display_plat->src_dev = dev;
	ret = device_probe(display);
	if (ret)
		goto fail;
	for (index = 0; index < PANEL_WIDTH * PANEL_HEIGHT; index++)
		pixels[index] = 0xff101820;
	flush_dcache_range(plat->base,
			   ALIGN(plat->base + plat->size, ARCH_DMA_MINALIGN));
	w600d_vop2_mode(priv, &timing, plat->base);
	ret = display_enable(display, 24, &timing);
	if (ret)
		goto fail;
	ret = readl_poll_timeout(priv->vop + VOP_VP1_INT_RAW, status,
				status & VP_FRAME_START, 100000);
	if (ret)
		goto fail;
	video->xsize = PANEL_WIDTH;
	video->ysize = PANEL_HEIGHT;
	video->bpix = VIDEO_BPP32;
	video->format = VIDEO_X8R8G8B8;
	video_set_flush_dcache(dev, true);
	printf("W600D native display READY: fresh VP1 frame, no takeover path\n");
	return 0;

fail:
	printf("W600D native display FAILED: %d (serial remains available)\n",
	       ret);
	return ret;
}

static const struct udevice_id w600d_vop2_ids[] = {
	{ .compatible = "zte,w600d-vop2-native" },
	{ }
};

U_BOOT_DRIVER(w600d_vop2) = {
	.name = "w600d_vop2_native",
	.id = UCLASS_VIDEO,
	.of_match = w600d_vop2_ids,
	.bind = w600d_vop2_bind,
	.probe = w600d_vop2_probe,
	.priv_auto = sizeof(struct w600d_vop2_priv),
};
