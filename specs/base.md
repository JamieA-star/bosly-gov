# The base spec — every build inherits these

- A check the build writes is registered in `manifests/checks.yml` and kept.
- One job per step — "write, register, and run" is three steps.
- A finished step ticks with the check's output as its evidence.
- A question is a spec gap — the answer goes into this spec, and the build parks until it does.
- A step's check is registered under the step's `check_id` and prints its proof on success. A silent check cannot tick.
