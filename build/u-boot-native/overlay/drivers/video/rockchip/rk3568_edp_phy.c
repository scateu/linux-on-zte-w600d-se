#include <dm.h>
#include <generic-phy.h>
#include <reset.h>
#include <rockchip_edp_phy.h>
#include <asm/io.h>
#include <linux/delay.h>
#include <linux/iopoll.h>

#define PHY_CON0		0x00
#define PHY_CON1		0x04
#define PHY_CON2		0x08
#define PHY_CON3		0x0c
#define PHY_CON4		0x10
#define PHY_CON5		0x14
#define PHY_CON6		0x18
#define PHY_CON8		0x20
#define PHY_CON9		0x24
#define PHY_CON10	0x28
#define PHY_CON11	0x2c
#define PHY_STATUS0	0x30

struct rk3568_edp_phy_priv {
	void *regs;
	struct reset_ctl reset;
};

static const u8 amplitudes[4][4] = {
	{ 1, 2, 3, 5 },
	{ 3, 5, 6, 0 },
	{ 5, 7, 0, 0 },
	{ 7, 0, 0, 0 },
};

static const u8 emphases[4][4] = {
	{ 0, 4, 8, 15 },
	{ 0, 7, 6, 0 },
	{ 0, 4, 0, 0 },
	{ 0, 0, 0, 0 },
};

static void phy_update(struct rk3568_edp_phy_priv *priv, u32 offset,
		       u32 mask, u32 value)
{
	writel((mask << 16) | (value & mask), priv->regs + offset);
}

static int rk3568_edp_phy_power_on(struct phy *phy)
{
	struct rk3568_edp_phy_priv *priv = dev_get_priv(phy->dev);
	int ret;

	ret = reset_assert(&priv->reset);
	if (ret)
		return ret;
	udelay(100);
	ret = reset_deassert(&priv->reset);
	if (ret)
		return ret;
	udelay(100);
	phy_update(priv, PHY_CON10, 0x37, 0x07);
	phy_update(priv, PHY_CON0, 0xff3, 0xff1);
	udelay(100);
	phy_update(priv, PHY_CON11, 0x7f77, 0x4501);
	phy_update(priv, PHY_CON10, 0x03, 0);
	udelay(100);
	phy_update(priv, PHY_CON10, 0x04, 0);
	printf("W600D PHY: reset; AUX powered, inherited link discarded\n");
	return 0;
}

static int rk3568_edp_phy_power_off(struct phy *phy)
{
	struct rk3568_edp_phy_priv *priv = dev_get_priv(phy->dev);

	phy_update(priv, PHY_CON0, 0xff3, 0xff1);
	phy_update(priv, PHY_CON10, 0x07, 0x07);
	return 0;
}

static int rk3568_edp_phy_configure(struct phy *phy, void *params)
{
	struct rk3568_edp_phy_priv *priv = dev_get_priv(phy->dev);
	struct rockchip_edp_phy_config *config = params;
	u32 active, status;
	unsigned int lane;
	int ret;

	if (!config || (config->lanes != 1 && config->lanes != 2 &&
			config->lanes != 4))
		return -EINVAL;
	if (config->set_rate && config->link_rate != 1620 &&
	    config->link_rate != 2700)
		return -EINVAL;
	if (config->set_voltages) {
		for (lane = 0; lane < config->lanes; lane++) {
			if (config->voltage[lane] > 3 || config->pre[lane] > 3 ||
			    config->voltage[lane] + config->pre[lane] > 3)
				return -EINVAL;
		}
	}
	if (config->set_rate) {
		phy_update(priv, PHY_CON0, 0xff0, 0xff0);
		udelay(100);
		phy_update(priv, PHY_CON5, 0x300, 0x300);
		phy_update(priv, PHY_CON0, 1, 1);
		phy_update(priv, PHY_CON1, 0x7fff,
			   config->link_rate == 1620 ? 0x4380 : 0x3840);
		phy_update(priv, PHY_CON2, 0x73f,
			   config->link_rate == 1620 ? 0x110 : 0x100);
		phy_update(priv, PHY_CON8, 0xffff, 0x0800);
		phy_update(priv, PHY_CON9, 0xffff, 0);
		phy_update(priv, PHY_CON6, 0xfbff,
			   config->ssc ? 0xa97d : 0);
		phy_update(priv, PHY_CON0, 1, 0);
		active = (1U << config->lanes) - 1;
		phy_update(priv, PHY_CON0, 0xf0, (~active & 0xf) << 4);
		ret = readl_poll_timeout(priv->regs + PHY_STATUS0, status,
					status & BIT(0), 10000);
		if (ret) {
			printf("W600D PHY: PLL timeout, status=%08x\n", status);
			return ret;
		}
		phy_update(priv, PHY_CON5, 0x300, 0);
		phy_update(priv, PHY_CON0, 0xf00, (~active & 0xf) << 8);
		printf("W600D PHY: %u Mb/s x %u lanes, PLL=%08x\n",
		       config->link_rate, config->lanes, status);
	}
	if (config->set_voltages) {
		for (lane = 0; lane < config->lanes; lane++) {
			unsigned int voltage = config->voltage[lane];
			unsigned int pre = config->pre[lane];

			phy_update(priv, PHY_CON4, 7U << (lane * 4),
				   amplitudes[voltage][pre] << (lane * 4));
			phy_update(priv, PHY_CON5, 3U << (lane * 2),
				   1U << (lane * 2));
			phy_update(priv, PHY_CON3, 15U << (lane * 4),
				   emphases[voltage][pre] << (lane * 4));
		}
	}
	return 0;
}

static int rk3568_edp_phy_probe(struct udevice *dev)
{
	struct rk3568_edp_phy_priv *priv = dev_get_priv(dev);

	priv->regs = dev_read_addr_ptr(dev);
	if (!priv->regs)
		return -EINVAL;
	return reset_get_by_name(dev, "apb", &priv->reset);
}

static const struct phy_ops rk3568_edp_phy_ops = {
	.power_on = rk3568_edp_phy_power_on,
	.power_off = rk3568_edp_phy_power_off,
	.configure = rk3568_edp_phy_configure,
};

static const struct udevice_id rk3568_edp_phy_ids[] = {
	{ .compatible = "rockchip,rk3568-edp-phy" },
	{ }
};

U_BOOT_DRIVER(rk3568_edp_phy) = {
	.name = "rk3568_edp_phy",
	.id = UCLASS_PHY,
	.of_match = rk3568_edp_phy_ids,
	.probe = rk3568_edp_phy_probe,
	.ops = &rk3568_edp_phy_ops,
	.priv_auto = sizeof(struct rk3568_edp_phy_priv),
};
