from inletdesign.export import export_dxf
from inletdesign.geometry import design_inlet
from inletdesign.plotting import save_inlet_plot

geom = design_inlet(3.0, 2, scale=0.1)
save_inlet_plot(geom, "examples/output/m3_two_ramp.png")
export_dxf(geom, "examples/output/m3_two_ramp.dxf")
