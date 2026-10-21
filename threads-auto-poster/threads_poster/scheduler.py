"""投稿枠（スロット）の判定。"""

from datetime import datetime, timedelta


def parse_slot(slot: str) -> tuple[int, int]:
    hour, minute = slot.split(":")
    return int(hour), int(minute)


def due_slot(now: datetime, slots: list[str], window_minutes: int) -> str | None:
    """now が「スロット時刻〜その window_minutes 分後」に入っていれば、そのスロットを返す。

    GitHub Actions などの定期実行は数分〜数十分遅れることがあるため、幅を持たせて判定する。
    """
    for slot in sorted(slots, key=parse_slot, reverse=True):
        hour, minute = parse_slot(slot)
        start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if start <= now < start + timedelta(minutes=window_minutes):
            return slot
    return None


def slot_key(now: datetime, slot: str) -> str:
    return f"{now.date().isoformat()} {slot}"
