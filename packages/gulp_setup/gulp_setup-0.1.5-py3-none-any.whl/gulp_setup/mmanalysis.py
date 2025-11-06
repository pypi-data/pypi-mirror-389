#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright : see accompanying license files for details
'''
Code borrowed from autografs and modified.
'''

import numpy
import os
from scipy.sparse import csgraph
from ase.data import covalent_radii
from ase.neighborlist import NeighborList
from itertools import combinations
import networkx as nx
# from ase import neighborlist
# from collections import deque
import mofstructure.mofdeconstructor as mof_deconstructor

# import gulp_setup
# from __data__ import uff as uff_path

uff_path = os.path.dirname(os.path.abspath(__file__))
# os.path.dirname(os.path.abspath('__data__/uff'))


def is_metal(symbols):
    """
    Check wether symbols in a list are metals
    """
    symbols = numpy.array([symbols]).flatten()
    metals = ['Li', 'Be', 'Al', 'Sc', 'Ti', 'V', 'Cr', 'Mn',
              'Fe', 'Co', 'Ni', 'Cu', 'Zn',
              'Ga', 'Ge', 'Y', 'Zr', 'Nb', 'Mo',
              'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In',
              'Sn', 'Sb', 'La', 'Ce', 'Pr', 'Nd',
              'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho',
              'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta',
              'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
              'Tl', 'Pb', 'Bi', 'Po', 'Fr', 'Ra',
              'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am',
              'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md',
              'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs',
              'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl',
              'Mc', 'Lv', 'Ts', 'Og']
    return numpy.isin(symbols, metals)


def region_representative_system(ase_atom, regions):
    for keys in regions:
        data = regions[keys][0]
        atoms = mof_deconstructor.wrap_systems_in_unit_cell(ase_atom[data])
        atoms.info['concentration'] = len(regions[keys])
        atoms.write(f'region_{keys}.xyz')


def is_alkali(symbols):
    """
    Check wether symbols in a list are alkali
    """
    symbols = numpy.array([symbols]).flatten()
    alkali = ['Li', 'Be', 'Na', 'Mg', 'K', 'Ca', 'Rb', 'Sr', 'Cs', 'Ba']
    return numpy.isin(symbols, alkali)


def read_uff_library(library="uff4mof"):
    """
    Return the UFF library as a numpy array
    """
    # uff_file = +"/uff4mof".format(library)
    uff_file = os.path.join(uff_path, '__data__', 'uff', f"{library}.csv")
    with open(uff_file, "r", encoding='utf-8') as lib:
        lines = [line.split(",")
                 for line in lib.read().splitlines()
                 if not line.startswith("#")]
        # symbol,radius,angle,coordination
        ufflib = {s: numpy.array([r, a, c],
                                 dtype=numpy.float32) for s, r, a, c in lines}
    return ufflib


def find_regions(connected_components,
                 atoms_indices_at_breaking_point,
                 all_regions):
    '''
    Function to find the regions in the MOF.
    parameters
    ----------
    connected_components: List of connected components in the MOF.
    atoms_indices_at_breaking_point: List of indices of
    atoms at the breaking point.
    all_regions: List of all regions in the MOF.
    '''
    flattened_list = [item for pair in
                      atoms_indices_at_breaking_point.items()
                      for item in pair
                      ]
    point_of_ext = {}
    all_atom_mapping = {}
    for number, region in enumerate(all_regions):
        region_point_of_ext = []
        index_in_region = all_regions[region]
        atom_mapping = [connected_components[i] for i in index_in_region]
        all_atom_mapping[number+1] = atom_mapping
        for sub in atom_mapping:
            tmp = []
            for indices in sub:
                if indices in flattened_list:
                    tmp.append(indices)
            region_point_of_ext.append(tmp)
        point_of_ext[number+1] = region_point_of_ext
    return point_of_ext, all_atom_mapping


def find_sbu_regions(ase_atom):
    '''
    Function to find the SBU regions in the MOF.
    parameters
    ----------
    ase_atom: ASE Atoms object representing the MOF
    return: A
    '''
    connected_components, atoms_indices_at_breaking_point, _, all_regions =\
        mof_deconstructor.secondary_building_units(ase_atom)
    point_of_ext, all_atom_mapping =\
        find_regions(connected_components,
                     atoms_indices_at_breaking_point,
                     all_regions)
    return point_of_ext, all_atom_mapping

# def get_bond_matrix(sbu):
#     """Guesses the bond order in neighbourlist based on covalent radii
#     the radii for BO > 1 are extrapolated by removing 0.1 Angstroms by order
#     see Beatriz Cordero, Veronica Gomez, Ana E. Platero-Prats,
# Marc Reves, Jorge Echeverria,
#     Eduard Cremades, Flavia Barragan and Santiago Alvarez (2008).
#     "Covalent radii revisited".
#     Dalton Trans. (21): 2832-2838
#     http://dx.doi.org/10.1039/b801115j
#     """
#     # first guess
#     bonds = numpy.zeros((len(sbu), len(sbu)))
#     symbols = numpy.array(sbu.get_chemical_symbols())
#     numbers = numpy.array(sbu.get_atomic_numbers())
#     positions = numpy.array(sbu.get_positions())
#     BO1 = numpy.array([covalent_radii[n] if n>0 else 0.7 for n in numbers])
#     BO2 = BO1 - 0.15
#     BO3 = BO2 - 0.15
#     nl1 = NeighborList(cutoffs=BO1, bothways=True, self_interaction=False, skin=0.1)
#     nl2 = NeighborList(cutoffs=BO2, bothways=True, self_interaction=False, skin=0.1)
#     nl3 = NeighborList(cutoffs=BO3, bothways=True, self_interaction=False, skin=0.1)
#     nl1.update(sbu); nl2.update(sbu); nl3.update(sbu)
#     for atom in sbu:
#         i1, _ = nl1.get_neighbors(atom.index)
#         i2, _ = nl2.get_neighbors(atom.index)
#         i3, _ = nl3.get_neighbors(atom.index)
#         bonds[atom.index, i1] = 1.0
#         bonds[atom.index, i2] = 2.0
#         bonds[atom.index, i3] = 3.0
#     # cleanup with particular cases
#     # identify particular atoms
#     hydrogens = numpy.where(symbols == "H")[0]
#     metals = numpy.where(is_metal(symbols))[0]
#     alkali = numpy.where(is_alkali(symbols))[0]
#     # the rest is dubbed "organic"
#     organic = numpy.ones(bonds.shape)
#     organic[hydrogens, :] = False
#     organic[metals, :] = False
#     organic[alkali, :] = False
#     organic[:, hydrogens] = False
#     organic[:, metals] = False
#     organic[:, alkali] = False
#     organic = numpy.where(organic)[0]
#     # Hydrogen has BO of 1
#     bonds_h = bonds[hydrogens]
#     bonds_h[bonds_h > 1.0] = 1.0
#     bonds[hydrogens, :] = bonds_h
#     bonds[:, hydrogens] = bonds_h.T
#     # Metal-Metal bonds: if no special case, nominal bond
#     ix = numpy.ix_(metals, metals)
#     bix = bonds[ix]
#     bix[numpy.nonzero(bix)] = 0.25
#     bonds[ix] = bix
#     # no H-Metal bonds
#     ix = numpy.ix_(metals, hydrogens)
#     bonds[ix] = 0.0
#     ix = numpy.ix_(hydrogens, metals)
#     bonds[ix] = 0.0
#     # no alkali-alkali bonds
#     ix = numpy.ix_(alkali, alkali)
#     bonds[ix] = 0.0
#     # no alkali-metal bonds
#     ix = numpy.ix_(metals, alkali)
#     bonds[ix] = 0.0
#     ix = numpy.ix_(alkali, metals)
#     bonds[ix] = 0.0
#     # metal-organic is coordination bond
#     ix  = numpy.ix_(metals, organic)
#     bix = bonds[ix]
#     bix[numpy.nonzero(bix)] = 0.5
#     bonds[ix] = bix
#     ix = numpy.ix_(organic, metals)
#     bix = bonds[ix]
#     bix[numpy.nonzero(bix)] = 0.5
#     bonds[ix] = bix
#     # aromaticity and rings
#     rings = []
#     # first, use the compressed sparse graph object
#     # we only care about organic bonds and not hydrogens
#     graph_bonds = numpy.array(bonds > 0.99, dtype=float)
#     graph_bonds[hydrogens, :] = 0.0
#     graph_bonds[:, hydrogens] = 0.0
#     graph = csgraph.csgraph_from_dense(graph_bonds)
#     for sg in graph.indices:
#         subgraph = graph[sg]
#         for i, j in combinations(subgraph.indices, 2):
#             t0 = csgraph.breadth_first_tree(graph, i_start=i, directed=False)
#             t1 = csgraph.breadth_first_tree(graph, i_start=j, directed=False)
#             t0i = t0.indices
#             t1i = t1.indices
#             ring = sorted(set(list(t0i)+list(t1i)+[i, j, sg]))
#             # some conditions
#             seen = (ring in rings)
#             isring = (sorted(t0i[1:]) == sorted(t1i[1:]))
#             bigenough = (len(ring) >= 5)
#             smallenough = (len(ring) <= 10)
#             if isring and not seen and bigenough and smallenough:
#                 rings.append(ring)

#     # we now have a list of all the shortest rings within
#     # the molecular graph. If planar, the ring might be aromatic
#     aromatic_epsilon = 0.1
#     aromatic = []
#     for ring in rings:
#         homocycle = (symbols[ring] == "C").all()
#         heterocycle = numpy.in1d(symbols[ring], numpy.array(["C", "S", "N", "O"])).all()
#         if (homocycle and (len(ring) % 2) == 0) or heterocycle:
#             ring_positions = positions[ring]
#             # small function for coplanarity
#             coplanar = all([numpy.linalg.det(numpy.array(x[:3]) - x[3]) < aromatic_epsilon
#                             for x in combinations(ring_positions, 4)])
#             if coplanar:
#                 aromatic.append(ring)
#     # aromatic bond fixing
#     aromatic = numpy.array(aromatic).ravel()

#     ix = numpy.ix_(aromatic, aromatic)
#     ix = tuple([i.astype(int) for i in ix])
#     bix = bonds[ix]
#     # bix       = bonds[ix]
#     bix[numpy.nonzero(bix)] = 1.5
#     bonds[ix] = bix
#     # hydrogen bonds
#     return bonds


def get_bond_matrix(sbu):
    """
    Guesses bond order matrix using covalent
    radii + networkx for ring detection.
    """
    bonds = numpy.zeros((len(sbu), len(sbu)))
    symbols = numpy.array(sbu.get_chemical_symbols())
    numbers = numpy.array(sbu.get_atomic_numbers())
    positions = numpy.array(sbu.get_positions())

    BO1 = numpy.array([covalent_radii[n] if n > 0 else 0.7 for n in numbers])
    BO2 = BO1 - 0.15
    BO3 = BO2 - 0.15

    nl1 = NeighborList(cutoffs=BO1,
                       bothways=True,
                       self_interaction=False,
                       skin=0.1)
    nl2 = NeighborList(cutoffs=BO2,
                       bothways=True,
                       self_interaction=False,
                       skin=0.1)
    nl3 = NeighborList(cutoffs=BO3,
                       bothways=True,
                       self_interaction=False,
                       skin=0.1)

    nl1.update(sbu)
    nl2.update(sbu)
    nl3.update(sbu)

    for atom in sbu:
        i1, _ = nl1.get_neighbors(atom.index)
        i2, _ = nl2.get_neighbors(atom.index)
        i3, _ = nl3.get_neighbors(atom.index)
        bonds[atom.index, i1] = 1.0
        bonds[atom.index, i2] = 2.0
        bonds[atom.index, i3] = 3.0

    hydrogens = numpy.where(symbols == "H")[0]
    metals = numpy.where(is_metal(symbols))[0]
    alkali = numpy.where(is_alkali(symbols))[0]
    organic = numpy.ones(bonds.shape[0], dtype=bool)
    organic[hydrogens] = False
    organic[metals] = False
    organic[alkali] = False

    # bonds[hydrogens][:, bonds[hydrogens] > 1.0] = 1.0
    bonds[hydrogens, :] = numpy.clip(bonds[hydrogens, :], 0, 1.0)
    bonds[:, hydrogens] = numpy.clip(bonds[:, hydrogens], 0, 1.0)
    bonds[:, hydrogens] = bonds[hydrogens].T

    ix = numpy.ix_(metals, metals)
    bonds[ix][bonds[ix] > 0] = 0.25
    bonds[numpy.ix_(metals, hydrogens)] = 0.0
    bonds[numpy.ix_(hydrogens, metals)] = 0.0
    bonds[numpy.ix_(alkali, alkali)] = 0.0
    bonds[numpy.ix_(metals, alkali)] = 0.0
    bonds[numpy.ix_(alkali, metals)] = 0.0

    ix = numpy.ix_(metals, numpy.where(organic)[0])
    bonds[ix][bonds[ix] > 0] = 0.5
    bonds[ix[::-1]][bonds[ix[::-1]] > 0] = 0.5

    # -----------------
    # Ring detection
    # -----------------
    # Build graph from strong bonds (single + double)
    graph = nx.Graph()
    for i in range(len(sbu)):
        for j in range(i+1, len(sbu)):
            if bonds[i, j] >= 1.0 and symbols[i] != "H" and symbols[j] != "H":
                graph.add_edge(i, j)

    # Find all cycles (rings)
    aromatic_rings = []
    for cycle in nx.cycle_basis(graph):
        if 5 <= len(cycle) <= 10:
            ring_symbols = symbols[cycle]
            homocycle = numpy.all(ring_symbols == "C")
            heterocycle = numpy.in1d(ring_symbols, ["C", "S", "N", "O"]).all()
            if (homocycle and len(cycle) % 2 == 0) or heterocycle:
                coords = positions[cycle]
                # Check coplanarity
                coplanar = True
                for quad in combinations(coords, 4):
                    matrix = numpy.vstack(quad[:3]) - quad[3]
                    if abs(numpy.linalg.det(matrix)) >= 0.1:
                        coplanar = False
                        break
                if coplanar:
                    aromatic_rings.append(cycle)

    # Aromatic bond fixing
    for ring in aromatic_rings:
        for i, j in combinations(ring, 2):
            if bonds[i, j] > 0:
                bonds[i, j] = 1.5
                bonds[j, i] = 1.5

    return bonds


def uff_symbol(atom):
    """Returns the first twol letters of a UFF parameters"""
    sym = atom.symbol
    if len(sym) == 1:
        sym = ''.join([sym, '_'])
    return sym


def best_angle(a,
               sbu,
               indices):
    """Calculates the most common angle around an atom"""
    # linear case
    if len(indices) <= 1:
        da = 180.0
    else:
        angles = numpy.array([sbu.get_angle(a1, a, a3, mic=True)
                              for a1, a3 in combinations(indices,
                                                         2)]).reshape(-1, 1)
        if angles.shape[0] > 1:
            # do some clustering on the angles, keep most frequent
            from scipy.cluster.hierarchy import fclusterdata as cluster
            clusters = cluster(angles, 10.0, criterion='distance')
            counts = numpy.bincount(clusters)
            da = angles[numpy.where(clusters == numpy.argmax(counts))].mean()
        else:
            da = angles[0, 0]
    return da


def best_radius(a,
                sbu,
                indices,
                ufflib):
    """Return the radius, according to the neighbors of an atom"""
    if len(indices) == 0:
        d1 = 0.7
    else:
        # the average of covalent radii will be used for distances
        others = [uff_symbol(at) for at in sbu[indices] if at.symbol != "X"]
        if len(others) == 0:
            d1 = 0.7
        else:
            d1 = numpy.array([numpy.array([v[0] for k, v in ufflib.items()
                                           if k.startswith(s)]).mean()
                              for s in others]).mean()
    # get the distances also
    d0 = sbu.get_distances(a, indices, mic=True).mean()
    dx = d0-d1
    return dx


def best_type(dx,
              da,
              dc,
              ufflib,
              types):
    """Chooses the best UFF type according to neighborhood."""
    mincost = 1000.0
    mintyp = None
    for typ in types:
        xx, aa, cc = ufflib[typ]
        cost_x = ((dx-xx)**2)/2.50
        cost_a = ((da-aa)**2)/180.0
        cost_c = ((dc-cc)**2)/4.0
        cost = cost_x+cost_a+cost_c
        if cost < mincost:
            mintyp = typ
            mincost = cost
    return mintyp


def analyze_mm(sbu):
    """Returns the UFF types and bond matrix for an ASE Atoms."""
    ufflib = read_uff_library(library="uff4mof")

    if len(sbu) == 1:
        bonds = numpy.zeros((1, 1))
        atom = sbu[0]
        symbol = uff_symbol(atom)
        uff_types = [k for k in ufflib.keys()
                     if k.startswith(symbol)]
        mmtypes = numpy.array([uff_types[0]
                               if uff_types else symbol])  # fallback
        return bonds, mmtypes

    bonds = get_bond_matrix(sbu)
    mmtypes = [None,]*len(sbu)
    for atom in sbu:
        if atom.symbol == "X":
            continue
        # get the starting symbol in uff nomenclature
        symbol = uff_symbol(atom)
        # narrow the choices
        uff_types = [k for k in ufflib.keys() if k.startswith(symbol)]
        these_bonds = bonds[atom.index].copy()
        # if only one choice, use it
        if len(uff_types) == 1:
            mmtypes[atom.index] = uff_types[0]
        # aromatics are easy also
        elif (numpy.abs(these_bonds-1.5) < 1e-6).any():
            uff_types = [typ for typ in uff_types if typ.endswith("R")]
            mmtypes[atom.index] = uff_types[0]
        else:
            indices = numpy.where(these_bonds >= 0.25)[0]
            # coordination
            dc = len(indices)
            # angle
            da = best_angle(atom.index, sbu, indices)
            # radius
            dx = best_radius(atom.index, sbu, indices, ufflib)
            # complete data
            mmtypes[atom.index] = best_type(dx, da, dc, ufflib, uff_types)
    # now correct the dummies
    for xi in [x.index for x in sbu if x.symbol == "X"]:
        bonded = numpy.argmax(bonds[xi])
        mmtypes[xi] = mmtypes[bonded]
    mmtypes = numpy.array(mmtypes)
    bonds = numpy.array(bonds)
    return bonds, mmtypes


def find_key_by_value(data, target):
    """
    Find the key in a dictionary where the target value is
    located within the nested lists.
    parameters
    ----------
    data: Dictionary with lists of lists as values.
    target: Value to search for within the nested lists.
    Returns:
    -------
    Key in the dictionary where the target value is located
    within the nested lists.
    """
    for key, value in data.items():
        for sublist in value:
            if target in sublist:
                return key
    return None


def write_gin(path, atoms, bonds, mmtypes, add_c_if_2d=False, c_length=80.0):
    """Write a GULP input file to disc

    Parameters
    ----------
    path: str or Path
        the file path to the file object
        where the chemical information will
        be written
    atoms: ase.Atoms
        the chemical information
    bonds: numpy.array
        the block symmetric matrix of bond orders
    mmtypes: [str, ...]
        the UFF atomic types

    Returns
    -------
    None
    """
    with open(path, "w") as fileobj:
        fileobj.write(("opti conp molmec noautobond conjugate " "cartesian unit positive unfix\n"))
        fileobj.write("maxcyc 100\n")
        fileobj.write("switch bfgs gnorm 1.0\n")
        pbc = atoms.get_pbc()
        if pbc.any():
            cell = atoms.get_cell().tolist()
            if not pbc[2]:
                if add_c_if_2d:
                    # Emulate vacuum by switching to full 3D vectors with a big c
                    fileobj.write("vectors\n")
                    fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[0]))
                    fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[1]))
                    fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(0.0, 0.0, float(c_length)))
                else:
                    fileobj.write("{0}\n".format("svectors"))
                    fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[0]))
                    fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[1]))
            else:
                fileobj.write("{0}\n".format("vectors"))
                fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[0]))
                fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[1]))
                fileobj.write("{0:.3f} {1:.3f} {2:.3f}\n".format(*cell[2]))
        fileobj.write("{0}\n".format("cartesian"))
        symbols = atoms.get_chemical_symbols()
        # We need to map MMtypes to numbers. We'll do it via a dictionary
        symb_types = []
        mmdic = {}
        types_seen = 1
        for m, s in zip(mmtypes, symbols):
            if m not in mmdic:
                mmdic[m] = "{0}{1}".format(s, types_seen)
                types_seen += 1
                symb_types.append(mmdic[m])
            else:
                symb_types.append(mmdic[m])
        # write it
        for (
            s,
            (x, y, z),
        ) in zip(symb_types, atoms.get_positions()):
            fileobj.write(("{0:<4} {1:<7} {2:<15.8f} " "{3:<15.8f} {4:<15.8f}\n").format(s, "core", x, y, z))
        fileobj.write("\n")
        bondstring = {
            4: "quadruple",
            3: "triple",
            2: "double",
            1.5: "resonant",
            1.0: "",
            0.5: "half",
            0.25: "quarter",
        }
        # write the bonding
        for (i0, i1), b in numpy.ndenumerate(bonds):
            if i0 < i1 and b > 0.0:
                fileobj.write(("{0} {1:<4} {2:<4} {3:<10}" "\n").format("connect", i0 + 1, i1 + 1, bondstring[b]))
        fileobj.write("\n")
        fileobj.write("{0}\n".format("species"))
        for k, v in mmdic.items():
            fileobj.write("{0:<5} {1:<5}\n".format(v, k))
        fileobj.write("\n")
        fileobj.write("library uff4mof\n")
        fileobj.write("\n")
        name = ".".join(path.split("/")[-1].split(".")[:-1])
        fileobj.write("output movie xyz {0}.xyz\n".format(name))
        fileobj.write("output cssr {0}.cssr\n".format(name))
        fileobj.write("output gen {0}.gen\n".format(name))
        if sum(pbc) == 3:
            fileobj.write("output cif {0}.cif\n".format(name))
        return None

def write_gin_with_region(path,
                          atoms,
                          bonds,
                          mmtypes,
                          lattice='conp'):
    """Write an GULP input file to disc"""
    _, regions = find_sbu_regions(atoms)
    with open(path, "w") as fileobj:
        fileobj.write('opti ' + lattice + ' molmec noautobond conjugate cartesian unit positive unfix\n')
        fileobj.write('maxcyc 500\n')
        fileobj.write('switch bfgs gnorm 1.0\n')
        pbc = atoms.get_pbc()
        if pbc.any():
            cell = atoms.get_cell().tolist()
            if not pbc[2]:
                fileobj.write('{0}\n'.format('svectors'))
                fileobj.write('{0:.3f} {1:.3f} {2:.3f}\n'.format(*cell[0]))
                fileobj.write('{0:.3f} {1:.3f} {2:.3f}\n'.format(*cell[1]))
            else:
                fileobj.write('{0}\n'.format('vectors'))
                fileobj.write('{0:.3f} {1:.3f} {2:.3f}\n'.format(*cell[0]))
                fileobj.write('{0:.3f} {1:.3f} {2:.3f}\n'.format(*cell[1]))
                fileobj.write('{0:.3f} {1:.3f} {2:.3f}\n'.format(*cell[2]))
        fileobj.write('{0}\n'.format('cartesian'))
        symbols = atoms.get_chemical_symbols()
        # We need to map MMtypes to numbers. We'll do it via a dictionary
        symb_types = []
        mmdic = {}
        types_seen = 1
        for m, s in zip(mmtypes, symbols):
            if m not in mmdic:
                mmdic[m] = "{0}{1}".format(s, types_seen)
                types_seen += 1
                symb_types.append(mmdic[m])
            else:
                symb_types.append(mmdic[m])
        # write it

        for s, (x, y, z), atom_index in zip(symb_types,
                                            atoms.get_positions(),
                                            range(len(symbols))
                                            ):
            # fileobj.write('{0:<4} {1:<7} {2:<15.8f} {3:<15.8f} {4:<15.8f} region {5}\n'.format(s, 'core', x, y, z, regions[atom_index]))
            fileobj.write('{0:<4} {1:<7} {2:<15.8f} {3:<15.8f} {4:<15.8f} region {5}\n'.format(s, 'core', x, y, z, find_key_by_value(regions, atom_index)))
        fileobj.write('\n')
        bondstring = {4: 'quadruple',
                      3: 'triple',
                      2: 'double',
                      1.5: 'resonant',
                      1.0: '',
                      0.5: 'half',
                      0.25: 'quarter'}
        # write the bonding
        for (i0, i1), b in numpy.ndenumerate(bonds):
            if i0 < i1 and b > 0.0:
                fileobj.write('{0} {1:<4} {2:<4} {3:<10}\n'.format('connect', i0 + 1, i1 + 1, bondstring[b]))
        fileobj.write('\n')
        fileobj.write('{0}\n'.format('species'))
        for k, v in mmdic.items():
            fileobj.write('{0:<5} {1:<5}\n'.format(v, k))

        fileobj.write('\n')
        fileobj.write('{0}\n'.format('constraints'))
        fileobj.write('\n')
        fileobj.write('library uff4mof\n')
        fileobj.write('\n')
        name = ".".join(path.split("/")[-1].split(".")[:-1])
        fileobj.write('dump every  10 {0}.res\n'.format(name))

        # fileobj.write('output movie xyz {0}.xyz\n'.format(name))
        # fileobj.write('output gen {0}.gen\n'.format(name))
        if sum(pbc) == 3:
            fileobj.write('output cif {0}_opt.cif\n'.format(name))
        fileobj.write('output xyz {0}_opt.xyz\n'.format(name))
        region_representative_system(atoms, regions)
        return None
