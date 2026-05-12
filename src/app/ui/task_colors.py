def task_background(color_hex: str) -> str:
    color = color_hex.strip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    return f"#{_mix(red):02x}{_mix(green):02x}{_mix(blue):02x}"


def _mix(channel: int) -> int:
    return round(channel * 0.16 + 255 * 0.84)
