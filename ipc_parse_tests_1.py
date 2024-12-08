import xml.etree.ElementTree as ET
import numpy as np
import matplotlib.pyplot as plt


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


def read_int(d: dict, key: str):
    if key not in d.keys():
        return None
    val = d[key]
    if not val.isnumeric():
        print(f"Warning: Could not convert value {val} to int. Returning None.")
        return None
    return int(val)


def read_float(d: dict, key: str):
    if key not in d.keys():
        return None
    val = d[key]
    try:
        return float(val)
    except ValueError:
        print("Warning: Could not convert value {val} to float. Returning None.")
        return None


def read_bool(d: dict, key: str):
    if key not in d.keys():
        return None
    val = d[key]
    return val.lower() == 'true'


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
            self.rotation = read_float(xfrm_node.attrib,'rotation')
        if 'mirror' in xfrm_node.attrib.keys():
            self.mirror = read_bool(xfrm_node.attrib,'mirror')
        if 'xOffset' in xfrm_node.attrib.keys():
            self.xOffset = read_float(xfrm_node.attrib,'xOffset')
        if 'yOffset' in xfrm_node.attrib.keys():
            self.yOffset = read_float(xfrm_node.attrib,'yOffset')

class IPC2581_Circle:
    def __init__(self, diameter: float = 0.0,fill_desc_ref: str = '',transform: IPC2581_Transform=None):
        self.diameter = diameter
        self.fill_desc_ref = fill_desc_ref
        self.transform = transform

    def load(self, circle_node: ET.Element):
        if circle_node.tag != prefix('Circle'):
            raise ValueError(f"Expected tag to be Circle, instead got {circle_node.tag}")

        self.diameter = read_float(circle_node.attrib,'diameter')
        fdr_node = circle_node.find(prefix('FillDescRef'))
        if fdr_node is not None:
            self.fill_desc_ref = fdr_node.attrib['id']
        xfrm_node = circle_node.find(prefix('Xform'))
        if xfrm_node is not None:
            self.transform = IPC2581_Transform()
            self.transform.load(xfrm_node)


class IPC2581_Line:
    """
    A Line has a start position, end position, and line description
    """
    def __init__(self, start_pos: tuple[float,float] = (0.0, 0.0),
                 end_pos: tuple[float,float] = (0.0, 0.0),
                 lineEnd: str = 'ROUND', lineWidth: float = 0.0):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.lineEnd = lineEnd
        self.lineWidth = lineWidth

    def load(self, line_node):
        if line_node.tag != prefix('Line'):
            raise ValueError(f'Expected Line tag, instead got {line_node.tag}')
        self.start_pos = (float(line_node.attrib['startX']), float(line_node.attrib['startY']))
        self.end_pos = (float(line_node.attrib['endX']), float(line_node.attrib['endY']))

        ld_node = line_node.find(prefix('LineDesc'))
        if ld_node is not None:
            self.lineEnd = ld_node.attrib['lineEnd']
            self.lineWidth = float(ld_node.attrib['lineWidth'])


class IPC2581_RectCenter:
    def __init__(self, width: float = 0.0, height: float = 0.0, fill_desc_ref: str = '', transform: IPC2581_Transform = None):
        self.width = width
        self.height = height
        self.fill_desc_ref = fill_desc_ref
        self.transform = transform

    def load(self, rc_node: ET.Element):
        if rc_node.tag != prefix('RectCenter'):
            raise ValueError(f'Expected RectCenter tag, instead got {rc_node.tag}')
        self.width = read_float(rc_node.attrib,'width')
        self.height = read_float(rc_node.attrib,'height')

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
        self.width = read_float(oval_node.attrib,'width')
        self.height = read_float(oval_node.attrib,'height')

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


class IPC2581_Polygon:
    """
    A polygon has a list of coordinates creating a closed shape.
    Some coordinates are connected by lines, others are connected by curves with a center point.
    Polygons are used by <Contour>, <Outline>, and <Profile> tags, among others?
    """
    def __init__(self):
        self.points = []
        self.connections = []

    def load(self, poly_node: ET.Element):
        if poly_node.tag != prefix('Polygon'):
            raise ValueError(f'Expected Polygon tag, instead got {poly_node.tag}')
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



class IPC2581_Contour:
    """
    A contour has a list of coordinates creating a closed shape, with fill style
    Some coordinates are connected by lines, others are connected by curves with a center point
    Contours can have one Polygon node and zero or more Cutout nodes
    """
    def __init__(self, points: list[tuple[float,float], ...] = None,
                 connections: list[IPC2581_PolyStepCurve, ...] = None, fill_desc_ref = ''):
        self.points = points or []
        self.connections = connections or []
        self.cutout_points = []
        self.cutout_connections = []
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
        cutout_nodes = ct_node.findall(prefix('Cutout'))
        for cutout_node in cutout_nodes:
            for pnode in cutout_node:
                if pnode.tag == prefix('PolyBegin'):
                    self.cutout_points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                elif pnode.tag == prefix('PolyStepSegment'):
                    self.cutout_points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                    self.cutout_connections.append(None)
                elif pnode.tag == prefix('PolyStepCurve'):
                    self.cutout_points.append( (float(pnode.attrib['x']), float(pnode.attrib['y'])) )
                    self.cutout_connections.append(IPC2581_PolyStepCurve(
                        center=( float(pnode.attrib['centerX']), float(pnode.attrib['centerY']) ),
                        clockwise = pnode.attrib['clockwise'] == 'true'
                    ))



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
                self.lineWidth = read_float(pnode.attrib,'lineWidth')


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
            elif shape_tag == prefix('Line'):
                shape = IPC2581_Line()
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


class IPC2581_Pad:
    def __init__(self):
        self.padstackDefRef = ''
        self.loc = (0.0, 0.0)
        self.std_prim_ref = ''
        self.pin = ''  # Not all Pads have this
        self.pin_componentRef = ''  # LandPattern pads don't have this

    def load(self,pad_node: ET.Element):
        if pad_node.tag != prefix('Pad'):
            raise ValueError(f'Expected Pad tag, instead got {pad_node.tag}.')
        self.padstackDefRef = pad_node.attrib['padstackDefRef']

        loc_node = pad_node.find(prefix('Location'))
        if loc_node is not None:
            x = read_float(loc_node.attrib,'x')
            y = read_float(loc_node.attrib,'y')
            self.loc = (x,y)

        spr_node = pad_node.find(prefix('StandardPrimitiveRef'))
        if spr_node is not None:
            self.std_prim_ref = spr_node.attrib['id']

        pinref_node = pad_node.find(prefix('PinRef'))
        if pinref_node is not None:
            self.pin = pinref_node.attrib['pin']
            if 'componentRef' in pinref_node.attrib.keys():
                self.pin_componentRef = pinref_node.attrib['componentRef']


class IPC2581_BomItem:
    def __init__(self):
        self.quantity = 0
        self.pin_count = 0
        self.category = ''
        self.OEM_design_number_ref = ''
        self.characteristics = []
        self.characteristics_categories = []
        self.reference_designators = []

    def load(self,bomitem_node: ET.Element):
        if bomitem_node.tag != prefix('BomItem'):
            raise ValueError(f"Unexpected tag {bomitem_node.tag}. Expected 'BomItem'.")
        self.quantity = read_int(bomitem_node.attrib,'quantity')
        self.pin_count = read_int(bomitem_node.attrib,'pinCount')
        self.category = bomitem_node.attrib['category']
        self.OEM_design_number_ref = bomitem_node.attrib['OEMDesignNumberRef']
        refdes_nodes = bomitem_node.findall(prefix('RefDes'))
        for rdn in refdes_nodes:
            self.reference_designators.append(rdn.attrib)

        characteristics_nodes = bomitem_node.findall(prefix('Characteristics'))
        for cnode in characteristics_nodes:
            if cnode is not None:
                if 'category' in cnode.attrib.keys():
                    self.characteristics_categories.append(cnode.attrib['category'])
                else:
                    self.characteristics_categories.append('')
                # parse characteristics
                textual_nodes = cnode.findall(prefix('Textual'))
                chars = []
                for tnode in textual_nodes:
                    chars.append(tnode.attrib)
                self.characteristics.append(chars)


class IPC2581_Bom:
    """
    An IPC2581 Bom includes:
     - A header with assembly name, rev, and geometry reference (step reference)
     - A list of Bom items, each with a quantity, pin count, category, and OEM design number reference; as well as
       characteristics, and finally a ref des object for each instantiation

    The list of characteristics has a category (e.g. Electrical) and one or more characteristic objects
     - Each characteristic object has a definition source, name, and value

    Each reference designator object has a name, package reference (e.g. 402), a populate flag (True/False), and a layer
    """
    def __init__(self):
        self.name = ''
        self.assembly_name = ''  #
        self.revision = ''       #
        self.pcb_reference = ''  # StepRef
        self.bom_items = []

    def load(self,bomnode: ET.Element):
        if bomnode.tag != prefix('Bom'):
            raise ValueError(f"Unexpected tag {bomnode.tag}. Expected 'Bom'.")

        self.name = bomnode.attrib['name']

        bhdr_node = bomnode.find(prefix('BomHeader'))
        if bhdr_node is not None:
            self.assembly_name = bhdr_node.attrib['assembly']
            self.revision = bhdr_node.attrib['revision']

            stepref_node = bhdr_node.find(prefix('StepRef'))
            if stepref_node is not None:
                self.pcb_reference = stepref_node.attrib['name']

        bomitem_nodes = bomnode.findall(prefix('BomItem'))
        for binode in bomitem_nodes:
            if binode is not None:
                bomitem = IPC2581_BomItem()
                bomitem.load(binode)
                self.bom_items.append(bomitem)


class IPC2581_Layer:
    """
    Represents a layer in a PCB, including specifications/properties, pads, physical net points, and traces/features

    About components and pads:
     - Top level <Component> tags store a layerRef and a packageRef
     - The packageRef gives the name of a corresponding <Package> tag that has the geometry information in the <LandPattern>
     - The LandPattern has multiple pads, each of which has a Location, and a StandardPrimitiveRef
     - The <Pad>s also have padstackDefRef that references the PadStackDef name
     - These PadStackDef tags have PadstackPadDef with a layerRef, padUse, Location (usually 0,0), and StandardPrimitiveRef
     - The StandardPrimitiveRef also appears under the <Package> <Pin> tag(s)
     - All StandardPrimitiveRef references should be the same, I assume...
    Not sure why the <PadstackPadDef> have a layerRef

    To make things more confusing, there are also <Set> tags with padstackRef

    I'll need to work on this...

    """
    def __init__(self, root: ET.Element, name: str):
        self.root = root
        self.name = name

        # from <Layer>
        self.function = ''
        self.side = ''
        self.polarity = ''

        # from <StackupLayer>
        self.thickness = 0.0
        self.tolPlus = 0.0
        self.tolminus = 0.0
        self.sequence = -1

        # from <PhyNetPoint> tags
        self.physical_net_points = []

        # from <LayerFeature> tag
        self.nets = {}  # netname : LayerNet
        self.nonet_geom = []
        self.vias = []
        self.pads_not_used = []

        # from <Component> tags
        self.components = []

        self.parse_Layer()
        self.parse_StackupLayer()
        self.parse_LayerFeature()
        self.parse_Components()

    class NetVia:
        def __init__(self):
            self.pad = None  # IPC2581_Pad
            self.nonstd_attrib = {}
            self.plate = False
            self.testPoint = False
        def load(self,set_node: ET.Element):
            if set_node.tag != prefix('Set'):
                raise ValueError(f"Expected Set tag, instead got {set_node.tag}")
            if 'padUsage' not in set_node.attrib.keys():
                print("WARNING: Attempting to parse via without padUsage attribute. This is probably a mistake.")
            if set_node.attrib['padUsage'] not in ['VIA','NONE']:
                print(f"WARNING: Attempting to parse via with padUsage={set_node.attrib['padUsage']} instead of VIA or NONE")
            if 'plate' in set_node.attrib.keys():
                self.plate = set_node.attrib['plate'] == 'true'
            if 'testPoint' in set_node.attrib.keys():
                self.testPoint = set_node.attrib['testPoint'] == 'true'
            pad_node = set_node.find(prefix('Pad'))
            if pad_node is not None:
                self.pad = IPC2581_Pad()
                self.pad.load(pad_node)
            nonstd_attrs = set_node.findall(prefix('NonstandardAttribute'))
            for nonstd in nonstd_attrs:
                self.nonstd_attrib[nonstd.attrib['name']] = nonstd.attrib['value']

    class PhysicalNetPoint:
        def __init__(self):
            self.position = (0.,0.)
            self.layer = ''
            self.net_node = ''
            self.exposure = ''
            self.via = False
            self.primitive_ref = ''

    class IPC2581_Component:
        def __init__(self):
            self.refDes = ''
            self.packageRef = ''
            # self.layerRef = ''  # Components are owned by layers so this isn't needed
            self.part = ''
            self.mountType = ''
            self.standoff = 0.0
            self.height = 0.0
            self.nonstd_attrib = {}
            self.loc = (0.0, 0.0)
            self.Xform = None # IPC2581_Transform()

        def load(self,comp_node: ET.Element):
            self.refDes = comp_node.attrib['refDes']
            self.packageRef = comp_node.attrib['packageRef']
            self.part = comp_node.attrib['part']
            self.mountType = comp_node.attrib['mountType']
            self.standoff = read_float(comp_node.attrib,'standoff')
            self.height = read_float(comp_node.attrib,'height')

            loc_node = comp_node.find(prefix('Location'))
            if loc_node is not None:
                x = read_float(loc_node.attrib,'x')
                y = read_float(loc_node.attrib,'y')
                self.loc = (x,y)

            xform_node = comp_node.find(prefix('Xform'))
            if xform_node is not None:
                self.Xform = IPC2581_Transform()
                self.Xform.load(xform_node)

            nonstd_nodes = comp_node.findall(prefix('NonstandardAttribute'))
            for nonstd in nonstd_nodes:
                self.nonstd_attrib[nonstd.attrib['name']] = nonstd.attrib['value']


    class LayerNet:
        """
        <Set> tags group layer net features
        Some sets have a componentRef (reference designator for component)
        Set nodes might not have an associated net (e.g. text)
        Set nodes can have <NonstandardAttribute>s
        A <Set> node representing a test point or via has additional attributes
        """
        def __init__(self,name):
            self.name = name
            self.feature_locations = []  # (x,y) coordinates
            self.features = []  # IPC2581_xyz features
            self.Xform = None

        def load_feature(self, feat_node : ET.Element):
            if feat_node.tag != prefix('Features'):
                raise ValueError(f"Unexpected tag {feat_node.tag}. Expected 'Features'.")
            for child in feat_node:
                if child.tag == prefix('Location'):
                    self.feature_locations.append(
                       (read_float(child.attrib,'x'),
                        read_float(child.attrib,'y'))
                    )
                    continue
                elif child.tag == prefix('Xform'):
                    self.Xform = IPC2581_Transform()
                    self.Xform.load(child)
                    continue
                elif child.tag == prefix('UserPrimitiveRef'):
                    self.features.append(child.attrib['id'])
                    continue
                elif child.tag == prefix('Circle'):
                    shape = IPC2581_Circle()
                elif child.tag == prefix('Line'):
                    shape = IPC2581_Line()
                elif child.tag == prefix('RectCenter'):
                    shape = IPC2581_RectCenter()
                elif child.tag == prefix('Oval'):
                    shape = IPC2581_Oval()
                elif child.tag == prefix('Arc'):
                    shape = IPC2581_Arc()
                elif child.tag == prefix('Contour'):
                    shape = IPC2581_Contour()
                elif child.tag == prefix('Polygon'):
                    shape = IPC2581_Polygon()
                elif child.tag == prefix('Polyline'):
                    shape = IPC2581_Polyline()
                else:
                    raise ValueError(f"Unknown geometry type with tag {child.tag}")
                shape.load(child)
                self.features.append(shape)

    def parse_Layer(self):
        layer_node = self.root.find(prefix(f'Ecad/CadData/Layer[@name="{self.name}"]'))
        if layer_node is None:
            raise ValueError(f"Could not find layer {self.name} in <Layer> tags.")
        self.function = layer_node.attrib['layerFunction']
        self.side = layer_node.attrib['side']
        self.polarity = layer_node.attrib['polarity']

    def parse_StackupLayer(self,stackup=None,stackup_group=None):
        """
        :param stackup: stackup name, if more than one (not implemented)
        :param stackup_group: stackup group name, if more than one (not implemented)
        :return:
        """
        sl_node = self.root.find(prefix(f'Ecad/CadData/Stackup/StackupGroup/StackupLayer[@layerOrGroupRef="{self.name}"]'))
        if sl_node is None:
            print(f"Warning: Could not find layer {self.name} in <StackupLayer> tags in default group.")
            return
        self.thickness = read_float(sl_node.attrib,'thickness')
        self.tolPlus = read_float(sl_node.attrib,'tolPlus')
        self.tolMinus = read_float(sl_node.attrib,'tolMinus')
        self.sequence = read_int(sl_node.attrib,'sequence')

    def add_physical_net_point(self,phynetpoint_node : ET.Element):
        """
        Add a physical net point to the list for this layer.
        A physial net point has:
            position x,y
            layerRef
            netNode (END, MIDDLE)
            exposure (COVERED_PRIMARY, COVERED_SECONDARY, EXPOSED)
            via [bool]
        :param phynetpoint_node:
        :return: None
        """
        if phynetpoint_node.tag != prefix('PhyNetPoint'):
            raise ValueError(f"Unexpected tag {phynetpoint_node.tag}. Expected PhyNetPoint.")
        if phynetpoint_node.attrib['layerRef'] != self.name:
            raise ValueError(f"Physical net point node does not correspond to layer {self.name}. Layer of node: {phynetpoint_node.attrib['layerRef']}")
        pnp = IPC2581_Layer.PhysicalNetPoint()
        pnp.position = (read_float(phynetpoint_node.attrib,'x'),
                        read_float(phynetpoint_node.attrib,'y'))
        pnp.net_node = phynetpoint_node.attrib['netNode']
        pnp.exposure = phynetpoint_node.attrib['exposure']
        pnp.via = read_bool(phynetpoint_node.attrib,'via')

        primref_node = phynetpoint_node.find(prefix('StandardPrimitiveRef'))
        if primref_node is not None:
            pnp.primitive_ref = primref_node.attrib['id']

        self.physical_net_points.append(pnp)

    def parse_LayerFeature(self):
        layerfeat_node = self.root.find(prefix(f'Ecad/CadData/Step/LayerFeature[@layerRef="{self.name}"]'))
        if layerfeat_node is None:
            print(f"Warning: Could not find LayerFeature node with layerRef={self.name}")
            return
        for set_node in layerfeat_node.findall(prefix('Set')):
            if 'net' in set_node.attrib.keys():
                net_name = set_node.attrib['net']
                if 'padUsage' in set_node.attrib.keys():
                    # This is a pad or via
                    if set_node.attrib['padUsage'] == 'VIA':
                        via = IPC2581_Layer.NetVia()
                        via.load(set_node)
                        self.vias.append(via)
                    elif set_node.attrib['padUsage'] == 'NONE':
                        pad_not_used = IPC2581_Layer.NetVia()
                        pad_not_used.load(set_node)
                        self.pads_not_used.append(pad_not_used)
                elif 'geometry' in set_node.attrib.keys():
                    # TODO: Hole or SlotCavity
                    pass
                else:
                    # This is just the layer's net geometry, parse each feature
                    # Make sure this net is in the `nets` dictionary
                    if net_name not in self.nets.keys():
                        self.nets[net_name] = IPC2581_Layer.LayerNet(net_name)
                    # Parse
                    layernet = self.nets[net_name]
                    feats_node = set_node.find(prefix('Features'))
                    if feats_node is not None:
                        layernet.load_feature(feats_node)
            else:
                # No-net geometry (e.g. text)
                # ColorRef node
                nonet = IPC2581_Layer.LayerNet('')
                feats_node = set_node.find(prefix('Features'))
                if feats_node is not None:
                    nonet.load_feature(feats_node)
                    self.nonet_geom.append(nonet)

    def parse_Components(self):
        comp_nodes = self.root.findall(prefix(f'Ecad/CadData/Step/Component[@layerRef="{self.name}"]'))
        for comp_node in comp_nodes:
            component = IPC2581_Layer.IPC2581_Component()
            component.load(comp_node)
            self.components.append(component)


class IPC2581_Package:
    def __init__(self,root: ET.Element, name: str):
        self.root = root
        self.name = name
        self.type = ''
        self.pinOne = ''
        self.pinOneOrientation = ''
        self.height = 0.00

        # Outline
        self.outline = None
        self.outline_lineWidth = 0.0
        self.outline_lineEnd = ''

        # PickupPoint
        self.PickupPoint = (0.0, 0.0)

        # SilkScreen
        self.silkscreen_markings = []

        # AssemblyDrawing
        self.asm_dwg_outline = None
        self.asm_dwg_lineEnd = ''
        self.asm_dwg_lineWidth = 0.0
        self.asm_dwg_markings = []

        # Pins
        self.pins = []

        # LandingPattern
        self.land_pads = []

    class IPC2581_Marking:
        def __init__(self):
            self.usage = ''
            self.loc = (0.0, 0.0)
            self.polyline = None
            self.contour = None

        def load(self,marking_node: ET.Element):
            if marking_node.tag != prefix('Marking'):
                raise ValueError(f'Expected Marking tag, instead got {marking_node.tag}.')
            self.usage = marking_node.attrib['markingUsage']
            loc_node = marking_node.find(prefix('Location'))
            if loc_node is not None:
                x = read_float(loc_node.attrib,'x')
                y = read_float(loc_node.attrib,'y')
                self.loc = (x,y)

            poly_node = marking_node.find(prefix('Polyline'))
            if poly_node is not None:
                self.polyline = IPC2581_Polyline()
                self.polyline.load(poly_node)

            contour_node = marking_node.find(prefix('Contour'))
            if contour_node is not None:
                self.contour = IPC2581_Contour()
                self.contour.load(contour_node)

    class IPC2581_Pin:
        def __init__(self):
            self.number = ''  # str to support letter-number pins e.g. B9
            self.type = ''
            self.electricalType = ''
            self.loc = (0.0, 0.0)
            self.std_prim_ref = ''

        def load(self,pin_node: ET.Element):
            if pin_node.tag != prefix('Pin'):
                raise ValueError(f'Expected Pin tag, instead got {pin_node.tag}.')
            self.number = pin_node.attrib['number']
            self.type = pin_node.attrib['type']
            self.electricalType = pin_node.attrib['electricalType']

            loc_node = pin_node.find(prefix('Location'))
            if loc_node is not None:
                x = read_float(loc_node.attrib,'x')
                y = read_float(loc_node.attrib,'y')
                self.loc = (x,y)

            spr_node = pin_node.find(prefix('StandardPrimitiveRef'))
            if spr_node is not None:
                self.std_prim_ref = spr_node.attrib['id']

    def parse_Package(self):
        pkg_node = self.root.find(prefix(f'Ecad/CadData/Step/Package[@name="{self.name}"]'))
        if pkg_node is None:
            print(f"Warning: Could not find Package with name {self.name}")
            return
        self.type = pkg_node.attrib['type']
        self.pinOne = pkg_node.attrib['pinOne']
        self.pinOneOrientation = pkg_node.attrib['pinOneOrientation']
        self.height = read_float(pkg_node.attrib,'height')

        outline_node = pkg_node.find(prefix('Outline'))
        if outline_node is None:
            print(f"Warning: Package with name {self.name} did not have an Outline.")
        else:
            self._parse_Outline(outline_node)

        pickup_node = pkg_node.find(prefix('PickupPoint'))
        if pickup_node is not None:
            x = read_float(pickup_node.attrib,'x')
            y = read_float(pickup_node.attrib,'x')
            self.PickupPoint = (x,y)

        ss_node = pkg_node.find(prefix('SilkScreen'))
        if ss_node is None:
            print(f"Warning: Package with name {self.name} does not have a SilkScreen.")
        else:
            self._parse_SilkScreen(ss_node)

        asm_dwg_node = pkg_node.find(prefix('AssemblyDrawing'))
        if asm_dwg_node is None:
            print(f"Warning: Package with name {self.name} does not have an AssemblyDrawing.")
        else:
            self._parse_AssemblyDrawing(asm_dwg_node)

        # Parse Pin nodes
        pin_nodes = pkg_node.findall(prefix('Pin'))
        for pin_node in pin_nodes:
            pin = IPC2581_Package.IPC2581_Pin()
            pin.load(pin_node)
            self.pins.append(pin)

        # Finally, parse the LandPattern
        land_node = pkg_node.find(prefix('LandPattern'))
        if land_node is None:
            print(f"Warning: Package with name {self.name} does not have a LandPattern.")
        else:
            pad_nodes = land_node.findall(prefix('Pad'))
            for pad_node in pad_nodes:
                pad = IPC2581_Pad()
                pad.load(pad_node)
                self.land_pads.append(pad)

    def _parse_Outline(self, outline_node: ET.Element):
        if outline_node.tag != prefix('Outline'):
            raise ValueError(f'Expected Outline tag, instead got {outline_node.tag}.')
        for shape_node in outline_node:  # usually only one?
            shape_tag = shape_node.tag
            if shape_tag == prefix('LineDesc'):
                self.outline_lineEnd = shape_node.attrib['lineEnd']
                self.outline_lineWidth = read_float(shape_node.attrib, 'lineWidth')
                continue
            elif shape_tag == prefix('Circle'):
                shape = IPC2581_Circle()
            elif shape_tag == prefix('RectCenter'):
                shape = IPC2581_RectCenter()
            elif shape_tag == prefix('Oval'):
                shape = IPC2581_Oval()
            elif shape_tag == prefix('Arc'):
                shape = IPC2581_Arc()
            elif shape_tag == prefix('Contour'):
                shape = IPC2581_Contour()
            elif shape_tag == prefix('Polygon'):
                shape = IPC2581_Polygon()
            elif shape_tag == prefix('Polyline'):
                shape = IPC2581_Polyline()
            else:
                raise ValueError(f"Unknown geometry type with tag {shape_tag}")
            shape.load(shape_node)
            self.outline = shape  # NOTE: If more than one, this needs to be a list
            # Otherwise we're just reassigning


    def _parse_SilkScreen(self, silkscreen_node: ET.Element):
        if silkscreen_node.tag != prefix('SilkScreen'):
            raise ValueError(f'Expected SilkScreen tag, instead got {silkscreen_node.tag}.')

        marking_nodes = silkscreen_node.findall(prefix('Marking'))
        for mn in marking_nodes:
            marking = IPC2581_Package.IPC2581_Marking()
            marking.load(mn)
            self.silkscreen_markings.append(marking)

    def _parse_AssemblyDrawing(self, asm_dwg_node: ET.Element):
        if asm_dwg_node.tag != prefix('AssemblyDrawing'):
            raise ValueError(f'Expected AssemblyDrawing tag, instead got {asm_dwg_node.tag}.')
        outline_node = asm_dwg_node.find(prefix('Outline'))
        if outline_node.tag != prefix('Outline'):
            raise ValueError(f'Expected Outline tag, instead got {outline_node.tag}.')

        for shape_node in outline_node:  # usually only one?
            shape_tag = shape_node.tag
            if shape_tag == prefix('LineDesc'):
                self.asm_dwg_lineEnd = shape_node.attrib['lineEnd']
                self.asm_dwg_lineWidth = read_float(shape_node.attrib, 'lineWidth')
                continue
            elif shape_tag == prefix('Circle'):
                shape = IPC2581_Circle()
            elif shape_tag == prefix('RectCenter'):
                shape = IPC2581_RectCenter()
            elif shape_tag == prefix('Oval'):
                shape = IPC2581_Oval()
            elif shape_tag == prefix('Arc'):
                shape = IPC2581_Arc()
            elif shape_tag == prefix('Contour'):
                shape = IPC2581_Contour()
            elif shape_tag == prefix('Polygon'):
                shape = IPC2581_Polygon()
            elif shape_tag == prefix('Polyline'):
                shape = IPC2581_Polyline()
            else:
                raise ValueError(f"Unknown geometry type with tag {shape_tag}")
            shape.load(shape_node)
            self.asm_dwg_outline = shape  # NOTE: If more than one, this needs to be a list
            # Otherwise we're just reassigning

        # Next get markings
        marking_nodes = asm_dwg_node.findall(prefix('Marking'))
        for mn in marking_nodes:
            marking = IPC2581_Package.IPC2581_Marking()
            marking.load(mn)
            self.asm_dwg_markings.append(marking)





class PCBAssembly:
    def __init__(self,root: ET.Element):
        self.root = root

        # Content
        self.function_mode = ''         # str, e.g. "ASSEMBLY"
        self.function_mode_level = -1   # int, e.g. 3
        self.step_ref = ''              # str, name attribute of <Step> tag
        self.bom_ref = ''               # str, name attribute of <Bom> tag
        self.layer_refs = []            # list of str, name attributes of <Layer> tags and similar (layer names)
        self.color_dictionary = {}      # dict of tuples, color 'id': (r,g,b)
        self.line_desc_units = ''       # units for DictionaryLineDesc
        self.line_desc_dictionary = {}  # 'id': {'lineEnd','lineWidth'}
        self.fill_desc_units = ''       # units for DictionaryFillDesc
        self.fill_desc_dictionary = {}  # 'id': 'fillProperty'
        self.standard_dict_units = ''   # units for DictionaryStandard
        self.standard_dict = {}         # standard dictionary
        self.user_dict_units = ''       # units for DictionaryUser
        self.user_dict = {}             # user dictionary

        # Logistic Header
        self.Role = {}                  # id, roleFunction
        self.Enterprise = {}            # id, code
        self.Person = {}                # name, enterpriseRef, roleRef

        # Bom
        self.Bom = None

        # Profile and Datum
        self.Profile = None
        self.Datum = (0.0, 0.0)

        # Layers
        self.Layers = {}

        # Packages
        self.Packages = {}

        # Initialize
        self.rpf = '{http://webstds.ipc.org/2581}'  # root prefix

        self.parse_Content()
        self.parse_LogisticHeader()
        self.parse_Bom()
        self.parse_HistoryRecord()
        self.parse_Bom()
        self.parse_ECad()

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

        :return: None
        """
        if verbose:
            print("Parsing function mode, step ref, bom ref, layer ref... ", end='')
        fm_node = self.root.find(prefix('Content/FunctionMode'))
        if fm_node is not None:
            if 'mode' in fm_node.attrib:
                self.function_mode = fm_node.attrib['mode']
            if 'level' in fm_node.attrib:
                self.function_mode_level = read_int(fm_node.attrib,'level')

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

    def parse_LogisticHeader(self):
        role_node = self.root.find(prefix('LogisticHeader/Role'))
        if role_node is not None:
            self.Role = role_node.attrib  # id, roleFunction

        enterprise_node = self.root.find(prefix('LogisticHeader/Enterprise'))
        if enterprise_node is not None:
            self.Enterprise = enterprise_node.attrib  # id, code

        person_node = self.root.find(prefix('LogisticHeader/Person'))
        if person_node is not None:
            self.Person = person_node.attrib  # name, enterpriseRef, roleRef

    def parse_HistoryRecord(self):
        pass

    def parse_Bom(self):
        bomnode = self.root.find(prefix('Bom'))
        if bomnode is not None:
            self.Bom = IPC2581_Bom()
            self.Bom.load(bomnode)

    def parse_ECad(self):
        # Construct Layer objects for each layer
        # Parsing is done automatically
        for layer_name in self.layer_refs:
            self.Layers[layer_name] = IPC2581_Layer(self.root,layer_name)

        # Parse Profile
        prof_node = root.find(prefix('Ecad/CadData/Step/Profile'))
        if prof_node is not None:
            for shape_node in prof_node:  # usually only one
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
                elif shape_tag == prefix('Polygon'):
                    shape = IPC2581_Polygon()
                elif shape_tag == prefix('Polyline'):
                    shape = IPC2581_Polyline()
                else:
                    raise ValueError(f"Unknown geometry type with tag {shape_tag}")

                shape.load(shape_node)
                self.Profile = shape
                # NOTE: If more than one shape, this needs to be a list
                # Otherwise we're just reassigning

        datum_node = root.find(prefix('Ecad/CadData/Step/Datum'))
        if datum_node is not None:
            x = read_float(datum_node.attrib,'x')
            y = read_float(datum_node.attrib,'y')
            self.Datum = (x,y)

        # Load packages
        package_names = []
        package_nodes = root.findall(prefix('Ecad/CadData/Step/Package'))
        for pn in package_nodes:
            package_names.append(pn.attrib['name'])
        for pn in package_names:
            pcbpkg = IPC2581_Package(root,pn)
            pcbpkg.parse_Package()
            self.Packages[pn] = pcbpkg

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
            if 'units' in ldu_node.attrib.keys():
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
        dfd_node = self.root.find(prefix('Content/DictionaryFillDesc'))
        if dfd_node is not None:
            if 'units' in dfd_node.attrib.keys():
                self.fill_desc_units = dfd_node.attrib['units']
        fill_desc_nodes = self.root.findall(prefix('Content/DictionaryFillDesc/EntryFillDesc'))
        for fill in fill_desc_nodes:
            if fill is not None:
                fill_id = fill.attrib['id']
                fill_property = fill.find(prefix('FillDesc')).attrib['fillProperty']
                if fill_property is not None:
                    self.fill_desc_dictionary[fill_id] = fill_property

    def _parse_standard_dict(self):
        # Standard dictionary
        dstd_node = self.root.find(prefix('Content/DictionaryStandard'))
        if dstd_node is not None:
            if 'units' in dstd_node.attrib.keys():
                self.standard_dict_units = dstd_node.attrib['units']
        entry_standard_nodes = self.root.findall(prefix('Content/DictionaryStandard/EntryStandard'))
        for es_node in entry_standard_nodes:
            es_id = es_node.attrib['id']
            for shape_node in es_node:  # there should only be one
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
                elif shape_tag == prefix('Polygon'):
                    shape = IPC2581_Polygon()
                elif shape_tag == prefix('Polyline'):
                    shape = IPC2581_Polyline()
                else:
                    raise ValueError(f"Unknown geometry type with tag {shape_tag}")

                shape.load(shape_node)
                self.standard_dict[es_id] = shape

    def _parse_user_dict(self):
        # User dictionary
        dusr_node = self.root.find(prefix('Content/DictionaryStandard'))
        if dusr_node is not None:
            if 'units' in dusr_node.attrib.keys():
                self.user_dict_units = dusr_node.attrib['units']
        entry_user_nodes = self.root.findall(prefix('Content/DictionaryUser/EntryUser'))
        for eu_node in entry_user_nodes:
            eu_id = eu_node.attrib['id']
            us_node = eu_node.find(prefix('UserSpecial'))
            if us_node is not None:
                us_obj = IPC2581_UserSpecial()
                us_obj.load(us_node)
                self.user_dict[eu_id] = us_obj


# For testing:
# def draw_polyline(polyline: IPC2581_Polyline, ax, canvas, color='k'):
#     pts_x = [pt[0] for pt in polyline.points]
#     pts_y = [pt[1] for pt in polyline.points]
#     # if a straigth line, connections is None
#     # if curved, connections is an IPC2581_PolyStepCurve
#     for i,conn in enumerate(polyline.connections):
#         if conn is None:
#             # Draw from here to next point
#             print(f'{pts_x[i:i+2]}, {pts_y[i:i+2]}')
#             ax.plot(pts_x[i:i+2], pts_y[i:i+2],color=color)  # +2 for slicing
#         else:
#             # Draw curved segment
#             pass
#     canvas.draw()
#
# def draw_pkg(pkg: IPC2581_Package):
#     fig,(ax) = plt.subplots(1,1,figsize=(8,8))
#     # for mark in pkg.asm_dwg_markings:
#     #     print("Marking")
#     #     draw_polyline(mark.polyline,ax,fig.canvas,color=None)
#     for mark in pkg.silkscreen_markings:
#         print("Marking")
#         if mark.polyline is not None:
#             draw_polyline(mark.polyline,ax,fig.canvas,color='y')
#         elif mark.contour is not None:
#             draw_polyline(mark.contour,ax,fig.canvas,color='b')
#     ax.set_aspect(1)


if __name__ == '__main__':
    """
    STATUS
    ===========
    Package is finished
    Basic geometry tags are finished
    LayerFeature is most of the way there
    Components are done
    Datum and Profile have been implemented
    
    Hole and SlotCavity tags have not been implemented  (part of Set nodes)
    PadStack has not been implemented (I still don't fully understand it)
    Rendering!
    """
    fname = 'examples/BeagleBone_Black_RevB6_nologo174-AllegroOut/BeagleBone_Black_RevB6_nologo174.xml'
    # fname = 'examples/testcase10-Rev C data/testcase10-RevC-Full.xml'
    print("Loading file... ",end='')
    tree = ET.parse(fname)
    root = tree.getroot()
    print("Done")
    test_pcb = PCBAssembly(root)
    
    # For testing:
    # pkg_name = 'SD-MICRO-SCHA5B0300'
    # pkg_name = '0402'
    # pkg_name = 'BGA153_P14_P5_11P5X13'
    # draw_pkg(test_pcb.Packages[pkg_name])
