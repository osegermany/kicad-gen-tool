#!/usr/bin/env python
# Licensed under the GPL v3, see LICENSE-GPLv3.md
#
# Fully automated rendering of a PCB from Gerber files into PNGs.
# Optionally, rendering to SVG is also possible,
# but the result is very poor!

import os, shutil
from gerber import common
from gerber.layers import PCBLayer, DrillLayer
from gerber.render import RenderSettings
from gerber.render.cairo_backend import GerberCairoContext
from PIL import Image
import click

# Render parameters
SCALE = 25
OFFSET = 20

@click.command()
@click.argument('gerbers_path')
@click.argument('render_base_path')
@click.argument('show', required=0)
@click.argument('png', required=0)
def render_pcb(gerbers_path, render_base_path, show=False, png=True):
    """Renders Gerber files into images (PNG by default, as SVG delivers poor results)

    GERBERS_PATH - Could be a folder or a zip file containing the Gerber files
    RENDER_BASE_PATH - Base-path of the PNGs to be generated; suffixes will be "-front.png", "-back.png", "-front-back.png"
    SHOW - Whether to show the generated front&back render in the end (default: False)
    PNG - Whether to render to PNG or SVG. NOTE: SVG output is very buggy, at least with text! (default: True (=> PNG))
    """
    del_tmp_folder = False
    extract_dir = ''

    if os.path.isfile(gerbers_path):
        if not gerbers_path.endswith('.zip'):
            click.BadParameter('Wrong GERBERS_PATH') # exit
        extract_dir = os.path.join(os.path.dirname(gerbers_path), 'tmp')
        shutil.unpack_archive(gerbers_path, extract_dir, 'zip')
        gerbers_path = extract_dir
        del_tmp_folder = True

    if png:
        img_file_ext = 'png'
    else:
        img_file_ext = 'svg'
    img_front_back_path = render_base_path + '-front-back.' + img_file_ext
    img_front_path = render_base_path + '-front.' + img_file_ext
    img_back_path = render_base_path + '-back.' + img_file_ext

    drill = None

    for gerber_file in os.listdir(gerbers_path):
        real_path = os.path.join(gerbers_path, gerber_file)

        if not os.path.isfile(real_path):
            continue

        # Drill
        if gerber_file.endswith('.drl'):
            drill = DrillLayer(real_path, common.read(real_path))

        # Front
        elif gerber_file.endswith('-F_Cu.gbr'):
            copper_front = PCBLayer(real_path, 'top', common.read(real_path))
        elif gerber_file.endswith('-F_Mask.gbr'):
            mask_front = PCBLayer(real_path, 'topmask', common.read(real_path))
        elif gerber_file.endswith('-F_SilkS.gbr'):
            silk_front = PCBLayer(real_path, 'topsilk', common.read(real_path))

        # Bottom
        elif gerber_file.endswith('-B_Cu.gbr'):
            copper_back = PCBLayer(real_path, 'back', common.read(real_path))
        elif gerber_file.endswith('-B_Mask.gbr'):
            mask_back = PCBLayer(real_path, 'backmask', common.read(real_path))
        elif gerber_file.endswith('-B_SilkS.gbr'):
            silk_back = PCBLayer(real_path, 'backsilk', common.read(real_path))
        else:
            continue

    # Create a new drawing context
    ctx = GerberCairoContext(scale=SCALE)

    ctx.render_layer(copper_front)
    ctx.render_layer(mask_front)
    ctx.render_layer(silk_front)
    if drill != None:
        ctx.render_layer(drill)

    # Write the front image file
    ctx.dump(img_front_path)

    # Clear the drawing
    ctx.clear()

    # Render back layers
    ctx.render_layer(copper_back)
    ctx.render_layer(mask_back)
    ctx.render_layer(silk_back)
    if drill != None:
        ctx.render_layer(drill, settings=RenderSettings(mirror=True))

    # Write the back image file
    ctx.dump(img_back_path)

    ctx.clear()

    # Concatenate the front and back images into a third image
    front = Image.open(img_front_path)
    back = Image.open(img_back_path)
    render = Image.new('RGB', (front.width, front.height * 2 + OFFSET))
    render.paste(front, (0, 0))
    render.paste(back, (0, front.height + OFFSET))
    render.save(img_front_back_path)
    if show:
        render.show()

    if del_tmp_folder:
        shutil.rmtree(extract_dir, ignore_errors=True)

if __name__ == "__main__":
    render_pcb()
