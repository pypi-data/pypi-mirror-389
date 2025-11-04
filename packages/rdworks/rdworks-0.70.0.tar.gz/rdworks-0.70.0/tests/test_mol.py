from pathlib import Path
from rdkit import Chem

import rdworks
from rdworks import Conf, Mol, MolLibr

datadir = Path(__file__).parent.resolve() / "data"


# python >=3.12 raises SyntaxWarning: invalid escape sequence
# To address this warning in general, we can make the string literal a raw string literal r"...". 
# Raw string literals do not process escape sequences. 
# For example, r"\n" is treated simply as the characters \ and n and not as a newline escape sequence.
drug_smiles = [
    "Fc1cc(c(F)cc1F)C[C@@H](N)CC(=O)N3Cc2nnc(n2CC3)C(F)(F)F", # [0]
    r"O=C(O[C@@H]1[C@H]3C(=C/[C@H](C)C1)\C=C/[C@@H]([C@@H]3CC[C@H]2OC(=O)C[C@H](O)C2)C)C(C)(C)CC",
    "C[C@@H](C(OC(C)C)=O)N[P@](OC[C@@H]1[C@H]([C@@](F)([C@@H](O1)N2C=CC(NC2=O)=O)C)O)(OC3=CC=CC=C3)=O",
    "C1CNC[C@H]([C@@H]1C2=CC=C(C=C2)F)COC3=CC4=C(C=C3)OCO4",
    "CC1=C(C=NO1)C(=O)NC2=CC=C(C=C2)C(F)(F)F",
    "CN1[C@@H]2CCC[C@H]1CC(C2)NC(=O)C3=NN(C4=CC=CC=C43)C", # [5] - Granisetron
    "CCCN1C[C@@H](C[C@H]2[C@H]1CC3=CNC4=CC=CC2=C34)CSC",
    "CCC1=C(NC2=C1C(=O)C(CC2)CN3CCOCC3)C", # [7] Molidone
    r"C[C@H]1/C=C/C=C(\C(=O)NC2=C(C(=C3C(=C2O)C(=C(C4=C3C(=O)[C@](O4)(O/C=C/[C@@H]([C@H]([C@H]([C@@H]([C@@H]([C@@H]([C@H]1O)C)O)C)OC(=O)C)C)OC)C)C)O)O)/C=N/N5CCN(CC5)C)/C",
    r"C=CC1=C(N2[C@@H]([C@@H](C2=O)NC(=O)/C(=N\O)/C3=CSC(=N3)N)SC1)C(=O)O",
    "CC1=C(N=CN1)CSCCNC(=NC)NC#N", # [10] - Cimetidine
    """C1=C(N=C(S1)N=C(N)N)CSCC/C(=N/S(=O)(=O)N)/N""",
    "C1CC(CCC1C2=CC=C(C=C2)Cl)C3=C(C4=CC=CC=C4C(=O)C3=O)O",
    "CN(CC/C=C1C2=CC=CC=C2SC3=C/1C=C(Cl)C=C3)C",
    "CN(C)CCCN1C2=CC=CC=C2CCC3=C1C=C(C=C3)Cl",
    "CN1CCCC(C1)CC2C3=CC=CC=C3SC4=CC=CC=C24", # [15] - Methixene
    "CCN(CC)C(C)CN1C2=CC=CC=C2SC3=CC=CC=C31",
    "CC(=O)OC1=CC=CC=C1C(=O)O",
    "C1=CC(=C(C=C1F)F)C(CN2C=NC=N2)(CN3C=NC=N3)O",
    "CC(=O)NC[C@H]1CN(C(=O)O1)C2=CC(=C(C=C2)N3CCOCC3)F", # [19]
    ]

drug_names = [
    "Sitagliptin", "Simvastatin", "Sofosbuvir", "Paroxetine", "Leflunomide",
    "Granisetron", "Pergolide", "Molindone", "Rifampin", "Cefdinir",
    "Cimetidine", "Famotidine", "Atovaquone", "Chlorprothixene", "Clomipramine",
    "Methixene",  "Ethopropazine", "Aspirin", "Fluconazole", "Linezolid",
    ]


def test_init_mol():
    mol = Mol(drug_smiles[0], drug_names[0])
    assert mol.num_confs == 0
    assert mol.name == drug_names[0]
    rdmol = Chem.MolFromSmiles(drug_smiles[0])
    rdmol.SetProp('_Name', drug_names[0])
    mol = Mol(rdmol, drug_names[0])
    assert mol.rdmol.GetProp('_Name') == drug_names[0]
    assert mol.name == drug_names[0]


def test_has_substr():
    mol = Mol('c1cc(C(=O)O)c(OC(=O)C)cc1')
    assert mol.has_substr('OC(=O)C')


def test_remove_stereo():
    m = Mol("C/C=C/C=C\\C", "double_bond")
    assert m.remove_stereo().smiles == "CC=CC=CC"


def test_complete_stereoisomers():
    m = Mol("CC=CC", "double_bond")
    assert m.is_stereo_specified is False, "double bond stereo is not properly handled"
    libr = rdworks.complete_stereoisomers(m)
    assert libr.count() == 2, "cis and trans are expected"
    assert all([_.is_stereo_specified for _ in libr])
    expected_canonical_smiles = [r'C/C=C/C', r'C/C=C\C']
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0

    # 0 out of 3 atom stereocenters is specified
    m = Mol("N=C1OC(CN2CC(C)OC(C)C2)CN1", "stereoisomer")
    assert m.is_stereo_specified is False
    libr = rdworks.complete_stereoisomers(m)
    assert libr.count() == 6, "0 out of 3 atom stereocenters is specified"
    assert all([_.is_stereo_specified for _ in libr])
    expected_names = [f'stereoisomer.{i}' for i in [1,2,3,4,5,6]]
    names = [_.name for _ in libr]
    assert names == expected_names
    expected_canonical_smiles = [
        'C[C@@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@@H]1CN(C[C@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@@H]1CN(C[C@@H]2CNC(=N)O2)C[C@@H](C)O1',
        'C[C@@H]1CN(C[C@H]2CNC(=N)O2)C[C@@H](C)O1',
        'C[C@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@H]1CN(C[C@H]2CNC(=N)O2)C[C@H](C)O1',
        ]
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0
    
    # 1 out of 3 atom stereocenters is specified
    m = Mol("N=C1OC(CN1)CN2CC(O[C@H](C2)C)C", "stereoisomer") 
    assert m.is_stereo_specified is False
    libr = rdworks.complete_stereoisomers(m)
    assert libr.count() == 4, "1 out of 3 atom stereocenters is specified"
    assert all([_.is_stereo_specified for _ in libr])
    expected_names = [f'stereoisomer.{i}' for i in [1,2,3,4]]
    names = [_.name for _ in libr]
    assert names == expected_names
    expected_canonical_smiles = [
        'C[C@@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@@H]1CN(C[C@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1',
        'C[C@H]1CN(C[C@H]2CNC(=N)O2)C[C@H](C)O1',
        ]
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0

    # 2 out of 3 atom stereocenters are specified
    m = Mol("N=C1OC(CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer") 
    assert m.is_stereo_specified is False
    libr = rdworks.complete_stereoisomers(m)
    assert libr.count() == 2, "2 out of 3 atom stereocenters is specified"
    assert all([_.is_stereo_specified for _ in libr])
    expected_names = [f'stereoisomer.{i}' for i in [1,2]]
    names = [_.name for _ in libr]
    assert names == expected_names
    expected_canonical_smiles = ['C[C@@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1',
                                    'C[C@@H]1CN(C[C@H]2CNC(=N)O2)C[C@H](C)O1',
                                    ]
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0
    
    # 3 out of 3 atom stereocenters are specified
    m = Mol("N=C1O[C@@H](CN1)CN2C[C@H](O[C@H](C2)C)C", "stereoisomer") 
    assert m.is_stereo_specified is True
    libr = rdworks.complete_stereoisomers(m)
    assert libr.count() == 1, "3 out of 3 atom stereocenters is specified"
    assert all([_.is_stereo_specified for _ in libr])
    expected_names = [f'stereoisomer']
    names = [_.name for _ in libr]
    assert names == expected_names
    expected_canonical_smiles = ['C[C@@H]1CN(C[C@@H]2CNC(=N)O2)C[C@H](C)O1']
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0

    # for 20 molecules
    isomer_libr = MolLibr()
    for mol in MolLibr(drug_smiles, drug_names):
        isomer_libr += rdworks.complete_stereoisomers(mol)
    assert isomer_libr.count() >= 25


def test_num_stereoisomers():
    """count all possible stereoisomers ignoring current stereochemistry assignment"""
    m = Mol('Cc1nc2c(-c3ccc(Cl)cc3F)nc(N3CCN(C(=O)C(F)F)CC3)cn2c(=O)c1C')
    assert m.num_stereoisomers == 1
    m = Mol('CN1C=C([C@H]2CN(C3=NC(C4=CC=C(Cl)C=C4F)=C4N=C5CCCCN5C(=O)C4=C3)CCO2)C=N1')
    assert m.num_stereoisomers == 2
    m = Mol('Cc1nc2c(-c3ccc(Cl)cc3F)nc(N3CCN(S(=O)(=O)N4C[C@@H](C)O[C@@H](C)C4)CC3)cn2c(=O)c1C')
    assert m.num_stereoisomers == 3
    m = Mol('Cc1cc([C@H]2CN(c3cc4nc(C)c(C)c(=O)n4c(-c4ccc(Cl)cc4F)n3)C[C@@H](C)O2)ccn1')
    assert m.num_stereoisomers == 4


def test_complete_tautomers():
    m = Mol("Oc1c(cccc3)c3nc2ccncc12", "tautomer")
    libr = rdworks.complete_tautomers(m)
    assert libr.count() == 3
    expected_names = ['tautomer.1','tautomer.2','tautomer.3']
    names = [_.name for _ in libr]
    assert names == expected_names
    expected_canonical_smiles = [
        'O=c1c2c[nH]ccc-2nc2ccccc12',
        'O=c1c2ccccc2[nH]c2ccncc12',
        'Oc1c2ccccc2nc2ccncc12',
        ]
    canonical_smiles = [_.smiles for _ in libr]
    difference = set(expected_canonical_smiles) - set(canonical_smiles)
    assert len(difference) == 0
    
    m = Mol("CCCCNC(=O)[C@@H]1CCCN1[C@@H](CC)c1nnc(Cc2ccc(C)cc2)o1")
    libr = rdworks.complete_tautomers(m)
    assert libr.count() == 5


def test_drop_confs():
    confs = []
    for serialized in [
        "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",
        ]:
        confs.append(Conf().deserialize(serialized))
    m = Mol(confs[0])
    m.confs.extend(confs[1:])
    with open("/home/shbae/bucket/rdworks/tests/dropconfs.sdf", "w") as f:
        f.write(m.to_sdf(confs=True))

    print(m.num_confs)
    print(m.is_confs_aligned)
    m = m.align_confs().cluster_confs().drop_confs(similar=True, similar_rmsd=0.3, verbose=True)
    print(m.is_confs_aligned)
    print(m.num_confs)