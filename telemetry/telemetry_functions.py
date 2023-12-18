"""
LBIT Telemetry module
"""
import os
import sys
import json
from collections import defaultdict
import jinja2


sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def generate_telemetry(
    rconn_pool,
    rconn_parent,
    lb_name,
    parent_object_type,
    parent_object_name,
    result_type,
):
    """Function to generate svg image with SLB VIP data

    Args:
        lb_name (str): SLB FQDN
        slb_vip (str): SLB VIP Handle

    Returns:
        str: vip data in image/xml format
    """

    loader = jinja2.FileSystemLoader(os.getcwd())
    jenv = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    template_svg = jenv.get_template("telemetry/template_svg.j2")

    result_dict = defaultdict(dict)
    # Dict to store collected data from Redis DB
    dashboard_dict = {}

    if parent_object_type != "pool":
        parent_object_result = rconn_parent.hgetall(parent_object_name)

        if parent_object_result == {}:
            dashboard_dict.update(
                {
                    "parent_object_type": parent_object_type,
                    "parent_object_name": f"{parent_object_name} does not exist in DB",
                    "pool": "",
                    "members": dict(result_dict),
                }
            )
        else:
            # Populate dashboard_dict with default values to handle non-existent pools
            dashboard_dict.update(
                {
                    "parent_object_type": parent_object_type,
                    "parent_object_name": parent_object_name,
                    "pool": "",
                    "members": dict(result_dict),
                }
            )

        # Get Pool Details from vip or WIP DB
        pool_result = rconn_pool.hgetall(
            f"{lb_name}:{parent_object_result.get('pool')}"
        )

    else:
        # Get Pool Details Pool DB
        pool_result = rconn_pool.hgetall(f"{lb_name}:{parent_object_name}")

    if pool_result == {}:
        dashboard_dict.update(
            {
                "pool": f"{parent_object_result.get('pool')} does not exist in DB",
                "members": dict(result_dict),
            }
        )
    else:
        try:
            # Sort member list before looping
            for k, v in pool_result.items():
                member = k.split("~")[0]
                stat_type = k.split("~")[1]
                stat_value = v

                result_dict[member][stat_type] = stat_value
                dict(result_dict)

                dashboard_dict.update(
                    {
                        "pool": parent_object_result.get("pool"),
                        "members": dict(result_dict),
                    }
                )

        except IndexError as err:
            dashboard_dict.update({"pool": f"DB Error: {err}", "members": {}})

    if result_type == "json":
        return json.dumps(dashboard_dict, indent=2)
    else:
        return template_svg.render(dashboard_dict=dashboard_dict)
