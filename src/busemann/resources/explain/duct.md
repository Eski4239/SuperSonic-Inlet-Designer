# Duct entry

## Relations
<!-- SOURCE: definition used by this tool: total pressure is unchanged between shocks, so the overall recovery is the product of the shock total-pressure ratios -->
$$ \eta = \frac{p_{0,\mathrm{duct}}}{p_{0\infty}} = \prod_i \left(\frac{p_{02}}{p_{01}}\right)_i $$

## This case
@each shocks: $$ \left(p_{02}/p_{01}\right)_{ {{n}} } = {{it.p0_ratio:.4f}}\quad(M_1 = {{it.M1:.4f}}) $$
$$ \eta = {{res.recovery_total:.4f}},\quad M_\mathrm{duct} = {{res.M_post_terminal:.4f}} $$
@if res.M_pre_terminal < 1: The flow behind the last ramp shock is already subsonic (M = {{res.M_pre_terminal:.4f}}): there is no terminal normal shock.

## In plain words
This is the flow entering the subsonic diffuser. The total-pressure recovery η = {{res.recovery_total:.4f}} is the headline number of an inlet: it multiplies every shock's total-pressure ratio, so a single strong shock dominates the loss. The oblique shocks alone give {{res.recovery_oblique:.4f}}; the rest is lost in the terminal shock.

## Assumptions
- Two-dimensional, steady, inviscid flow
- Calorically perfect gas (constant γ)
- No losses in the subsonic diffuser (not modelled)
