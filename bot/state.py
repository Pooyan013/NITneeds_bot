from threading import Timer
from typing import Any, Dict, List

pending_requests: List[Dict[str, Any]] = []
user_states: Dict[int, Dict[str, Any]] = {}
last_request_times: Dict[int, float] = {}
timers: Dict[int, Timer] = {}
