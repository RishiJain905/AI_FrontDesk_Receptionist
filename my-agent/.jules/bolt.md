## 2024-05-14 - Replace deepcopy with dataclasses.replace
**Learning:** `deepcopy` on simple dataclasses (like `SlotState`) introduces significant performance overhead compared to explicitly instantiating or using `dataclasses.replace()`. For high-frequency calls like `snapshot()` in conversational loops, `deepcopy` is a measurable bottleneck.
**Action:** When working with dataclasses that primarily hold primitives and don't require recursive copies, prefer `dataclasses.replace()` over `copy.deepcopy()` to improve performance without sacrificing safety.
