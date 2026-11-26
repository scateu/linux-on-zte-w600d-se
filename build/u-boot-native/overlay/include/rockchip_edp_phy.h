#ifndef ROCKCHIP_EDP_PHY_H
#define ROCKCHIP_EDP_PHY_H

#include <linux/types.h>

struct rockchip_edp_phy_config {
	u32 link_rate;
	u8 lanes;
	u8 voltage[4];
	u8 pre[4];
	bool set_rate;
	bool set_voltages;
	bool ssc;
};

#endif
