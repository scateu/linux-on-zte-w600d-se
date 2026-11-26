#include <backlight.h>
#include <dm.h>
#include <errno.h>
#include <panel.h>
#include <asm/gpio.h>
#include <linux/delay.h>
#include <power/regulator.h>

struct w600d_panel_priv {
	struct udevice *supply;
	struct udevice *backlight;
	struct gpio_desc enable;
};

static int w600d_panel_supply(struct udevice *supply, bool enable)
{
	int ret;

	ret = regulator_set_enable(supply, enable);
	if (ret && ret != -EALREADY)
		return ret;
	ret = regulator_get_enable(supply);
	if (ret < 0)
		return ret;
	return ret == enable ? 0 : -EIO;
}

static int w600d_panel_timing(struct udevice *dev,
			      struct display_timing *timing)
{
	return ofnode_decode_display_timing(dev_ofnode(dev), 0, timing);
}

static int w600d_panel_backlight(struct udevice *dev)
{
	struct w600d_panel_priv *priv = dev_get_priv(dev);
	int ret;

	mdelay(50);
	ret = backlight_enable(priv->backlight);
	if (!ret)
		printf("W600D panel: trained video; backlight enabled\n");
	return ret;
}

static int w600d_panel_probe(struct udevice *dev)
{
	struct w600d_panel_priv *priv = dev_get_priv(dev);
	int ret;

	ret = uclass_get_device_by_phandle(UCLASS_REGULATOR, dev,
					 "power-supply", &priv->supply);
	if (ret)
		return ret;
	ret = uclass_get_device_by_phandle(UCLASS_PANEL_BACKLIGHT, dev,
					 "backlight", &priv->backlight);
	if (ret)
		return ret;
	ret = gpio_request_by_name(dev, "enable-gpios", 0, &priv->enable,
				   GPIOD_IS_OUT);
	if (ret)
		return ret;
	ret = dm_gpio_set_value(&priv->enable, 0);
	if (ret)
		goto fail;
	ret = w600d_panel_supply(priv->supply, false);
	if (ret)
		goto fail;
	printf("W600D panel: supply/enable OFF for 500 ms (cold-display test)\n");
	mdelay(500);
	ret = w600d_panel_supply(priv->supply, true);
	if (ret)
		goto fail;
	mdelay(20);
	ret = dm_gpio_set_value(&priv->enable, 1);
	if (ret)
		goto fail;
	mdelay(200);
	printf("W600D panel: supply/enable ON; backlight remains OFF\n");
	return 0;

fail:
	dm_gpio_set_value(&priv->enable, 0);
	w600d_panel_supply(priv->supply, false);
	dm_gpio_free(dev, &priv->enable);
	printf("W600D panel: power sequence failed: %d; enable GPIO released\n", ret);
	return ret;
}

static const struct panel_ops w600d_panel_ops = {
	.get_display_timing = w600d_panel_timing,
	.enable_backlight = w600d_panel_backlight,
};

static const struct udevice_id w600d_panel_ids[] = {
	{ .compatible = "zte,w600d-kdc-panel" },
	{ }
};

U_BOOT_DRIVER(w600d_panel) = {
	.name = "w600d_panel",
	.id = UCLASS_PANEL,
	.of_match = w600d_panel_ids,
	.probe = w600d_panel_probe,
	.ops = &w600d_panel_ops,
	.priv_auto = sizeof(struct w600d_panel_priv),
};
