from opentrons import protocol_api
from itertools import product
import sys

metadata = {'apiLevel': '2.7'}

# get protocal parameter values
#protocol_params = {}
#for param in ["ctab", "haucl4", "agno3", "aa", "hcl", "seed"]:
#    assert param in sys.argv, "Please define " + param
#    protocol_params[param] = [float(i) for i in sys.argv[sys.argv.index(param) + 1].split(",")]
protocol_params = {"ctab": [200], "haucl4": [2], "agno3": [2,3,4,5], "aa": [1.6], "hcl": [1,3,5,19,15,20], "seed": [0.2,0.5,1.5]}
protocol_params = {"ctab": [2], "haucl4": [2], "agno3": [2,3], "aa": [1.6], "hcl": [1,3], "seed": [0.2,0.5]}


wells = [i[0]+str(i[1]) for i in list(product(list('ABCDEFGH'), range(1,13)))]

def run(protocol: protocol_api.ProtocolContext):
    tuberack = protocol.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', 4)
    wellplate = protocol.load_labware('nest_96_wellplate_200ul_flat', 1)
    tiprack_10 = protocol.load_labware('opentrons_96_tiprack_10ul', 2)
    tiprack_300 = protocol.load_labware('opentrons_96_tiprack_300ul', 3)
    p10 = protocol.load_instrument('p10_single', 'left', tip_racks=[tiprack_10]) #1-10
    p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_300]) #5-50

    param_sets = list(product(*protocol_params.values())) # for every well a combination of volumes eg. (20,3,1.6,15)
    
    for param_idx in range(len(protocol_params)):
        if min(list(protocol_params.values())[param_idx])<5: #select pipette
            pipette = p10
            v_max = 10
        else:
            pipette = p50
            v_max = 50

        pipette.pick_up_tip()
        for well_idx in range(min(96, len(param_sets))):
            v = param_sets[well_idx][param_idx]
            _v = v
            while _v>v_max:
                pipette.aspirate(v_max, tuberack['A1'])
                pipette.dispense(v_max, wellplate.wells()[well_idx])
            pipette.aspirate(_v, tuberack['A1'])
            pipette.dispense(_v, wellplate.wells()[well_idx])
        pipette.return_tip()
