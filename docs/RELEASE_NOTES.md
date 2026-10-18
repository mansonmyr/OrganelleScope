# OrganelleScope 1.0.7

- Reduced 3D preview slices release full source-plane buffers immediately; regression checks retain exact pixels and enforce bounded plane lifetime.
- Expanded source-service qualification covers four local real TIFFs, a 2 GiB decoded synthetic stack and a 30-item technical-repeat batch, with independent numerical checks, source integrity, readiness latency and memory telemetry.
- Linux CI adds an enforced 1.5 GiB virtual-address-space worker; Mac performance measurements use a separately supervised service RSS budget. These are process tests, not whole low-RAM-computer claims.
- Twelve assistant questions retain their pre-inference manifest, outputs and developer review. Clearer threshold/cuboid definitions and targeted claim guards address observed answer failures. A separate packet supports independent human review; that review remains pending.

See the [manual](../MANUAL.md) and [verification records](VALIDATION.md) for methods, limits and measured outcomes. First installations retain empty research storage; upgrades preserve local work.
