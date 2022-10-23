from typing import Tuple

from rectpack import newPacker
import plotly.graph_objects as go

rectangles = [(2, 1)]*100
bins = [(8, 6)]

packer = newPacker()

# Add the rectangles to packing queue
for r in rectangles:
    packer.add_rect(*r)

# Add the bins where the rectangles will be placed
for b in bins:
    packer.add_bin(*b)

# Start packing
packer.pack()

# Obtain number of bins used for packing
nbins = len(packer)

# Index first bin
abin = packer[0]

# Bin dimmensions (bins can be reordered during packing)
width, height = abin.width, abin.height

# Number of rectangles packed into first bin
nrect = len(packer[0])

# Full rectangle list
all_rects = packer.rect_list()
for rect in all_rects:
    b, x, y, w, h, rid = rect


def convert_rect_to_scatter(rect: Tuple):
    b, x, y, w, h, rid = rect
    return go.Scatter(x=[x, x, x + w, x + w], y=[y, y + h, y + h, y], fill="toself")


data = [convert_rect_to_scatter(rect) for rect in all_rects]
fig = go.Figure()
for trace in data:
    fig.add_trace(trace)
fig.show()
