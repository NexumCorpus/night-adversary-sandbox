from typing import Callable, Dict, List

from vulnerabilitylookup.default import get_config

# Default topics to stream (ie Redis/Valkey channels)
DEFAULT_TOPICS = get_config("stream", "channels")

# Define a type alias for a callback function
Callback = Callable[[str], None]

# Thread-safe dictionary for subscriptions (initialize with default topics)
subscriptions: Dict[str, List[Callback]] = {topic: [] for topic in DEFAULT_TOPICS}
