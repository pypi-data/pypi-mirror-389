#!/bin/python
'''
A simple script that reads cif files that ase does not read.
It works uniquely with python3.6
'''
# __name__ = "Gulp.writer"
# __author__ = "Dinga Wonanke"

import os
from ase.io import read
import glob
from gulp_setup import mmanalysis as mm
import argparse


#from cif import CIFBlock, parse_cif_ase, parse_cif, parse_cif_pycodcif

# '''
# A simple line of coord to parse input file
# '''
# job_type = ''
# if len(sys.argv) == 2:
#     qcin = sys.argv[1]
#     qc_base = qcin.split('.')[0]
#     job_type = 'normal'
# elif len(sys.argv) == 3:
#     qcin = sys.argv[1]
#     qc_base = qcin.split('.')[0]
#     job_type = 'kick'
#     ext = sys.argv[2]

# else:
#     print ('Try: python Gulp_setup.py name_of_cif_file')
#     sys.exit()


def make_directory(qc_base):
    '''
    Make a directory for the job
    '''
    if not os.path.exists(qc_base):
        os.makedirs(qc_base)
    # shutil.move(qc_base+'*', qc_base)
    os.system('mv ' + qc_base + '.*   ' + qc_base)
    return


def put_contents(filename, output):
    with open(filename, 'w') as f:
        f.writelines(output)
    return

def Submit(qc_base, dir):
    New_input =[]
    New_input.append('#!/bin/bash\n')
    New_input.append('#SBATCH --partition=single\n')
    New_input.append('#SBATCH --nodes=1\n')
    New_input.append('#SBATCH --cpus-per-task=16\n')
    New_input.append('#SBATCH --time=00-10:60:00\n')
    New_input.append('#SBATCH --mem=16gb\n')
    New_input.append('#SBATCH -J  ' + qc_base +'\n')
    New_input.append('source ~/.bash_profile\n')
    New_input.append('sleep 10\n')
    New_input.append('$HOME/gulp-6.0/Src/gulp < ' + qc_base + '.gin  >  ' + qc_base + '.got \n' )
    new_file = 'submita.sh'
    put_contents(new_file, New_input)
    os.system('mv ' + new_file+ '  ' + dir)
    return

def find_cifs(qcin_folder):
    """
    Find CIF files in the current folder or the qcin folder.

    :param qcin_folder: The qcin folder to search for CIF files.
    :return: List of paths to CIF files found.
    """
    current_cifs = glob.glob("./*.cif")
    qcin_cifs = glob.glob(os.path.join(qcin_folder, "*.cif"))
    return current_cifs + qcin_cifs

def gulp_input(qcin, lattice='conv'):
    # Reading and writing gulp file
    #    File = parse_cif_ase(qcin)
    #    for structure in File:
    #       all_atoms_append.append(structure.get_atoms())
    #        sbu =all_atoms_append[0]
    all_atoms_append = []
    qc_base = qcin[:qcin.rindex('.')]
    sbu = read(qcin)
    bonds, mmtypes = mm.analyze_mm(sbu)
    out_file = qc_base+'.gin'
    mm.write_gin(out_file, sbu, bonds, mmtypes, lattice)
    return


def gulp_input2(qcin, lattice='conv'):
    """
    """

    # Reading and writing gulp file
    #    all_atoms_append =[]
    #     File = parse_cif_ase(qcin)
    #     for structure in File:
    #        all_atoms_append.append(structure.get_atoms())
    #         sbu =all_atoms_append[0]
    all_cifs = glob.glob(f"{qcin}/*.cif")
    for cif_file in all_cifs:
        qc_base = cif_file[:cif_file.rindex('.')]
        sbu = read(cif_file)
        bonds, mmtypes = mm.analyze_mm(sbu)
        out_file = qc_base + '.gin'
        mm.write_gin(out_file, sbu, bonds, mmtypes, lattice)
        make_directory(qc_base)
        Submit(qc_base, qc_base)
    return

def gulp_input_region(qcin, lattice='conv'):
    """
    """

    # Reading and writing gulp file
    #    all_atoms_append =[]
    #     File = parse_cif_ase(qcin)
    #     for structure in File:
    #        all_atoms_append.append(structure.get_atoms())
    #         sbu =all_atoms_append[0]
    # all_cifs = glob.glob(f"{qcin}/*.cif")
    all_cifs = find_cifs(qcin)
    for cif_file in all_cifs:
        qc_base = cif_file[:cif_file.rindex('.')]
        sbu = read(cif_file)
        bonds, mmtypes = mm.analyze_mm(sbu)
        out_file = qc_base + '.gin'
        mm.write_gin_with_region(out_file, sbu, bonds, mmtypes, lattice)
        make_directory(qc_base)
        Submit(qc_base, qc_base)
    return


def gulp_to_folder():
    '''
    Command line interface for computing docker
    '''
    parser = argparse.ArgumentParser(
        description='Run work_flow function with optional verbose output')
    parser.add_argument('cif_file', type=str,
                        help='path to cif file')

    parser.add_argument('-op', '--lattice_optimisation', type=str,
                        default='conv', help='default:conv for constant volume (meaning that lattices are constant) or conp if for lattice optimisation' )

    args = parser.parse_args()

    gulp_input2(args.cif_file, args.lattice_optimisation)


def gulp_to_file():
    '''
    Command line interface for computing docker
    '''
    parser = argparse.ArgumentParser(
        description='Run work_flow function with optional verbose output')
    parser.add_argument('cif_file', type=str,
                        help='path to cif file')

    parser.add_argument('-op', '--lattice_optimisation', type=str,
                        default='conv', help='default:conv for constant volume (meaning that lattices are constant) or conp if for lattice optimisation' )

    args = parser.parse_args()

    gulp_input(args.cif_file, args.lattice_optimisation)


def gulp_to_region():
    '''
    Command line interface for computing docker
    '''
    parser = argparse.ArgumentParser(
        description='Run work_flow function with optional verbose output')
    parser.add_argument('cif_file', type=str,
                        help='path to cif file')

    parser.add_argument('-op', '--lattice_optimisation', type=str,
                        default='conv', help='default:conv for constant volume (meaning that lattices are constant) or conp if for lattice optimisation' )

    args = parser.parse_args()

    gulp_input_region(args.cif_file, args.lattice_optimisation)
