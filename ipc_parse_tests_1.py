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


class IPC2581_Transform:
    def __init__(self, rotation: float = 0.0, mirror: bool = False, xOffset: float = 0.0, yOffset: float = 0.0):
        self.rotation = rotation  # angle in degrees
        self.mirror = mirror
        self.xOffset = xOffset
        self.yOffset = yOffset

    def load(self, xfrm_node: ET.Element):
        if xfrm_node.tag != prefix('Xform'):
            raise ValueError(f'Expected tag Xform, instead got {xfrm_node.tag}')

        if 'rotation' in xfrm_node.attrib.keys():
            self.rotation = float(xfrm_node.attrib['rotation'])
        if 'mirror' in xfrm_node.attrib.keys():
            self.mirror = xfrm_node.attrib['mirror']
        if 'xOffset' in xfrm_node.attrib.keys():
            self.xOffset = xfrm_node.attrib['xOffset']
        if 'yOffset' in xfrm_node.attrib.keys():
            self.yOffset = xfrm_node.attrib['yOffset']

class IPC2581_Circle:
    def __init__(self, diameter: float = 0.0,fill_desc_ref: str = '',transform: IPC2581_Transform=None):
        self.diameter = diameter
        self.fill_desc_ref = fill_desc_ref
        self.transform = transform

    def load(self, circle_node: ET.Element):
        if circle_node.tag != prefix('Circle'):
            raise ValueError(f"Expected tag to be Circle, instead got {circle_node.tag}")

        self.diameter = circle_node.attrib['diameter']
        fdr_node = circle_node.find(prefix('FillDescRef'))
        if fdr_node is not None:
            self.fill_desc_ref = fdr_node.attrib['id']
        xfrm_node = circle_node.find(prefix('Xform'))
        if xfrm_node is not None:
            self.transform = IPC2581_Transform()
            self.transform.load(xfrm_node)


class IPC2581_RectCenter:
    def __init__(self, width: float = 0.0, height: float = 0.0, fill_desc_ref: str = '', transform: IPC2581_Transform = None):
        self.width = width
        self.height = height
        self.fill_desc_ref = fill_desc_ref
        self.transform = transform

    def load(self, rc_node: ET.Element):
        if rc_node.tag != prefix('RectCenter'):
            raise ValueError(f'Expected RectCenter tag, instead got {rc_node.tag}')
        self.width = float(rc_node.attrib['width'])
        self.height = float(rc_node.attrib['height'])

        fdr_node = rc_node.find(prefix('FillDescRef'))
        if fdr_node is not None:
            self.fill_desc_ref = fdr_node.attrib['id']
        xfrm_node = rc_node.find(prefix('Xform'))
        if xfrm_node is not None:
            self.transform = IPC2581_Transform()
            self.transform.load(xfrm_node)


class IPC2581_Oval:
    def __init__(self, width: float = 0.0, height: float = 0.0, fill_desc_ref: str = '', transform: IPC2581_Transform = None):
        self.width = width
        self.height = height
        self.fill_desc_ref = fill_desc_ref
        self.transform = transform

    def load(self, oval_node: ET.Element):
        if oval_node.tag != prefix('Oval'):
            raise ValueError(f'Expected Oval tag, instead got {oval_node.tag}')
        self.width = float(oval_node.attrib['width'])
        self.height = float(oval_node.attrib['height'])

        fdr_node = oval_node.find(prefix('FillDescRef'))
        if fdr_node is not None:
            self.fill_desc_ref = fdr_node.attrib['id']
        xfrm_node = oval_node.find(prefix('Xform'))
        if xfrm_node is not None:
            self.transform = IPC2581_Transform()
            self.transform.load(xfrm_node)


class IPC2581_Arc:
    """
    An arc has a start point, end point, center point, direction (CW or CCW), and line style
    """
    def __init__(self, start_pos: tuple[float,float] = (0.0, 0.0),
                 end_pos: tuple[float,float] = (0.0, 0.0),
                 center_pos: tuple[float, float] = (0.0, 0.0),
                 clockwise: bool = True, lineEnd: str = 'ROUND', lineWidth: float = 0.0):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.center_pos = center_pos
        self.clockwise = clockwise
        self.lineEnd = lineEnd
        self.lineWidth = lineWidth

    def load(self, arc_node):
        if arc_node.tag != prefix('Arc'):
            raise ValueError(f'Expected Arc tag, instead got {arc_node.tag}')
        self.start_pos = (float(arc_node.attrib['startX']), float(arc_node.attrib['startY']))
        self.end_pos = (float(arc_node.attrib['endX']), float(arc_node.attrib['endY']))
        self.center_pos = (float(arc_node.attrib['centerX']), float(arc_node.attrib['centerY']))
        self.clockwise = arc_node.attrib['clockwise'] == 'true'

        ld_node = arc_node.find(prefix('LineDesc'))
        if ld_node is not None:
            self.lineEnd = ld_node.attrib['lineEnd']
            self.lineWidth = float(ld_node.attrib['lineWidth'])


class IPC2581_PolyStepCurve:
    def __init__(self, center: tuple[float,float] = (0., 0.), clockwise: bool = True):
        self.center = center
        self.clockwise = clockwise


class IPC2581_Contour:
    """
    A contour has a list of coordinates creating a closed shape, with fill style
    Some coordinates are connected by lines, others are connected by curves with a center point
    """
    def __init__(self, points: list[tuple[float,float], ...] = None,
                 connections: list[IPC2581_PolyStepCurve, ...] = None, fill_desc_ref = ''):
        self.points = points or []
        self.connections = connections or []
        self.fill_desc_ref = fill_desc_ref

    def load(self, ct_node: ET.Element):
        if ct_node.tag != prefix('Contour'):
            raise ValueError(f'Expected Contour tag, instead got {ct_node.tag}')
        poly_node = ct_node.find(prefix('Polygon'))
        if poly_node is not None:
            for pnode in poly_node:
                if pnode.tag == prefix('PolyBegin'):
                    self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                elif pnode.tag == prefix('PolyStepSegment'):
                    self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                    self.connections.append(None)
                elif pnode.tag == prefix('PolyStepCurve'):
                    self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                    self.connections.append(IPC2581_PolyStepCurve(
                        center=( float(pnode.attrib['centerX']), float(pnode.attrib['centerY']) ),
                        clockwise = pnode.attrib['clockwise'] == 'true'
                    ))
                elif pnode.tag == prefix('FillDescRef'):
                    self.fill_desc_ref = pnode.attrib['id']


class IPC2581_Polyline:
    """
    A polyline has a list of coordinates and line style
    Some coordinates are connected by lines, others are connected by curves with a center point
    """
    def __init__(self, points: list[tuple[float,float], ...] = None,
                 connections: list[IPC2581_PolyStepCurve, ...] = None,
                 lineEnd: str = '', lineWidth: str = ''):
        self.points = points or []
        self.connections = connections or []
        self.lineEnd = lineEnd
        self.lineWidth = lineWidth

    def load(self, poly_node: ET.Element):
        if poly_node.tag != prefix('Polyline'):
            raise ValueError(f'Expected Polyline tag, instead got {poly_node.tag}')
        for pnode in poly_node:
            if pnode.tag == prefix('PolyBegin'):
                self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
            elif pnode.tag == prefix('PolyStepSegment'):
                self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                self.connections.append(None)
            elif pnode.tag == prefix('PolyStepCurve'):
                self.points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                self.connections.append(IPC2581_PolyStepCurve(
                    center=( float(pnode.attrib['centerX']), float(pnode.attrib['centerY']) ),
                    clockwise = pnode.attrib['clockwise'] == 'true'
                ))
            elif pnode.tag == prefix('LineDesc'):
                self.lineEnd = pnode.attrib['lineEnd']
                self.lineWidth = float(pnode.attrib['lineWidth'])

class IPC2581_UserSpecial:
    """
    Collection of geometries
    """
    def __init__(self, shapes = None):
        self.shapes = shapes or []

    def load(self, node):
        if node.tag != prefix('UserSpecial'):
            raise ValueError(f'Expected UserSpecial tag, instead got {node.tag}')

        self.shapes = []
        for shape_node in node:  # there should only be one
            shape_tag = shape_node.tag
            if shape_tag == prefix('Circle'):
                shape = IPC2581_Circle()
            elif shape_tag == prefix('RectCenter'):
                shape = IPC2581_RectCenter()
            elif shape_tag == prefix('Oval'):
                shape = IPC2581_Oval()
            elif shape_tag == prefix('Arc'):
                shape = IPC2581_Arc()
            elif shape_tag == prefix('Contour'):
                shape = IPC2581_Contour()
            elif shape_tag == prefix('Polyline'):
                shape = IPC2581_Polyline()
            else:
                raise ValueError(f"Unknown geometry type with tag {shape_tag}")

            shape.load(shape_node)
            self.shapes.append(shape)


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
        self.fill_desc_dictionary = {}  # 'id': 'fillProperty'
        self.standard_dict = {}
        self.user_dict = {}
        self.rpf = '{http://webstds.ipc.org/2581}'  # root prefix

        self.parse_Content()

    def parse_Content(self,verbose=False):
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
        if verbose:
            print("Parsing function mode, step ref, bom ref, layer ref... ", end='')
        fm_node = self.root.find(prefix('Content/FunctionMode'))
        if fm_node is not None:
            self.function_mode = fm_node.attrib['mode']

        sr_node = self.root.find(prefix('Content/StepRef'))
        if sr_node is not None:
            self.step_ref = sr_node.attrib['name']

        br_node = self.root.find(prefix('Content/BomRef'))
        if br_node is not None:
            self.bom_ref = br_node.attrib['name']

        layer_ref_nodes = self.root.findall(prefix('Content/LayerRef'))
        for layer in layer_ref_nodes:
            if layer is not None:
                self.layer_refs.append(layer.attrib['name'])

        if verbose:
            print("Done")
            print("Parsing color dictionary... ", end='')
        self._parse_color_dict()
        if verbose:
            print("Done")
            print("Parsing line description dictionary... ", end='')
        self._parse_line_desc_dict()
        if verbose:
            print("Done")
            print("Parsing fill description dictionary... ", end='')
        self._parse_fill_desc_dict()
        if verbose:
            print("Done")
            print("Parsing standard dictionary... ", end='')
        self._parse_standard_dict()
        if verbose:
            print("Done")
            print("Parsing user dictionary... ", end='')
        self._parse_user_dict()
        if verbose:
            print("Done")

    def _parse_color_dict(self):
        # Color dictionary
        entry_color_nodes = self.root.findall(prefix('Content/DictionaryColor/EntryColor'))
        for ecn in entry_color_nodes:
            color_id = ecn.attrib['id']
            color_node = ecn.find(prefix('Color'))
            if color_node is not None:
                color_rgb = tuple([int(color_node.attrib[attr]) for attr in ('r','g','b')])
                self.color_dictionary[color_id] = color_rgb

    def _parse_line_desc_dict(self):
        # Line description dictionary
        ldu_node = self.root.find(prefix('Content/DictionaryLineDesc'))
        if ldu_node is not None:
            self.line_desc_units = ldu_node.attrib['units']
        entry_line_desc_nodes = self.root.findall(prefix('Content/DictionaryLineDesc/EntryLineDesc'))
        for entry in entry_line_desc_nodes:
            if entry is not None:
                entry_line_desc_id = entry.attrib['id']
                linedesc = entry.find(prefix('LineDesc'))
                if linedesc is not None:
                    linedesc_attrib = {
                        'lineEnd': linedesc.attrib['lineEnd'],
                        'lineWidth': float(linedesc.attrib['lineWidth'])
                    }
                    self.line_desc_dictionary[entry_line_desc_id] = linedesc_attrib

    def _parse_fill_desc_dict(self):
        # Fill description dictionary
        fill_desc_nodes = self.root.findall(prefix('Content/EntryFillDesc'))
        for fill in fill_desc_nodes:
            if fill is not None:
                fill_id = fill.attrib['id']
                fill_property = fill.find(prefix('FillDesc')).attrib['fillProperty']
                if fill_property is not None:
                    self.fill_desc_dictionary[fill_id] = fill_property

    def _parse_standard_dict(self):
        # Standard dictionary
        entry_standard_nodes = self.root.findall(prefix('Content/DictionaryStandard/EntryStandard'))
        for es_node in entry_standard_nodes:
            es_id = es_node.attrib['id']
            for shape_node in es_node:  # there should only be one
                shape_tag = shape_node.tag
                # Geometry types:
                # - Circle
                # - RectCenter
                # - Oval
                # - Contour.Polygon
                # - Polyline
                # - Arc
                if shape_tag == prefix('Circle'):
                    shape = IPC2581_Circle()
                elif shape_tag == prefix('RectCenter'):
                    shape = IPC2581_RectCenter()
                elif shape_tag == prefix('Oval'):
                    shape = IPC2581_Oval()
                elif shape_tag == prefix('Arc'):
                    shape = IPC2581_Arc()
                elif shape_tag == prefix('Contour'):
                    shape = IPC2581_Contour()
                elif shape_tag == prefix('Polyline'):
                    shape = IPC2581_Polyline()
                else:
                    raise ValueError(f"Unknown geometry type with tag {shape_tag}")

                shape.load(shape_node)
                self.standard_dict[es_id] = shape

    def _parse_user_dict(self):
        # User dictionary
        entry_user_nodes = self.root.findall(prefix('Content/DictionaryUser/EntryUser'))
        for eu_node in entry_user_nodes:
            eu_id = eu_node.attrib['id']
            us_node = eu_node.find(prefix('UserSpecial'))
            if us_node is not None:
                us_obj = IPC2581_UserSpecial()
                us_obj.load(us_node)
                self.user_dict[eu_id] = us_obj




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
    print("Loading file... ",end='')
    tree = ET.parse(fname)
    root = tree.getroot()
    print("Done")
    test_pcb = PCBAssembly(root)

