import json
import opentrons.simulate
import opentrons.execute
import socket

host = socket.gethostname()
port = 8080
opentrons_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
opentrons_socket.bind((host, port))

data, _ = opentrons_socket.recvfrom(1024)
data = data.decode('utf-8').split(',') #data is a string "material,units,simulate,episode,close"
simulate = data[2]=="True"

if simulate:
    protocol = opentrons.simulate.get_protocol_api('2.7')
else:
    protocol = opentrons.execute.get_protocol_api('2.7')

with open('src/hardware/smartprobes_24_tuberack_eppendorf_2ml_safelock_snapcap.json') as labware_file:
    smartprobes_tuberack = json.load(labware_file)
tuberack = protocol.load_labware_from_definition(smartprobes_tuberack, 1)

with open('src/materials/tuberack.json') as materials_file:
    tuberack_materials = json.load(materials_file)

def find_tube_with_enough_volume(material, volume):
    tube_idx = 0
    tube_label = list(tuberack_materials)[tube_idx] #eg 'B3'
    while (tuberack_materials[tube_label][0]!=material) | (volume>tuberack_materials[tube_label][1]):
        tube_idx += 1
        tube_label = list(tuberack_materials)[tube_idx]
    return tube_label

def update_tuberack_volumes(tuberack_materials, tube_label, volume):
    tuberack_materials[tube_label] = [tuberack_materials[tube_label][0], tuberack_materials[tube_label][1] - volume]
    return tuberack_materials

with open('src/hardware/smartprobes_96_tiprack_10ul.json') as labware_file:
    smartprobes_tiprack_10 = json.load(labware_file)
tiprack_10 = protocol.load_labware_from_definition(smartprobes_tiprack_10, 2)

with open('src/hardware/smartprobes_96_tiprack_200ul.json') as labware_file:
    smartprobes_tiprack_200 = json.load(labware_file)
tiprack_200 = protocol.load_labware_from_definition(smartprobes_tiprack_200, 5)

p10 = protocol.load_instrument('p10_single', 'left', tip_racks=[tiprack_10]) #1-10
p10.well_bottom_clearance.dispense = 0
p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_200]) #5-50
p50.well_bottom_clearance.aspirate = 0

with open('src/hardware/smartprobes_96_wellplate_200ul_flat.json') as labware_file:
    smartprobes_wellplate = json.load(labware_file)
wellplate = protocol.load_labware_from_definition(smartprobes_wellplate, 3)

protocol.home()
while data[4]=='False': #intil close==True
    material = data[0]
    volume = float(data[1])
    well = wellplate.wells()[int(data[3])]
   
    if volume <= 10: 
        pipette, pipette_max_volume = p10, 10
    else:
        pipette, pipette_max_volume = p50, 50

    tube_label = find_tube_with_enough_volume(material, volume)
    tube, tube_volume = tube_label, tuberack_materials[tube_label][1]

    pipette.pick_up_tip()

    remaining_volume_to_pipette = volume
    while remaining_volume_to_pipette>0:
        v = min(pipette_max_volume, remaining_volume_to_pipette)
        tuberack_materials = update_tuberack_volumes(tuberack_materials, tube_label, volume)
        remaining_volume_to_pipette -= v
        pipette.aspirate(v, tuberack[tube].bottom())
        pipette.dispense(v, well, rate=2.0)
        pipette.blow_out(well)
        pipette.touch_tip(well, v_offset=-9, radius=1.3)
        pipette.blow_out(well)
        volume -= pipette_max_volume

    pipette.return_tip()

    data, _ = opentrons_socket.recvfrom(1024) #get next action from server
    data = data.decode('utf-8').split(',')

protocol.home()
opentrons_socket.close()

print("\n".join(protocol._commands))
