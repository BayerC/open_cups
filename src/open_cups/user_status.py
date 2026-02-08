from enum import Enum


class UserStatus(Enum):
    UNKNOWN = "Unknown"
    GREEN = "🟢 Green"
    YELLOW = "🟡 Yellow"
    RED = "🔴 Red"

    def caption(self) -> str:
        captions = {
            UserStatus.UNKNOWN: "Not decided yet",
            UserStatus.GREEN: "Following easily",
            UserStatus.YELLOW: "Need more explanation",
            UserStatus.RED: "Cannot follow",
        }
        return captions[self]
