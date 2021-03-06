from rdkit import Chem
import numpy as np
from functools import reduce

"""
rdkit mol manipulations
"""
#TODO maybe better to place somewhere else?
def mol_from_multiple_pdb_files(file_list, removeHs = False):
    """
    assumes all pdb belong to the same molecule entity
    """
    pdb_string = reduce(lambda a, b : a + b, [open(i, "r").read()[:-4] for i in file_list]) + "END\n"
    return Chem.MolFromPDBBlock(pdb_string, removeHs = removeHs)


def get_carbonyl_O(mol):
    return [i[0] for i in get_atom_mapping(mol, "[C]=[O:1]")]
def get_amine_H(mol):
    return [i[0] for i in get_atom_mapping(mol, "[N]-[H:1]")]
def get_1_4_pairs(mol, smirks_1_4 = "[O:1]=[C:2]@;-[NX3:3]-[CX4H3:4]" ):
    return get_atom_mapping(mol, smirks_1_4)
def get_1_5_pairs(mol, smirks_1_5 = "[O:1]=[C]@;-[CX4H1,CX4H2]-[NX3H1]-[H:5]"):
    return get_atom_mapping(mol, smirks_1_5)

def get_atom_mapping(mol, smirks):
    qmol = Chem.MolFromSmarts(smirks)
    ind_map = {}
    for atom in qmol.GetAtoms():
        map_num = atom.GetAtomMapNum()
        if map_num:
            ind_map[map_num - 1] = atom.GetIdx()
    map_list = [ind_map[x] for x in sorted(ind_map)]
    matches = list()
    for match in mol.GetSubstructMatches(qmol, uniquify = False) :
        mas = [match[x] for x in map_list]
        matches.append(tuple(mas))
    return matches


def _decide_indices_order(indices):
    """
    arrange indices such the first entry in list has smallest index, the second has the second smallest index
    """

    indices = list(np.roll(indices, -np.argwhere(indices == np.min(indices))[0][0]))
    second_entry, last_entry = indices[1], indices[-1]
    if second_entry > last_entry : #reverse list
        indices = indices[1:] + [indices[0]]
        indices.reverse()
    return [int(i) for i in indices]

def get_rings(mol):
    for ring in mol.GetRingInfo().AtomRings():
        yield ring

def get_largest_ring(mol):
    out = []
    for r in get_rings(mol):
        if len(r) > len(out):
            out = r
    out = list(out)
    return _decide_indices_order(out)

def get_neighbor_indices(mol, indices):
    out = []
    for i in indices:
        out += [a.GetIdx() for a in mol.GetAtomWithIdx(i).GetNeighbors()]
    out = indices + out
    #set does not necessarily preserve order
    return list(set(out))

def get_neighbour_indices(mol, indices):
    return get_neighbor_indices(mol, indices)


def mol_with_atom_index( mol ):
    atoms = mol.GetNumAtoms()
    for idx in range( atoms ):
        mol.GetAtomWithIdx( idx ).SetProp( 'molAtomMapNumber', str( mol.GetAtomWithIdx( idx ).GetIdx() ) )
    return mol


def draw_mol_with_property( mol, property, **kwargs):
    """
    http://rdkit.blogspot.com/2015/02/new-drawing-code.html

    Parameters
    ---------
    property : dict
        key atom idx, val the property (need to be stringfiable)
    """
    import copy
    from rdkit.Chem import Draw
    from rdkit.Chem import AllChem

    def run_from_ipython():
        try:
            __IPYTHON__
            return True
        except NameError:
            return False


    AllChem.Compute2DCoords(mol)
    mol = copy.deepcopy(mol) #FIXME do I really need deepcopy?

    for idx in property:
        # opts.atomLabels[idx] =
        mol.GetAtomWithIdx( idx ).SetProp( 'molAtomMapNumber', "({})".format( str(property[idx])))

    mol = Draw.PrepareMolForDrawing(mol, kekulize=False) #enable adding stereochem

    if run_from_ipython():
        from IPython.display import SVG, display
        if "width" in kwargs and type(kwargs["width"]) is int and "height" in kwargs and type(kwargs["height"]) is int:
            drawer = Draw.MolDraw2DSVG(kwargs["width"], kwargs["height"])
        else:
            drawer = Draw.MolDraw2DSVG(500,250)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        display(SVG(drawer.GetDrawingText().replace("svg:", "")))
    else:
        if "width" in kwargs and type(kwargs["width"]) is int and "height" in kwargs and type(kwargs["height"]) is int:
            drawer = Draw.MolDraw2DCairo(kwargs["width"], kwargs["height"])
        else:
            drawer = Draw.MolDraw2DCairo(500,250) #cairo requires anaconda rdkit
        # opts = drawer.drawOptions()
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        #
        # with open("/home/shuwang/sandbox/tmp.png","wb") as f:
        #     f.write(drawer.GetDrawingText())

        import io
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg

        buff = io.BytesIO()
        buff.write(drawer.GetDrawingText())
        buff.seek(0)
        plt.figure()
        i = mpimg.imread(buff)
        plt.imshow(i)
        plt.show()
        # display(SVG(drawer.GetDrawingText()))
