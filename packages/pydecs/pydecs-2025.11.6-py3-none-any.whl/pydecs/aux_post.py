
#!/usr/bin/env python
#---------------------------------------------------------------------------
# Copyright 2025 Takafumi Ogawa
# Licensed under the Apache License, Version2.0.
#---------------------------------------------------------------------------
# Auxiliary tool of pydecs library for post-analyses
#---------------------------------------------------------------------------
import os,sys
import argparse
from pathlib import Path
import shutil
import numpy as np

def parse_POSCAR(path):
    with open(path) as f:
        L = [l.strip() for l in f if l.strip()]
    scale = float(L[1].split()[0])
    lattice = np.array([[float(x) for x in L[i].split()] for i in (2,3,4)]) * scale
    elems  = L[5].split()
    natoms = [int(x) for x in L[6].split()]
    natoms_tot = sum(natoms)
    natoms_dict = {}
    for i in range(len(elems)):
        natoms_dict[elems[i]] = natoms[i]
    elems_list = []
    for i in range(len(elems)):
        for j in range(natoms[i]):
            elems_list.append(elems[i])

    print(f"-"*60)
    print(f"  Parsing {path}")
    print(f"  Lattice constants:")
    for i in range(3):
        print(f"    {lattice[i]}")
    print(f"  Elements: {elems}")
    print(f"  Number of atoms: {natoms}")
    coords = []
    for i in range(8, natoms_tot+8):
        coords.append([float(x) for x in L[i].split()[:3]])
    coords = np.array(coords)

    return lattice, natoms_dict, elems_list, coords

def identify_defects():
    parser = argparse.ArgumentParser(
        prog='pydecs-post-identify-defects',
        description='Convert CIF file to VASP POSCAR/CONTCAR'
    )
    parser.add_argument(
        'input_POSCAR_bulk',
        type=Path,
        help='Path to perfect POSCAR'
    )
    parser.add_argument(
        'input_POSCAR_defect',
        type=Path,
        help='Path to POSCAR including defects'
    )
    
    args = parser.parse_args()
    input_POSCAR_bulk = args.input_POSCAR_bulk
    input_POSCAR_defect = args.input_POSCAR_defect
    print(f"-"*60)
    print(f"  Starting pydecs-post-identify-defects")
    print(f"  Input POSCAR bulk: {input_POSCAR_bulk}")
    print(f"  Input POSCAR defect: {input_POSCAR_defect}")

    lattice_bulk, natoms_bulk, elems_bulk, coords_bulk = parse_POSCAR(input_POSCAR_bulk)
    lattice_defect, natoms_defect, elems_defect, coords_defect = parse_POSCAR(input_POSCAR_defect)

    print("-"*60)
    diff1 = np.linalg.norm(lattice_defect - lattice_bulk)
    print(f"  Difference of lattice constants: {diff1}")
    if diff1 > 1e-5:
        print("  ERROR:: Lattice constants are different, which should be the same.")
        sys.exit(1)
    else:
        print("  Lattice constants are the same (tolerance is 1e-5).")

    print("-"*60)
    print("  Calculating nearest neighbors")
    cutoff_max = 5.0
    num_nearest = 10
    neighbor_list = []
    nnlist_fromBulk = [[] for _ in range(len(elems_bulk))]
    fn1 = "postpydecs_neighbors_all.csv"
    if os.path.exists(fn1):
        backup_fn = fn1 + "_backup"
        if os.path.exists(backup_fn):
            os.remove(backup_fn)
        shutil.move(fn1, backup_fn)
        print(f"  Moved existing {fn1} to {backup_fn}")
    fout1 = open(fn1, "w")
    fout1.write("id_defect,elem_defect,id_nearest,elem_nearest,dist_nearest\n")
    for id_def, (elem_def, coord_def) in enumerate(zip(elems_defect, coords_defect)):
        diff_list_tmp = []
        for id_bulk, (elem_bulk, coord_bulk) in enumerate(zip(elems_bulk, coords_bulk)):
            dv1 = coord_def - coord_bulk
            for i1 in range(3):
                if dv1[i1] > 0.5:
                    dv1[i1] -= 1.0
                elif dv1[i1] < -0.5:
                    dv1[i1] += 1.0
            dv1c = dv1 @ lattice_bulk
            dist1 = np.linalg.norm(dv1c)
            if dist1 < cutoff_max:
                diff_list_tmp.append((id_bulk, elem_bulk, dist1))
        diff_list_tmp_sorted = sorted(diff_list_tmp, key=lambda x: x[2])
        # print(diff_list_tmp_sorted[:num_nearest])
        neighbor_list.append(diff_list_tmp_sorted[:num_nearest])
        for j1 in range(num_nearest):
            fout1.write(f"{id_def+1:04d},{elem_def},")
            fout1.write(f"{j1+1},")
            fout1.write(f"{diff_list_tmp_sorted[j1][0]+1:04d},{diff_list_tmp_sorted[j1][1]},{diff_list_tmp_sorted[j1][2]:.6f}")
            fout1.write("\n")
        nn1 = diff_list_tmp_sorted[0]
        nnlist_fromBulk[nn1[0]].append(id_def)
    fout1.close()

    fn1 = "postpydecs_neighbors_eachAtomInDefectCell.csv"
    if os.path.exists(fn1):
        backup_fn = fn1 + "_backup"
        if os.path.exists(backup_fn):
            os.remove(backup_fn)
        shutil.move(fn1, backup_fn)
        print(f"  Moved existing {fn1} to {backup_fn}")
    fout1 = open(fn1, "w")
    fout1.write("id_nearest,elem_nearest,id_defect,elem_defect,dist_nearest,determined_by\n")
    defective_data = []
    for id_nnb1,nnb1 in enumerate(nnlist_fromBulk):
        elem_bulk = elems_bulk[id_nnb1]
        if len(nnb1)==1:
            id_def = nnb1[0]
            nn1 = neighbor_list[id_def][0]
            elem_def = elems_defect[id_def]
            fout1.write(f"{nn1[0]+1:04d},{nn1[1]},")
            fout1.write(f"{id_def+1:04d},{elem_def},")
            fout1.write(f"{nn1[2]:.6f},determined in 1st-match")
            fout1.write("\n")
            if elem_bulk.split("[")[0]=="Rn":
                defective_data.append(("interstitial",)+nn1+(id_def,elem_def))
            elif elem_bulk.split("[")[0]!=elem_def:
                defective_data.append(("substitutional",)+nn1+(id_def,elem_def))
        elif len(nnb1)==0 and elem_bulk.split("[")[0]!="Rn":
            defective_data.append(("vacancy",id_nnb1+1,elem_bulk, "None"))
            fout1.write(f"{id_nnb1+1:04d},{elem_bulk},vacancy")
            fout1.write("\n")
        elif len(nnb1)>1:
            distlist = []
            for id_def1 in nnb1:
                nl1 = neighbor_list[id_def1][0]
                distlist.append(nl1[2])
            argmin = np.argmin(distlist)
            id_def0 = nnb1[argmin]
            nn1 = neighbor_list[id_def0][0]
            elem_def = elems_defect[id_def0]
            fout1.write(f"{nn1[0]+1:04d},{nn1[1]},")
            fout1.write(f"{id_def0+1:04d},{elem_def},")
            fout1.write(f"{nn1[2]:.6f},determined in 1st-match")
            fout1.write("\n")
            if elem_bulk.split("[")[0]=="Rn":
                defective_data.append(("interstitial",)+nn1+(id_def0,elem_def))
            elif elem_bulk.split("[")[0]!=elem_def:
                defective_data.append(("substitutional",)+nn1+(id_def0,elem_def))            
            nnb1.remove(id_def0)
            for id_def1 in nnb1:
                for irank in range(1,num_nearest):
                    nl1 = neighbor_list[id_def1][irank]
                    id_bulk2 = nl1[0]
                    elem_bulk2 = elems_bulk[id_bulk2]
                    nnb2 = nnlist_fromBulk[id_bulk2]
                    if len(nnb2)>0:
                        continue
                    else:
                        nn1 = nl1
                        elem_def = elems_defect[id_def1]
                        fout1.write(f"{nn1[0]+1:04d},{nn1[1]},")
                        fout1.write(f"{id_def1+1:04d},{elem_def},")
                        fout1.write(f"{nn1[2]:.6f}, determined in {irank+1}-th-match")
                        fout1.write("\n")
                        print(nnb1, nn1,elem_bulk2,elem_def)
                        if elem_bulk2.split("[")[0]=="Rn":
                            defective_data.append(("interstitial",)+nn1+(id_def1,elem_def))
                        elif elem_bulk2.split("[")[0]!=elem_def:
                            defective_data.append(("substitutional",)+nn1+(id_def1,elem_def))
                        break
    fout1.close()

    print("-"*60)
    print("  Detected defects:")
    fn1 = "postpydecs_detected_defects.txt"
    if os.path.exists(fn1):
        backup_fn = fn1 + "_backup"
        if os.path.exists(backup_fn):
            os.remove(backup_fn)
        shutil.move(fn1, backup_fn)
        print(f"  Moved existing {fn1} to {backup_fn}")
    fout1 = open(fn1, "w")
    fout1.write("defect_type,id_bulk,elem_bulk,bulk_coord,id_def,elem_def,defect_coord,distance\n")
    def_symbol_all = ""
    for d1 in defective_data:
        def_type = d1[0]
        id_bulk = d1[1]
        elem_bulk = d1[2]
        elem_bulk = elem_bulk.replace("Rn","int")
        cb1 = coords_bulk[id_bulk]
        def_symbol = ""
        if def_type=="vacancy":
            def_symbol = "Vac_"
        else: 
            elem_def = d1[5]
            def_symbol = f"{elem_def}_"
        def_symbol += f"{elem_bulk}"
        print(f"  [{def_type}] {def_symbol}")
        print(f"     Bulk-id: {id_bulk}({elem_bulk})")
        print(f"     Bulk-coord: {cb1}")
        fout1.write(f"{def_type},{id_bulk},{elem_bulk},{cb1}")
        if def_type!="vacancy":
            id_def = d1[4]
            elem_def = d1[5]
            cd1 = coords_defect[id_def]
            print(f"     Defect-id: {id_def}({elem_def})")
            print(f"     Defect-coord: {cd1}")
            print(f"     Distance: {d1[3]:.6f}")
            fout1.write(f",{id_def},{elem_def},{cd1},{d1[3]:.6f}")
        fout1.write("\n")
        def_symbol_all += def_symbol+"+"
    def_symbol_all = def_symbol_all[:-1]
    fout1.write(def_symbol_all+"\n")
    if len(def_symbol_all)==0:
        print(f"  Total defect symbol: None")
    else:
        print(f"  Total defect symbol: {def_symbol_all}")
    fout1.close()
    print("-"*60)


if __name__ == "__main__":
    identify_defects()
