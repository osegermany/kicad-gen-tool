import pcbnew
import os
import shutil
import subprocess


# SETTINGS:
# Gerber

# Drill
METRIC = True
ZERO_FORMAT = pcbnew.GENDRILL_WRITER_BASE.DECIMAL_FORMAT
INTEGER_DIGITS = 3
MANTISSA_DIGITS = 3
MIRROR_Y_AXIS = False
HEADER = True
OFFSET = pcbnew.wxPoint(0,0)
MERGE_PTH_NPTH = True
DRILL_FILE = True
MAP_FILE = False
REPORTER = None

def generate_gerbers(pcb, path):
    plot_controller = pcbnew.PLOT_CONTROLLER(pcb)
    plot_options = plot_controller.GetPlotOptions()

    # Set General Options:
    plot_options.SetOutputDirectory(path)
    plot_options.SetPlotFrameRef(False)
    plot_options.SetPlotValue(True)
    plot_options.SetPlotReference(True)
    plot_options.SetPlotInvisibleText(True)
    plot_options.SetPlotViaOnMaskLayer(True)
    plot_options.SetExcludeEdgeLayer(False)
    #plot_options.SetPlotPadsOnSilkLayer(PLOT_PADS_ON_SILK_LAYER)
    #plot_options.SetUseAuxOrigin(PLOT_USE_AUX_ORIGIN)
    plot_options.SetMirror(False)
    #plot_options.SetNegative(PLOT_NEGATIVE)
    #plot_options.SetDrillMarksType(PLOT_DRILL_MARKS_TYPE)
    #plot_options.SetScale(PLOT_SCALE)
    plot_options.SetAutoScale(True)
    #plot_options.SetPlotMode(PLOT_MODE)
    #plot_options.SetLineWidth(pcbnew.FromMM(PLOT_LINE_WIDTH))

    # Set Gerber Options
    #plot_options.SetUseGerberAttributes(GERBER_USE_GERBER_ATTRIBUTES)
    #plot_options.SetUseGerberProtelExtensions(GERBER_USE_GERBER_PROTEL_EXTENSIONS)
    #plot_options.SetCreateGerberJobFile(GERBER_CREATE_GERBER_JOB_FILE)
    #plot_options.SetSubtractMaskFromSilk(GERBER_SUBTRACT_MASK_FROM_SILK)
    #plot_options.SetIncludeGerberNetlistInfo(GERBER_INCLUDE_GERBER_NETLIST_INFO)

    plot_plan = [
        ( 'F.Cu', pcbnew.F_Cu, 'Front Copper' ),
        ( 'B.Cu', pcbnew.B_Cu, 'Back Copper' ),
        ( 'F.Paste', pcbnew.F_Paste, 'Front Paste' ),
        ( 'B.Paste', pcbnew.B_Paste, 'Back Paste' ),
        ( 'F.SilkS', pcbnew.F_SilkS, 'Front SilkScreen' ),
        ( 'B.SilkS', pcbnew.B_SilkS, 'Back SilkScreen' ),
        ( 'F.Mask', pcbnew.F_Mask, 'Front Mask' ),
        ( 'B.Mask', pcbnew.B_Mask, 'Back Mask' ),
        ( 'Edge.Cuts', pcbnew.Edge_Cuts, 'Edges' ),
        ( 'Eco1.User', pcbnew.Eco1_User, 'Eco1 User' ),
        ( 'Eco2.User', pcbnew.Eco2_User, 'Eco1 User' ),
    ]

    for layer_info in plot_plan:
        plot_controller.SetLayer(layer_info[1])
        plot_controller.OpenPlotfile(layer_info[0], pcbnew.PLOT_FORMAT_GERBER, layer_info[2])
        plot_controller.PlotLayer()

    plot_controller.ClosePlot()


def detect_blind_buried_or_micro_vias(pcb):
    through_vias = 0
    micro_vias = 0
    blind_or_buried_vias = 0

    for track in pcb.GetTracks():
        if track.Type() != pcbnew.PCB_VIA_T:
            continue

        if track.GetShape() == pcbnew.VIA_THROUGH:
            through_vias += 1
        elif track.GetShape() == pcbnew.VIA_MICROVIA:
            micro_vias += 1
        elif track.GetShape() == pcbnew.VIA_BLIND_BURIED:
            blind_or_buried_vias += 1

    if micro_vias or blind_or_buried_vias:
        return True
    else:
        return False


def generate_drill_file(pcb, path):

    #if detect_blind_buried_or_micro_vias(pcb):
    #    return

    drill_writer = pcbnew.EXCELLON_WRITER(pcb)
    drill_writer.SetFormat(METRIC, ZERO_FORMAT, INTEGER_DIGITS, MANTISSA_DIGITS)
    drill_writer.SetOptions(MIRROR_Y_AXIS, HEADER, OFFSET, MERGE_PTH_NPTH)
    drill_writer.CreateDrillandMapFilesSet(path, DRILL_FILE, MAP_FILE, REPORTER)


class SimplePlugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = 'Gerber Plot'
        self.category = 'Gerber'
        self.description = 'Generate Gerber files, drill holes, see the result and send to a compressed folder'
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'gerber_plot_icon.png')

    def Run(self):
        # The entry function of the plugin that is executed on user action
        try:
            cwd_path = os.getcwd()
            pcb = pcbnew.GetBoard()
            project_path, project_name = os.path.split(pcb.GetFileName())
            project_name = os.path.splitext(project_name)[0]
            output_path = os.path.join(project_path, project_name + '-Gerber').replace('\\','/')
            tmp_path = os.path.join(project_path, 'tmp').replace('\\','/')
            log_file = os.path.join(project_path, 'log.txt').replace('\\','/')
            if os.path.exists(log_file):
                os.remove(log_file)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('Startup error\nError:{}\n'.format(err))

        # Create a temp folder
        try:
            os.mkdir(tmp_path)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('tmp folder not created\nError:{}\n'.format(err))

        # Generate Gerber and drill files
        try:
            generate_gerbers(pcb, tmp_path)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('Gerbers not plotted\nError:{}\n'.format(err))

        try:
            generate_drill_file(pcb, tmp_path)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('Drill file not plotted\nError:{}\n'.format(err))

        # Render an image: we need to call an external script that uses python 3
        try:
            subprocess.check_call(['powershell','render_pcb', tmp_path, os.path.join(project_path, project_name + '.png').replace('\\','/')], shell=True)
            # if you don't wish to have it as a exe file you could use:
            #subprocess.check_call(['powershell', 'path_to_python3', 'path_to_render_pcb', tmp_path, os.path.join(project_path, project_name + '.png').replace('\\','/')], shell=True)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('PCB not rendered\nError:{}\n'.format(err))

        # Create compressed file from tmp
        try:
            os.chdir(tmp_path)
            shutil.make_archive(output_path, 'zip', tmp_path)
            os.chdir(cwd_path)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('ZIP file not created\nError:{}\n'.format(err))

        # Remove temp folder
        try:
            shutil.rmtree(tmp_path, ignore_errors=True)
        except Exception as err:
            with open(log_file, 'a') as file:
                file.write('temp folder not deleted\nError:{}\n'.format(err))

SimplePlugin().register() # Instantiate and register to Pcbnew

