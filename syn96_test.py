from opentrons import protocol_api
from itertools import product
import json

metadata = {'apiLevel': '2.7'}

protocol_params = {"ctab": [5,10], "haucl4": [5,10], "agno3": [5,10], "aa": [5,10], "hcl": [5,10], "seed": [5,10]}
tuberack_labels = {"A1": "ctab", "B1": "ctab", "C1": "ctab", "D1": "ctab",
                    "A2": "ctab", "B2": "ctab", "C2": "ctab", "D2": "ctab",
                    "A3": "ctab", "B3": "ctab",
                    "A4": "haucl4", "B4": "agno3", "C4": "aa", "A5": "hcl", "B5": "seed"}

wells = [i[0]+str(i[1]) for i in list(product(list('ABCDEFGH'), range(1,13)))]
param_sets = list(product(*protocol_params.values())) # for every well a combination of volumes eg. (20,3,1.6,15)

with open('smartprobes_24_tuberack_eppendorf_2ml_safelock_snapcap.json') as labware_file:
    smartprobes_tuberack = json.load(labware_file)
with open('smartprobes_96_tiprack_10ul.json') as labware_file:
    smartprobes_tiprack_10 = json.load(labware_file)
with open('smartprobes_96_wellplate_200ul_flat.json') as labware_file:
    smartprobes_wellplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    tuberack, tube_volume = protocol.load_labware_from_definition(smartprobes_tuberack, 1), 2000
    tiprack_10 = protocol.load_labware_from_definition(smartprobes_tiprack_10, 2)
    tiprack_200 = protocol.load_labware('opentrons_96_filtertiprack_200ul', 5)
    wellplate = protocol.load_labware_from_definition(smartprobes_wellplate, 3)
    p10 = protocol.load_instrument('p10_single', 'left', tip_racks=[tiprack_10]) #1-10
    p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_200]) #5-50

    for param_idx in range(len(protocol_params)):
        param = list(protocol_params.keys())[param_idx]
        if min(list(protocol_params.values())[param_idx])<=10: #select pipette
            pipette, v_max = p10, 10
        else:
            pipette, v_max = p50, 50

        param_tubes = [list(tuberack_labels.keys())[i] for i, x in enumerate(list(tuberack_labels.values())) if x == param] #list of tubes that hold param
        tube_idx = 0
        tube, v_tube = param_tubes[tube_idx], tube_volume
        pipette.pick_up_tip()
        for well_idx in range(min(96, len(param_sets))):
            v = param_sets[well_idx][param_idx] # volume of param for well
            while v>v_max:
                if v_tube<v_max: 
                    tube_idx += 1
                    tube, v_tube = param_tubes[tube_idx], tube_volume
                pipette.aspirate(v_max, tuberack[tube])
                v_tube -= v_max
                pipette.dispense(v_max, wellplate.wells()[well_idx])
                pipette.blow_out(wellplate.wells()[well_idx])
                pipette.blow_out(wellplate.wells()[well_idx])
                v -= v_max

            if v_tube<v: 
                tube_idx += 1
                tube, v_tube = param_tubes[tube_idx], tube_volume
            pipette.aspirate(v, tuberack[tube])
            v_tube -= v_max
            pipette.dispense(v, wellplate.wells()[well_idx])
            pipette.blow_out(wellplate.wells()[well_idx])
            pipette.blow_out(wellplate.wells()[well_idx])
        pipette.return_tip()

    # Mixing
    pipette, v_max = p50, 50
    pipette.pick_up_tip()
    for well_idx in range(min(96, len(param_sets))):
        pipette.mix(repetitions=2, volume=50, location=wellplate.wells()[well_idx])
        pipette.blow_out(wellplate.wells()[well_idx])
        pipette.blow_out(wellplate.wells()[well_idx])
    pipette.return_tip()
