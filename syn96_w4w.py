from opentrons import protocol_api
from itertools import product
import json

metadata = {'apiLevel': '2.7'}

protocol_params = {"ctab": [10,20], "haucl4": [10], "agno3": [10], "aa": [10], "hcl": [10], "seed": [10]}
tuberack_labels = { "A1": "ctab", "A2": "ctab" "", "A3": "haucl4",  "A4": "seed",   "A5": "", "A6": "",
                    "B1": "ctab", "B2": "ctab" "", "B3": "agno3",   "B4": "",       "B5": "", "B6": "",
                    "C1": "ctab", "C2": "ctab" "", "C3": "aa",      "C4": "",       "C5": "", "C6": "",
                    "D1": "ctab", "D2": "ctab" "", "D3": "hcl",     "D4": "",       "D5": "", "D6": ""}

param_sets = list(product(*protocol_params.values())) # for every well a combination of volumes eg. (20,3,1.6,15)

with open('src/hardware/smartprobes_24_tuberack_eppendorf_2ml_safelock_snapcap.json') as labware_file:
    smartprobes_tuberack = json.load(labware_file)
with open('src/hardware/smartprobes_96_tiprack_10ul.json') as labware_file:
    smartprobes_tiprack_10 = json.load(labware_file)
with open('src/hardware/smartprobes_96_wellplate_200ul_flat.json') as labware_file:
    smartprobes_wellplate = json.load(labware_file)

def run(protocol: protocol_api.ProtocolContext):
    tuberack, tube_volume = protocol.load_labware_from_definition(smartprobes_tuberack, 1), 2000
    tiprack_10 = protocol.load_labware_from_definition(smartprobes_tiprack_10, 2)
    tiprack_200 = protocol.load_labware('opentrons_96_filtertiprack_200ul', 5)
    wellplate = protocol.load_labware_from_definition(smartprobes_wellplate, 3)
    p10 = protocol.load_instrument('p10_single', 'left', tip_racks=[tiprack_10]) #1-10
    p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_200]) #5-50

    p10.well_bottom_clearance.dispense = 0
    p50.well_bottom_clearance.aspirate = 0

    for well_idx in range(min(96, len(param_sets))):
        for param_idx, param in enumerate(protocol_params):

            if min(list(protocol_params.values())[param_idx])<=10: #select pipette
                pipette, v_max = p10, 10
            else:
                pipette, v_max = p50, 50

            param_tubes = [list(tuberack_labels.keys())[i] for i, x in enumerate(list(tuberack_labels.values())) if x == param] #list of tubes that hold param
            tube_idx = 0
            tube, v_tube = param_tubes[tube_idx], tube_volume
            pipette.pick_up_tip()
            v = param_sets[well_idx][param_idx] # volume of param for well
            while v>v_max:
                if v_tube<v_max: 
                    tube_idx += 1
                    tube, v_tube = param_tubes[tube_idx], tube_volume
                pipette.aspirate(v_max, tuberack[tube])
                v_tube -= v_max
                pipette.dispense(v_max, wellplate.wells()[well_idx], rate=2.0)
                pipette.blow_out(wellplate.wells()[well_idx])
                pipette.touch_tip(wellplate.wells()[well_idx], v_offset=-10, radius=1.3)
                pipette.blow_out(wellplate.wells()[well_idx])
                v -= v_max
            if v_tube<v: 
                tube_idx += 1
                tube, v_tube = param_tubes[tube_idx], tube_volume
            pipette.aspirate(v, tuberack[tube])
            v_tube -= v_max
            pipette.dispense(v, wellplate.wells()[well_idx], rate=2.0)
            pipette.blow_out(wellplate.wells()[well_idx])
            pipette.touch_tip(wellplate.wells()[well_idx], v_offset=-10, radius=1.3)
            pipette.blow_out(wellplate.wells()[well_idx])
            pipette.return_tip()

    # Mixing
    pipette, v_max = p50, 50
    pipette.pick_up_tip()
    for well_idx in range(min(96, len(param_sets))):
        pipette.mix(repetitions=2, volume=50, location=wellplate.wells()[well_idx])
        pipette.blow_out(wellplate.wells()[well_idx])
        pipette.touch_tip(wellplate.wells()[well_idx], v_offset=-10, radius=1.3)
        pipette.blow_out(wellplate.wells()[well_idx])
    pipette.return_tip()
