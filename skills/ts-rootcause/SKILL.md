---
name: ts-rootcause
description: "Investigate bugs, failing tests, crashes, wrong results, or unexpected behavior. Use for diagnosis-only requests and for authorized fixes; distinguish their completion conditions."
license: MIT
metadata:
  author: the-shop
  version: "0.1.0"
---

# ts-rootcause

Before doing the task, read this skill's complete [reference.toon](reference.toon).
When multiple skills are explicitly requested, read every requested reference;
overlapping procedures do not make a reference optional.

```toon
read: "reference.toon"
when: "Read the full reference when this skill is selected; do not preload other skill references."
apply: "Follow only the parts relevant to the user's requested task and available tools."
combine: "Merge obligations and evidence into one response. Honor the user's format and explicit length limit; never append every skill's template."
fallback: "If the reference is inaccessible, say so and do not claim to have followed the full procedure."
```
