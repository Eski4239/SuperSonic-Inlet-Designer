# Off design at M∞ {{off.M_inf:.2f}}

## Relations
<!-- SOURCE: definition used by this tool: the captured streamtube is traced upstream from the lip, turning back at each ramp shock it crosses, to its freestream height y0 -->
$$ \frac{A_0}{A_c} = \frac{y_0}{h_c} $$
<!-- SOURCE: definition used by this tool: where ramp shock i crosses the cowl line, relative to the lip -->
$$ \Delta x_i / h_c = (x_{\mathrm{cross},i} - x_\mathrm{lip}) / h_c $$

## This case
Regime: {{off.regime}}; the frozen design (M {{design.inputs.M:.2f}}) is flown at M∞ = {{off.M_inf:.2f}}.
@each shocks: @if it.kind == "oblique": $$ \mathrm{shock}\;{{n}}:\;\Delta x/h_c = {{off.dx_over_hc[n-1]:+.4f}} $$
$$ A_0/A_c = {{off.mass_capture_ratio:.4f}},\quad \eta = {{off.recovery_total:.4f}}\;(\mathrm{design}\;{{design.recovery_total:.4f}}) $$

## In plain words
@if off.regime == "spillage": Below the design Mach the shocks are steeper and cross the cowl line ahead of the lip. Air behind them is deflected outward and spills around the lip, so only a streamtube of height A0/Ac = {{off.mass_capture_ratio:.4f}} times the capture height is swallowed; the tool finds it by tracing the streamline that ends at the lip back through the shocks.
@if off.regime == "on-lip": At the design Mach every ramp shock meets the lip: the inlet captures its full streamtube.
@if off.regime == "shock-in-duct": Above the design Mach the shocks are flatter and pass inside the cowl. All air is captured, but the shocks then reflect inside the duct and the lip meets freestream, which this model does not compute. The recovery shown is therefore an upper bound. {{cfd_lip_note}}

## Assumptions
- Two-dimensional, steady, inviscid flow; geometry frozen at the design point
- Calorically perfect gas (constant γ)
- Shock reflections, shock merging and the cowl shock are not modelled
