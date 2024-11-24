import xml.etree.ElementTree as ET
import numpy as np


def prefix(s: str, rpf: str = '{http://webstds.ipc.org/2581}'):
    """
    Add root prefix `rpf` between '/' in string `s`
    :param s:
    :param rpf:
    :return:
    """
    s_split = s.split('/')
    s_new = [f'{rpf}{s_old}' for s_old in s_split]
    return '/'.join(s_new)


class PCBAssembly:
    def __init__(self,root: ET.Element):
        self.root = root
        self.function_mode = ''
        self.step_ref = ''
        self.bom_ref = ''
        self.layer_refs = []
        self.color_dictionary = {}  # 'id': (r,g,b)
        self.line_desc_units = ''
        self.line_desc_dictionary = {}  # 'id': {'lineEnd','lineWidth'}
        self.rpf = '{http://webstds.ipc.org/2581}'  # root prefix

        self.parse_Content()

    def parse_Content(self):
        """
        The Content node has
         - FunctionMode
         - StepRef
         - LayerRef
         - BomRef
         - DictionaryColor
         - DictionaryLineDesc
         - DictionaryFillDescr
         - DictionaryStandard
         - DictionaryUser
         We can parse the function mode, step ref, BOM ref, and layer refs
         Dictionaries can wait.

        :return: None
        """
        self.function_mode = self.root.find(prefix('Content/FunctionMode')).attrib['mode']
        self.step_ref = self.root.find(prefix('Content/StepRef')).attrib['name']
        self.bom_ref = self.root.find(prefix('Content/BomRef')).attrib['name']
        layer_ref_nodes = self.root.findall(prefix('Content/LayerRef'))
        self.layer_refs = [layer.attrib['name'] for layer in layer_ref_nodes]

        # Color dictionary
        entry_color_nodes = self.root.findall(prefix('Content/DictionaryColor/EntryColor'))
        for ecn in entry_color_nodes:
            color_id = ecn.attrib['id']
            color_node = ecn.find(prefix('Color'))
            color_rgb = tuple([int(color_node.attrib[attr]) for attr in ('r','g','b')])
            self.color_dictionary[color_id] = color_rgb

        # Line description dictionary
        self.line_desc_units = self.root.find(prefix('Content/DictionaryLineDesc')).attrib['units']
        entry_line_desc_nodes = self.root.findall(prefix('Content/DictionaryLineDesc/EntryLineDesc'))
        for entry in entry_line_desc_nodes:
            entry_line_desc_id = entry.attrib['id']
            linedesc = entry.find(prefix('LineDesc'))
            linedesc_attrib = {
                'lineEnd': linedesc.attrib['lineEnd'],
                'lineWidth': float(linedesc.attrib['lineWidth'])
            }
            self.line_desc_dictionary[entry_line_desc_id] = linedesc_attrib




def get_layer_list(root: ET.Element):
    """
    Return a list of layers in dictionary format for this document

    Parameters
    ----------
    root : ET.Element

    Returns
    -------
    List of layer dictionaries with elements:
        name            Layer name
        layerFunction   Layer function as a string, one of {'DRILL', 'DOCUMENT', 'PASTEMASK', 'LEGEND', 'SOLDERMASK', 'SIGNAL', 'DIELCORE'}
        side            PCB side, one of {'TOP', 'BOTTOM', 'INTERNAL'}
        polarity        Layer drawing polarity, one of {'POSITIVE','NEGATIVE'}
        thickness       Layer thickness as float
        sequence        Layer sequence position as int
        z               Layer z position as float (bottom is z=0)

    """
    rpf = '{http://webstds.ipc.org/2581}'  # Root prefix
    # Get layer names and functions
    layer_refs = root.findall(f'{rpf}Content/{rpf}LayerRef')
    layers = root.findall(f'{rpf}Ecad/{rpf}CadData/{rpf}Layer')
    layers = [l.attrib for l in layers]

    # Get layer thicknesses
    for layer in layers:
        name = layer['name']
        stackuplayer = root.find(
            f'{rpf}Ecad/{rpf}CadData/{rpf}Stackup/{rpf}StackupGroup/{rpf}StackupLayer[@layerOrGroupRef="{name}"]')
        if stackuplayer is not None:
            layer['thickness'] = float(stackuplayer.attrib['thickness'])
            layer['sequence'] = int(stackuplayer.attrib['sequence'])
        else:
            layer['thickness'] = 0.0
            layer['sequence'] = -1

    thicknesses = [layer['thickness'] for layer in layers]
    zpos = np.cumsum(-np.array(thicknesses)) + np.sum(thicknesses)
    for i, layer in enumerate(layers):
        layer['z'] = np.around(zpos[i], decimals=6)

    return layers


def get_layer_net_list(root: ET.Element, layername: str):
    """
    Return list of layer nets (as strings) given root and layer name

    Parameters
    ----------
    root : ET.Element
    layername : str

    Returns
    -------
    None.

    """
    rpf = '{http://webstds.ipc.org/2581}'  # Root prefix
    LayerFeatureRoot = root.find(f'{rpf}Ecad/{rpf}CadData/{rpf}Step/{rpf}LayerFeature[@layerRef="{layername}"]')
    LayerSets = LayerFeatureRoot.findall(f'{rpf}Set')
    netnames = []
    for lset in LayerSets:
        if 'net' in lset.attrib.keys():
            #if lset.attrib['net'] != 'No Net':
            netnames.append(lset.attrib['net'])
    netnames = list(set(netnames))
    return netnames

if __name__ == '__main__':
    fname = 'examples/BeagleBone_Black_RevB6_nologo174-AllegroOut/BeagleBone_Black_RevB6_nologo174.xml'
    # fname = 'examples/testcase10-Rev C data/testcase10-RevC-Full.xml'
    tree = ET.parse(fname)
    root = tree.getroot()
    # print(get_layer_list(root))
    # print(get_layer_net_list(root,'TOP'))
    # print(get_CadHeader_units(root))
    test_pcb = PCBAssembly(root)

