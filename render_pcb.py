import os, shutil
from gerber import common
from gerber.layers import PCBLayer, DrillLayer
from gerber.render import RenderSettings
from gerber.render.cairo_backend import GerberCairoContext
from PIL import Image
import click

# Render
SCALE = 25
OFFSET = 20

@click.command()
@click.argument('input_path')
def render_pcb(input_path):
    """Render Gerber Files into a PNG Image

    INPUT_PATH  - Could be a folder or a zip file containing the Gerber Files
    """
    del_tmp_folder = False
    extract_dir = ''

    if os.path.isfile(input_path):
        if not input_path.endswith('.zip'):
            click.BadParameter('Wrong INPUT_PATH') # exit
        extract_dir = os.path.join(os.path.dirname(input_path), 'tmp')
        shutil.unpack_archive(input_path, extract_dir, 'zip')
        input_path = extract_dir
        del_tmp_folder = True

    output_path = os.path.join(os.path.dirname(input_path), 'pcb.png')

    img_front_path = os.path.join(input_path, 'front.png')
    img_bottom_path = os.path.join(input_path, 'bottom.png')

    for file in os.listdir(input_path):

        real_path = os.path.join(input_path, file)

        if not os.path.isfile(real_path):
            continue

        # Drill
        if file.endswith('.drl'):
            drill = DrillLayer(real_path, common.read(real_path))

        # Front
        elif file.endswith('-F_Cu.gbr'):
            copper_front = PCBLayer(real_path, 'top', common.read(real_path))
        elif file.endswith('-F_Mask.gbr'):
            mask_front = PCBLayer(real_path, 'topmask', common.read(real_path))
        elif file.endswith('-F_SilkS.gbr'):
            silk_front = PCBLayer(real_path, 'topsilk', common.read(real_path))

        # Bottom
        elif file.endswith('-B_Cu.gbr'):
            copper_bottom = PCBLayer(real_path, 'bottom', common.read(real_path))
        elif file.endswith('-B_Mask.gbr'):
            mask_bottom = PCBLayer(real_path, 'bottommask', common.read(real_path))
        elif file.endswith('-B_SilkS.gbr'):
            silk_bottom = PCBLayer(real_path, 'bottomsilk', common.read(real_path))
        else:
            continue

    # Create a new drawing context
    ctx = GerberCairoContext(scale=SCALE)

    ctx.render_layer(copper_front)
    ctx.render_layer(mask_front)
    ctx.render_layer(silk_front)
    ctx.render_layer(drill)

    # Write png file
    ctx.dump(img_front_path)

    # Clear the drawing
    ctx.clear()

    # Render bottom layers
    ctx.render_layer(copper_bottom)
    ctx.render_layer(mask_bottom)
    ctx.render_layer(silk_bottom)
    ctx.render_layer(drill, settings=RenderSettings(mirror=True))

    # Write png file
    ctx.dump(img_bottom_path)

    ctx.clear()

    # Concatenate
    front = Image.open(img_front_path)
    bottom = Image.open(img_bottom_path)
    render = Image.new('RGB', (front.width, front.height * 2 + OFFSET))
    render.paste(front, (0, 0))
    render.paste(bottom, (0, front.height + OFFSET))
    render.save(output_path)
    render.show()

    if del_tmp_folder:
        shutil.rmtree(extract_dir, ignore_errors=True)

if __name__ == "__main__":
    render_pcb()
